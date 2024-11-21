from fastapi import APIRouter, HTTPException, Request, Response, Depends
from fastapi.responses import JSONResponse
from typing import Dict, Any, Optional
import logging
import traceback

from app.config import settings
from app.models.session import session_manager, SessionError
from app.services.openai_service import generate_ikiguide

logger = logging.getLogger(__name__)

router = APIRouter()

class APIError(Exception):
    """
    Custom API exception for standardized error responses.
    """
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code

async def api_error_handler(request: Request, exc: APIError):
    """
    Global exception handler for API errors.
    
    :param request: Incoming request
    :param exc: API exception
    :return: JSON response with error details
    """
    logger.error(f"API Error: {exc.message}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.message,
            "details": traceback.format_exc() if settings.APP_DEBUG else None
        }
    )

def set_session_cookie(response, session_id: str):
    """
    Set session cookie with secure and httponly flags.
    
    :param response: FastAPI response object
    :param session_id: Session ID to set in cookie
    """
    response.set_cookie(
        key="session_id", 
        value=session_id, 
        httponly=True, 
        secure=settings.APP_ENV != "development",
        samesite="lax",
        max_age=settings.SESSION_MAX_AGE  # Use max_age from settings
    )

def get_session_id(request: Request) -> str:
    """
    Retrieve or create a session ID.
    
    :param request: Incoming request
    :return: Session ID
    """
    # Log all incoming request details for debugging
    logger.info(f"Request method: {request.method}")
    logger.info(f"Request URL: {request.url}")
    logger.info(f"Request headers: {dict(request.headers)}")
    
    # Extract session ID from cookies
    session_id = request.cookies.get("session_id")
    logger.info(f"Existing session_id from cookies: {session_id}")
    
    # Validate session
    if session_id:
        existing_session = session_manager.get_session(session_id)
        if existing_session:
            logger.info(f"Using existing valid session: {session_id}")
            return session_id
        else:
            logger.warning(f"Invalid session found: {session_id}")
    
    # Create new session if no valid session exists
    try:
        session_id = session_manager.create_session()
        logger.info(f"Created new session: {session_id}")
        return session_id
    except SessionError as e:
        logger.error(f"Session creation failed: {e}")
        raise APIError("Unable to create session", status_code=500)

@router.post("/start_session")
async def start_session(request: Request):
    """
    Explicitly start a new session.
    
    :param request: Incoming request
    :return: Session details
    """
    try:
        logger.info(f"Start session request received. Headers: {dict(request.headers)}")
        
        # Check for existing session
        existing_session_id = request.cookies.get("session_id")
        logger.info(f"Existing session ID from cookies: {existing_session_id}")
        
        if existing_session_id and session_manager.get_session(existing_session_id):
            logger.info(f"Returning existing valid session: {existing_session_id}")
            return JSONResponse(content={"session_id": existing_session_id})
        
        # Create new session if no valid session exists
        session_id = session_manager.create_session()
        logger.info(f"Created new session: {session_id}")
        
        response = JSONResponse(content={"session_id": session_id})
        set_session_cookie(response, session_id)
        return response
    
    except SessionError as e:
        logger.error(f"Session start failed: {e}", exc_info=True)
        raise APIError("Session initialization failed", status_code=500)

@router.get("/session_info")
async def get_session_info(request: Request):
    """
    Retrieve current session information.
    
    :param request: Incoming request
    :return: Session details
    """
    session_id = get_session_id(request)
    session = session_manager.get_session(session_id)
    
    if not session:
        raise APIError("Session not found", status_code=404)
    
    return {
        "session_id": session_id,
        "created_at": session._session_data['created_at'].isoformat(),
        "last_activity": session._session_data['last_activity'].isoformat(),
        "data": session._session_data['user_data']
    }

@router.post("/update_session")
async def update_session(request: Request, data: Dict[str, Any]):
    """
    Update session with provided data.
    
    :param request: Incoming request
    :param data: Data to update in session
    :return: Update status
    """
    session_id = get_session_id(request)
    
    try:
        updated = session_manager.update_session(session_id, data)
        if not updated:
            raise APIError("Session update failed", status_code=400)
        
        return {"success": True, "message": "Session updated successfully"}
    
    except Exception as e:
        logger.error(f"Session update error: {e}")
        raise APIError("Unable to update session", status_code=500)

@router.delete("/end_session")
async def end_session(request: Request):
    """
    Terminate the current session.
    
    :param request: Incoming request
    :return: Session termination status
    """
    session_id = get_session_id(request)
    
    try:
        deleted = session_manager.delete_session(session_id)
        if not deleted:
            raise APIError("Session termination failed", status_code=400)
        
        response = JSONResponse(content={"success": True, "message": "Session terminated"})
        response.delete_cookie("session_id")
        return response
    
    except Exception as e:
        logger.error(f"Session termination error: {e}")
        raise APIError("Unable to terminate session", status_code=500)

@router.get("/health")
async def health_check():
    """
    Simple health check endpoint.
    
    :return: Status of the API
    """
    return {"status": "healthy"}

@router.post("/responses")
async def save_response(request: Request, response_data: Dict[str, Any]):
    """
    Save user responses to the current session.
    
    :param request: Incoming request
    :param response_data: Responses to save
    :return: Confirmation of saved responses
    """
    try:
        # Use the session ID from the request body if provided
        session_id = response_data.get('session_id') or get_session_id(request)
        
        # Retrieve or create session
        session = session_manager.get_session(session_id)
        if not session:
            session_id = session_manager.create_session()
            session = session_manager.get_session(session_id)
        
        # Get current user data
        user_data = session._session_data['user_data']
        
        # Initialize responses if not exists
        if 'responses' not in user_data:
            user_data['responses'] = {}
        
        # Update specific response for the given question
        user_data['responses'][response_data['question_id']] = response_data['response']
        
        # Update session with modified responses
        updated = session_manager.update_session(session_id, {
            'responses': user_data['responses']
        })
        
        if not updated:
            raise APIError("Failed to save responses", status_code=400)
        
        logger.info(f"Saved response for question {response_data['question_id']}")
        logger.info(f"Current responses: {user_data['responses']}")
        
        # Create response with session cookie
        response = JSONResponse(content={
            "success": True, 
            "message": "Responses saved successfully",
            "session_id": session_id
        })
        
        # Set session cookie
        set_session_cookie(response, session_id)
        
        return response
    
    except Exception as e:
        logger.error(f"Error saving responses: {e}", exc_info=True)
        raise APIError("Unable to save responses", status_code=500)

@router.get("/responses")
async def get_responses(request: Request):
    """
    Retrieve saved responses for the current session.
    
    :param request: Incoming request
    :return: Saved responses
    """
    try:
        session_id = get_session_id(request)
        session = session_manager.get_session(session_id)
        
        if not session:
            raise APIError("No session found", status_code=404)
        
        # Get user data from the session
        user_data = session._session_data['user_data']
        
        if 'responses' not in user_data:
            raise APIError("No responses found", status_code=404)
        
        return {
            "success": True,
            "responses": user_data['responses']
        }
    
    except Exception as e:
        logger.error(f"Error retrieving responses: {e}")
        raise APIError("Unable to retrieve responses", status_code=500)

@router.get("/results")
async def get_results(request: Request, session_id: Optional[str] = None):
    """
    Retrieve Ikigai results for the current session.
    
    :param request: Incoming request
    :param session_id: Optional session ID to retrieve results for
    :return: Ikigai results
    """
    try:
        # Log all incoming request details for debugging
        logger.info(f"Results request received. Method: {request.method}")
        logger.info(f"Request URL: {request.url}")
        logger.info(f"Request headers: {dict(request.headers)}")
        logger.info(f"Request cookies: {request.cookies}")

        # Use provided session_id or retrieve from request
        if not session_id:
            session_id = get_session_id(request)
        
        logger.info(f"Retrieving results for session: {session_id}")
        
        # Validate session
        session = session_manager.get_session(session_id)
        if not session:
            logger.warning(f"Invalid session for results: {session_id}")
            raise APIError("Invalid session", status_code=404)
        
        # Retrieve responses from session
        user_responses = session._session_data['user_data'].get('responses', {})
        logger.info(f"User responses found: {user_responses}")
        
        # Check if we have at least some responses
        if len(user_responses) < 1:
            logger.warning(f"No responses found: {len(user_responses)}")
            raise APIError("No user responses found", status_code=404)
        
        # Map numeric keys to expected keys if necessary
        key_mapping = {
            1: 'good_at', 
            2: 'love', 
            3: 'world_needs', 
            4: 'paid_for'
        }
        
        # Prepare responses for Ikigai path generation
        ikiguide_responses = {}
        for key, value in user_responses.items():
            # If key is numeric, map it to the corresponding string key
            if isinstance(key, int) and key in key_mapping:
                ikiguide_responses[key_mapping[key]] = value
            # If key is already a string, use it directly
            elif isinstance(key, str):
                ikiguide_responses[key] = value
        
        # Validate required keys
        required_keys = ['good_at', 'love', 'world_needs', 'paid_for']
        if not all(key in ikiguide_responses for key in required_keys):
            logger.warning(f"Missing required response keys. Found: {list(ikiguide_responses.keys())}")
            raise APIError("Incomplete user responses", status_code=400)
        
        # Generate Ikigai paths
        from app.services.openai_service import generate_ikiguide
        
        try:
            ikiguide_result = generate_ikiguide(
                responses=ikiguide_responses, 
                session_id=session_id
            )
            
            logger.info(f"Successfully retrieved Ikigai paths for session {session_id}")
            return ikiguide_result
        
        except Exception as generate_error:
            logger.error(f"Error generating Ikigai paths: {generate_error}", exc_info=True)
            raise APIError("Failed to generate Ikigai paths", status_code=500)
    
    except APIError:
        # Re-raise APIErrors to be handled by FastAPI
        raise
    
    except Exception as e:
        logger.error(f"Unexpected error retrieving results: {e}", exc_info=True)
        raise APIError("Unable to retrieve results", status_code=500)

@router.post("/reset_session")
async def reset_session(session_data: dict, request: Request):
    """
    Endpoint to reset a specific session.
    
    Clears all session-related data and generates a new session ID.
    
    :param session_data: Dictionary containing session information
    :param request: Incoming request
    :return: Session reset confirmation
    """
    try:
        # Extract session ID from the request or session data
        session_id = session_data.get('session_id') or await get_session_id(request)
        
        if not session_id:
            raise APIError("No session ID provided", status_code=400)
        
        # Log the session reset attempt
        logger.info(f"Resetting session: {session_id}")
        
        # Terminate the existing session
        await end_session(request)
        
        # Start a new session
        new_session = await start_session(request)
        
        return {
            "status": "success",
            "message": "Session reset successfully",
            "new_session_id": new_session.get('session_id')
        }
    
    except Exception as e:
        logger.error(f"Error resetting session: {e}", exc_info=True)
        raise APIError("Unable to reset session", status_code=500)
