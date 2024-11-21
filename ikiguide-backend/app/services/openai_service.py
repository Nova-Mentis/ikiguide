from openai import OpenAI
import os
from dotenv import load_dotenv
import logging
from app.logging_config import logger  # Import the centralized logger
from app.models.session import session_manager

# Load environment variables
load_dotenv()

# Initialize OpenAI client
try:
    print("Attempting to initialize OpenAI client...")
    print(f"API Key present: {bool(os.getenv('OPENAI_API_KEY'))}")
    print(f"API Key (first 5 chars): {os.getenv('OPENAI_API_KEY')[:5] if os.getenv('OPENAI_API_KEY') else 'N/A'}")
    
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    
    print("OpenAI client initialized successfully!")
    # Perform a quick test to validate the client
    try:
        test_response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": "Hello, can you confirm the client is working?"}]
        )
        print("Client test successful!")
    except Exception as test_error:
        print(f"Client test failed: {test_error}")
except Exception as e:
    print(f"Error initializing OpenAI client: {e}")
    client = None

# Prompt template
PROMPT_TEMPLATE = """
INSTRUCTIONS

Using the below USER RESPONSES to the Ikigai elements, identify and generate five unique career directions for the user.

USER RESPONSES

    - Skills: {good_at}
    - Passions: {passions}
    - World Needs: {world_needs}
    - Income Potential: {paid_for}

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

def generate_ikiguide(responses, session_id=None):
    """
    Generate Ikigai paths based on user responses with session support.
    
    :param responses: Dictionary of user responses
    :param session_id: Optional session identifier
    :return: List of paths including a summary
    """
    logger.info("Attempting to generate Ikigai paths")
    logger.info(f"Received responses type: {type(responses)}")
    logger.info(f"Received responses: {responses}")
    logger.info(f"Received responses keys: {list(responses.keys())}")

    # Validate responses
    required_keys = ['good_at', 'love', 'world_needs', 'paid_for']
    if not all(key in responses for key in required_keys):
        logger.error("Missing required response keys")
        raise ValueError("Missing required response keys")

    # Determine session management
    if not session_id:
        session_id = session_manager.create_session()
    
    session = session_manager.get_session(session_id)
    if not session:
        session_id = session_manager.create_session()
        session = session_manager.get_session(session_id)
    
    # Log session details
    logger.info(f"Session ID: {session_id}")

    # Check if paths are already generated for this session
    existing_paths = session._session_data['user_data'].get('ikiguide_paths')
    if existing_paths:
        logger.info(f"Returning existing paths for session {session_id}")
        return {
            'session_id': session_id,
            'paths': existing_paths,
            'user_responses': responses
        }

    # Set user responses in the session
    session.set_user_responses(responses)

    # Generate paths using OpenAI
    if client:
        try:
            logger.info("Attempting to generate paths with OpenAI")
            
            # Format the prompt template with user responses
            formatted_prompt = PROMPT_TEMPLATE.format(
                good_at=responses['good_at'],
                passions=responses['love'],
                world_needs=responses['world_needs'],
                paid_for=responses['paid_for']
            )
            
            logger.info(f"Prompt length: {len(formatted_prompt)} characters")
            
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a career path advisor specializing in Ikigai."},
                    {"role": "user", "content": formatted_prompt}
                ],
                temperature=0.2
            )
            
            # Log full response details
            logger.info("OpenAI Response Received")
            logger.info(f"Response object type: {type(response)}")
            logger.info(f"Number of choices: {len(response.choices)}")
            
            # Extract and process paths
            paths_text = response.choices[0].message.content.strip()
            logger.info(f"Generated paths text length: {len(paths_text)} characters")
            logger.info(f"Generated paths text (first 500 chars): {paths_text[:500]}...")
            
            # Split paths and validate
            paths = [path.strip() for path in paths_text.split('\n') if path.strip()]
            
            # Store paths in session to prevent regeneration
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
    else:
        logger.error("OpenAI client not initialized")
        return {
            'session_id': session_id,
            'paths': ["ERROR: OpenAI client not initialized"],
            'user_responses': responses
        }