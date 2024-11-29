from openai import OpenAI
import os
from dotenv import load_dotenv
import logging
from app.models.logger import logger
from app.models.session import session_manager
from app.config import settings
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential
import concurrent.futures

# Load environment variables
load_dotenv()

# Initialize OpenAI client
try:
    logger.info("Attempting to initialize OpenAI client...")
    
    # Use configuration to get API key

    
    # Log the environment variable status
    logger.info(f"OpenAI API Key in environment: {'OPENAI_API_KEY' in os.environ}")
    logger.info(f"OpenAI API Key length: {len(os.environ.get('OPENAI_API_KEY', ''))}")
    
    # Validate API key
    if not settings.OPENAI_API_KEY:
        logger.error("OpenAI API key is not set. Please encrypt and set the key.")
    else:
        
        # Initialize client
        os.environ['OPENAI_API_KEY'] = settings.OPENAI_API_KEY
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        
        logger.info("OpenAI client initialized successfully!")
        # Perform a quick test to validate the client
        try:
            test_response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": "Hello, can you confirm the client is working?"}]
            )
            logger.info("Client test successful!")
        except Exception as test_error:
            logger.error(f"Client test failed: {test_error}")

except Exception as e:
    logger.error(f"Error initializing OpenAI client: {e}")
    logger.error(f"Exception type: {type(e).__name__}")


# Prompt template
PROMPT_TEMPLATE = """
INSTRUCTIONS

Using the below USER RESPONSES to the Ikigai elements, identify and generate five unique career directions for the user.

USER RESPONSES

    - What are you good at: {good_at}
    - What do you love: {love}
    - What does the world need: {world_needs}
    - What can you get paid for: {paid_for}

GUIDANCE

 For each path:

    - Generate a title that aligns with the USER RESPONSES. 
        - Provide a title that avoids frivolity and quotes.
        - All CAPS.
        - Do not repeat USER RESPONSES
        - Do no include quotes
        - Do not include the word "Career"
        - Do not include "[]" brackets
        - Do not include the word "Title" or "Path"
    - Generate a two-sentence description that highlights:
        - How this path leverages the user's unique skills and aligns with the USER RESPONSES.
        - The deeper purpose and passion that fuels it.
        - Tangible ways it fulfills societal needs.
        - Innovative methods for sustainable income generation.

SUMMARY

After listing the career directions, include a reflective summary that:

    - Aligns with the USER RESPONSES to the Ikigai elements.
    - Explains how the paths provide personal fulfillment, societal impact, and sustainable career opportunities.
    - Summarizes how they holistically address societal needs and income potential.

EXAMPLE OUTPUT

[PATH NAME 1]
[Description]

[New Line]

[PATH NAME 2]
[Description]

[New Line]

[PATH NAME 3]
[Description]

[New Line]

[PATH NAME 4]
[Description]

[New Line]

[PATH NAME 5]
[Description]

[New Line]

SUMMARY
[Summary]

"""

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
async def generate_ikiguide_with_retry(responses, session_id=None):
    """
    Generate Ikigai paths with retry mechanism and better error handling.
    
    :param responses: Dictionary of user responses
    :param session_id: Optional session identifier
    :return: Dictionary with paths and session information
    """
    logger.info("Attempting to generate Ikigai paths with retry mechanism")
    
    # Validate responses
    required_keys = ['good_at', 'love', 'world_needs', 'paid_for']
    
    # Transform responses if they are using numeric keys
    if all(isinstance(k, int) for k in responses.keys()):
        logger.info("Transforming numeric response keys to expected keys")
        responses = {
            'good_at': responses.get(1, ''),
            'love': responses.get(2, ''),
            'world_needs': responses.get(3, ''),
            'paid_for': responses.get(4, '')
        }
    
    if not all(key in responses for key in required_keys):
        logger.error(f"Missing required response keys. Current keys: {list(responses.keys())}")
        raise ValueError("Missing required response keys")
    
    # Determine or create session
    if not session_id:
        session_id = session_manager.create_session()
    
    session = session_manager.get_session(session_id)
    if not session:
        session_id = session_manager.create_session()
        session = session_manager.get_session(session_id)
    
    # Check for existing paths
    existing_paths = session._session_data['user_data'].get('ikiguide_paths')
    if existing_paths:
        logger.info(f"Returning existing paths for session {session_id}")
        return {
            'session_id': session_id,
            'paths': existing_paths,
            'user_responses': responses
        }
    
    # Ensure OpenAI client is initialized
    if not client:
        logger.error("OpenAI client not initialized")
        return {
            'session_id': session_id,
            'paths': ["ERROR: OpenAI client not initialized"],
            'user_responses': responses
        }
    
    try:
        # Format prompt
        formatted_prompt = PROMPT_TEMPLATE.format(
            good_at=responses['good_at'],
            love=responses['love'],
            world_needs=responses['world_needs'],
            paid_for=responses['paid_for']
        )
        
        # Use a thread pool executor for running blocking I/O
        with concurrent.futures.ThreadPoolExecutor() as pool:
            # Run the OpenAI API call in a separate thread
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                pool, 
                lambda: client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "You are a career path advisor specializing in Ikigai."},
                        {"role": "user", "content": formatted_prompt}
                    ],
                    temperature=0.2
                )
            )
        
        # Process response
        paths_text = response.choices[0].message.content.strip()
        paths = [path.strip() for path in paths_text.split('\n') if path.strip()]
        
        # Store paths in session
        session_manager.update_session(session_id, {'ikiguide_paths': paths})
        
        return {
            'session_id': session_id,
            'paths': paths,
            'user_responses': responses
        }
    
    except Exception as e:
        logger.error(f"Error generating Ikigai paths: {str(e)}")
        return {
            'session_id': session_id,
            'paths': [f"ERROR: {str(e)}"],
            'user_responses': responses
        }

# Update the original function to use the new async version
async def generate_ikiguide(responses, session_id=None):
    """
    Synchronous wrapper for async Ikigai path generation.
    
    :param responses: Dictionary of user responses
    :param session_id: Optional session identifier
    :return: Dictionary with paths and session information
    """
    # Use the async function directly instead of asyncio.run()
    # This allows FastAPI to handle the async call
    async def _async_generate():
        return await generate_ikiguide_with_retry(responses, session_id)
    
    # Return the coroutine to be awaited by FastAPI
    return await _async_generate()