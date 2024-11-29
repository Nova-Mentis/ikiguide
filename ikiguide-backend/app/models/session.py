import uuid
from app.models.logger import logger
import threading
from datetime import datetime, timedelta
from typing import Dict, Optional

class SessionError(Exception):
    """Custom exception for session-related errors."""
    pass

class SessionManager:
    def __init__(self, max_sessions: int = 1000, session_timeout: int = 24):
        """
        Initialize session manager with configurable max sessions and timeout.
        
        :param max_sessions: Maximum number of concurrent sessions
        :param session_timeout: Session timeout in hours
        """
        self._sessions: Dict[str, Dict] = {}
        self._max_sessions = max_sessions
        self._session_timeout = session_timeout
        self._session_creation_lock = threading.Lock()
        logger.info(f"SessionManager initialized: max_sessions={max_sessions}, timeout={session_timeout} hours")

    def create_session(self, initial_data: Optional[Dict] = None) -> str:
        """
        Create a new session with optional initial user data.
        
        :param initial_data: Optional initial data to store in the session
        :return: Session ID
        :raises SessionError: If session creation fails
        """
        with self._session_creation_lock:
            try:
                # Cleanup expired and old sessions BEFORE creating a new one
                self._cleanup_expired_sessions()

                # Check if we've reached max sessions
                if len(self._sessions) >= self._max_sessions:
                    # Remove oldest session
                    oldest_session = min(self._sessions, key=lambda k: self._sessions[k]['created_at'])
                    del self._sessions[oldest_session]
                    logger.warning(f"Max sessions reached. Removed oldest session: {oldest_session}")

                # Generate unique session ID
                session_id = str(uuid.uuid4())
                
                # Prepare session data
                session_data = {
                    'created_at': datetime.now(),
                    'user_data': initial_data or {},
                    'last_activity': datetime.now(),
                    'user_responses': {}  # Consistent with previous implementation
                }
                
                # Store session data
                self._sessions[session_id] = session_data
                
                logger.info(f"Created new session: {session_id}")
                return session_id
            
            except Exception as e:
                logger.error(f"Failed to create session: {str(e)}")
                raise SessionError(f"Session creation failed: {str(e)}")

    def get_session(self, session_id: str) -> Optional['Session']:
        """
        Retrieve session data if it exists and is not expired.
        
        :param session_id: Session ID to retrieve
        :return: Session object or None
        """
        try:
            logger.info(f"Attempting to retrieve session: {session_id}")
            logger.info(f"Current sessions: {list(self._sessions.keys())}")
            
            session_data = self._sessions.get(session_id)
            
            if session_data:
                # Update last activity timestamp
                session_data['last_activity'] = datetime.now()
                logger.info(f"Session found: {session_id}")
                return Session(session_id, session_data)
            
            logger.warning(f"Attempted to access non-existent session: {session_id}")
            return None
        
        except Exception as e:
            logger.error(f"Error retrieving session {session_id}: {str(e)}")
            return None

    def update_session(self, session_id: str, data: Dict) -> bool:
        """
        Update session data.
        
        :param session_id: Session ID to update
        :param data: Dictionary of data to update
        :return: True if update successful, False otherwise
        """
        try:
            session = self.get_session(session_id)
            if session:
                # Update the session's internal dictionary
                session._session_data['user_data'].update(data)
                session._session_data['last_activity'] = datetime.now()
                logger.info(f"Updated session: {session_id}")
                return True
            
            logger.warning(f"Cannot update non-existent session: {session_id}")
            return False
        
        except Exception as e:
            logger.error(f"Error updating session {session_id}: {str(e)}")
            return False

    def delete_session(self, session_id: str) -> bool:
        """
        Delete a specific session.
        
        :param session_id: Session ID to delete
        :return: True if session was deleted, False otherwise
        """
        try:
            if session_id in self._sessions:
                del self._sessions[session_id]
                logger.info(f"Deleted session: {session_id}")
                return True
            
            logger.warning(f"Attempted to delete non-existent session: {session_id}")
            return False
        
        except Exception as e:
            logger.error(f"Error deleting session {session_id}: {str(e)}")
            return False

    def _cleanup_expired_sessions(self):
        """
        Remove sessions that have exceeded the timeout.
        Maintains multiple sessions within the max_sessions limit.
        """
        now = datetime.now()
        
        # Remove expired sessions first
        expired_sessions = [
            sid for sid, session in list(self._sessions.items())
            if (now - session['created_at']) > timedelta(hours=self._session_timeout)
        ]
        
        for sid in expired_sessions:
            del self._sessions[sid]
            logger.info(f"Cleaned up expired session: {sid}")
        
        # If we've exceeded max sessions, remove oldest sessions
        if len(self._sessions) > self._max_sessions:
            # Sort sessions by creation time, oldest first
            sorted_sessions = sorted(
                self._sessions.items(), 
                key=lambda x: x[1]['created_at']
            )
            
            # Remove oldest sessions until we're within the limit
            while len(self._sessions) > self._max_sessions:
                oldest_sid, _ = sorted_sessions.pop(0)
                del self._sessions[oldest_sid]
                logger.info(f"Removed oldest session to maintain max sessions: {oldest_sid}")

class Session:
    def __init__(self, session_id: str, session_data: Dict):
        """
        Initialize a Session object.
        
        :param session_id: Session identifier
        :param session_data: Dictionary containing session data
        """
        self._session_id = session_id
        self._session_data = session_data
        self._session_manager = session_manager  # Global session manager

    def __len__(self):
        """
        Return the number of items in the session data.
        
        :return: Number of items in session data
        """
        return len(self._session_data)

    def __contains__(self, key):
        """
        Allow 'in' operator for checking key existence in session data.
        
        :param key: Key to check
        :return: True if key exists, False otherwise
        """
        return key in self._session_data

    def __getitem__(self, key):
        """
        Allow dictionary-like access to session data for backwards compatibility.
        
        :param key: Key to retrieve from session data
        :return: Value associated with the key
        """
        return self._session_data[key]

    def set_user_responses(self, responses: Dict):
        """
        Set user responses for the session.
        
        :param responses: Dictionary of user responses
        """
        try:
            self._session_data['user_responses'] = responses
            self._session_data['last_activity'] = datetime.now()
            logger.info(f"Set user responses for session {self._session_id}")
        except Exception as e:
            logger.error(f"Error setting user responses for session {self._session_id}: {str(e)}")

    def get_user_responses(self) -> Dict:
        """
        Retrieve user responses for the session.
        
        :return: Dictionary of user responses
        """
        return self._session_data.get('user_responses', {})

    @property
    def session_id(self) -> str:
        """
        Get the session identifier.
        
        :return: Session ID
        """
        return self._session_id

# Global session manager instance
session_manager = SessionManager()
