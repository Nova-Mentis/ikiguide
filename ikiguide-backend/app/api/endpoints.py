from fastapi import APIRouter, HTTPException, Request, Response, Depends
from fastapi.responses import JSONResponse
from typing import Dict, Any, Optional
from app.models.logger import logger
import traceback
import json
import msal
import requests
from app.config import settings
from app.models.session import session_manager, SessionError
from app.services.openai_service import generate_ikiguide
import os

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
        
        # Check if a session already exists and is valid
        existing_session_id = request.cookies.get("session_id")
        logger.info(f"Existing session ID from cookies: {existing_session_id}")
        
        if existing_session_id:
            existing_session = session_manager.get_session(existing_session_id)
            if existing_session:
                logger.info(f"Existing valid session found: {existing_session_id}")
                return JSONResponse(content={"session_id": existing_session_id})
        
        # If no valid session exists, create a new one
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
    
    Supports two response formats:
    1. Single response: {'question_id': int, 'response': str}
    2. Multiple responses: {'responses': {question_id: response}}
    
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
        
        # Handle multiple response formats
        if 'question_id' in response_data and 'response' in response_data:
            # Single response format
            user_data['responses'][response_data['question_id']] = response_data['response']
        elif 'responses' in response_data and isinstance(response_data['responses'], dict):
            # Multiple responses format
            user_data['responses'].update(response_data['responses'])
        else:
            # If neither format is recognized, raise an error
            raise APIError("Invalid response format", status_code=400)
        
        # Update session with modified responses
        updated = session_manager.update_session(session_id, {
            'responses': user_data['responses']
        })
        
        if not updated:
            raise APIError("Failed to save responses", status_code=400)
        
        logger.info(f"Saved responses: {user_data['responses']}")
        
        # Create response with session cookie
        response = JSONResponse(content={
            "success": True, 
            "message": "Responses saved successfully",
            "session_id": session_id,
            "saved_responses": list(user_data['responses'].keys())
        })
        
        # Set session cookie
        set_session_cookie(response, session_id)
        
        return response
    
    except Exception as e:
        logger.error(f"Error saving responses: {e}", exc_info=True)
        raise APIError(f"Unable to save responses: {str(e)}", status_code=500)

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
        # If no session ID provided, get current session
        if not session_id:
            session_id = get_session_id(request)
        
        # Retrieve session data using the proper method
        session = session_manager.get_session(session_id)
        
        if not session:
            raise APIError("No results found for this session", status_code=404)
        
        # Access user responses from the session object
        user_responses = session._session_data['user_data'].get('responses', {})
        
        # Log the retrieved responses for debugging
        logger.info(f"Retrieved user responses: {user_responses}")
        
        # Validate required keys
        required_keys = ['good_at', 'love', 'world_needs', 'paid_for']
        
        # If responses are numeric keys, try to map them to required keys
        if all(isinstance(key, int) for key in user_responses.keys()):
            if len(user_responses) == len(required_keys):
                mapped_responses = dict(zip(required_keys, user_responses.values()))
                logger.info(f"Mapped numeric responses to required keys: {mapped_responses}")
                user_responses = mapped_responses
            else:
                logger.warning(f"Numeric responses do not match required keys. Found: {list(user_responses.keys())}")
                raise APIError("Incomplete user responses", status_code=400)
        
        # Validate mapped or original responses
        if not all(key in user_responses for key in required_keys):
            logger.warning(f"Missing required response keys. Found: {list(user_responses.keys())}")
            raise APIError("Incomplete user responses", status_code=400)
        
        # Additional validation to ensure responses are not just 'testing'
        if all(response.lower() == 'testing' for response in user_responses.values()):
            logger.warning("All responses are 'testing'. Please provide meaningful responses.")
            raise APIError("Responses must be more specific than 'testing'", status_code=400)
        
        # Generate Ikigai paths
        from app.services.openai_service import generate_ikiguide
        
        try:
            # Generate Ikigai paths
            ikiguide_result = await generate_ikiguide(
                responses=user_responses, 
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

@router.post("/email_results")
async def email_results(request: Request, email_data: Dict[str, str]):
    """
    Email Ikigai results to the user using Azure AD authentication.
    
    :param request: Incoming request
    :param email_data: Dictionary containing email and optional message
    :return: Email sending status
    """

    # TODO Fix this
    
    try:
        # Get session ID (synchronous call)
        session_id = get_session_id(request)
        
        # Retrieve results for the current session (await the result)
        results = await get_results(request, session_id)
        
        # Validate email
        if not email_data.get('email'):
            raise APIError("Email address is required", status_code=400)
        
        # Azure AD configuration - log configuration details securely
        tenant_id = settings.AZURE_TENANT_ID
        client_id = settings.AZURE_CLIENT_ID
        client_secret = settings.AZURE_CLIENT_SECRET
        sender_email = settings.EMAIL_FROM
        
        # Validate Azure configuration
        if not all([tenant_id, client_id, client_secret, sender_email]):
            logger.error("Incomplete Azure AD configuration")
            raise APIError("Azure AD configuration is incomplete", status_code=500)
        
        logger.info(f"Attempting to send email. Sender: {sender_email}, Recipient: {email_data['email']}")
        
        # Authenticate and get access token
        authority = f"https://login.microsoftonline.com/{tenant_id}"
        try:
            app = msal.ConfidentialClientApplication(
                client_id,
                authority=authority,
                client_credential=client_secret
            )
        except Exception as app_init_error:
            logger.error(f"Failed to initialize MSAL application: {str(app_init_error)}")
            raise APIError("Failed to initialize authentication", status_code=500)
        
        # Acquire token
        scopes = ["https://graph.microsoft.com/.default"]
        
        try:
            # First try silent token acquisition
            result = app.acquire_token_silent(scopes, account=None)
            
            # If silent acquisition fails, acquire token directly
            if not result:
                result = app.acquire_token_for_client(scopes=scopes)
            
            # Validate token acquisition
            if "access_token" not in result:
                error_description = result.get('error_description', 'Unknown token acquisition error')
                logger.error(f"Token acquisition failed: {error_description}")
                raise APIError(f"Failed to acquire token: {error_description}", status_code=500)
            
            logger.info("Token acquired successfully")
        
        except Exception as token_error:
            logger.error(f"Token acquisition exception: {str(token_error)}", exc_info=True)
            raise APIError(f"Token acquisition failed: {str(token_error)}", status_code=500)
        
        # Prepare email payload
        email_payload = {
            "message": {
                "subject": "Your Ikiguide Results",
                "body": {
                    "contentType": "HTML",
                    "content": f"""
                    <html>
                    <body>
                    <h2>Your Ikiguide Results</h2>
                    <pre>{json.dumps(results, indent=2)}</pre>
                    {f'<p><strong>Additional Message:</strong> {email_data.get("message", "")}</p>' if email_data.get("message") else ''}
                    </body>
                    </html>
                    """
                },
                "toRecipients": [
                    {
                        "emailAddress": {
                            "address": email_data['email']
                        }
                    }
                ]
            },
            "saveToSentItems": "false"  # Explicitly set to avoid permission issues
        }
        
        logger.info(f"Email payload prepared for {email_data['email']}")
        
        # Send email via Microsoft Graph API
        send_mail_url = f"https://graph.microsoft.com/v1.0/users/{sender_email}/sendMail"
        headers = {
            'Authorization': f'Bearer {result["access_token"]}',
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.post(send_mail_url, headers=headers, json=email_payload, timeout=10)
            
            # Enhanced logging for response
            logger.info(f"Email send response status: {response.status_code}")
            logger.info(f"Email send response content: {response.text}")
            
            # Check response
            if response.status_code not in [200, 201, 202]:
                logger.error(f"Email sending failed. Status: {response.status_code}, Content: {response.text}")
                raise APIError(f"Failed to send email: {response.text}", status_code=500)
            
            return {
                "status": "success", 
                "message": "Results emailed successfully",
                "recipient": email_data['email']
            }
        
        except requests.RequestException as req_error:
            logger.error(f"Request error sending email: {str(req_error)}", exc_info=True)
            raise APIError(f"Email sending request failed: {str(req_error)}", status_code=500)
    
    except Exception as e:
        logger.error(f"Comprehensive error emailing results: {str(e)}", exc_info=True)
        raise APIError(f"Failed to email results: {str(e)}", status_code=500)

@router.post("/reset_session")
async def reset_session(session_data: dict, request: Request):
    """
    Endpoint to reset a specific session.
    
    Clears all session-related data without creating a new session.
    
    :param session_data: Dictionary containing session information
    :param request: Incoming request
    :return: Session reset confirmation
    """
    try:
        # Extract session ID from the request or session data
        session_id = session_data.get('session_id') or get_session_id(request)
        
        if not session_id:
            raise APIError("No session ID provided", status_code=400)
        
        # Log the session reset attempt
        logger.info(f"Resetting session: {session_id}")
        
        # Terminate the existing session
        await end_session(request)
        
        return {
            "status": "success",
            "message": "Session reset successfully",
            "new_session_id": None  # Explicitly do not create a new session
        }
    
    except Exception as e:
        logger.error(f"Error resetting session: {e}", exc_info=True)
        raise APIError("Unable to reset session", status_code=500)