import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import axios from 'axios';

const questions = [
  "What are you good at?",
  "What do you love?", 
  "What does the world need?",
  "What can you get paid for?"
];

const QuestionPage = () => {
  const { id, sessionId } = useParams();
  const navigate = useNavigate();
  const questionIndex = parseInt(id) - 1;
  const question = questions[questionIndex];
  const [response, setResponse] = useState("");
  const [error, setError] = useState(null);

  // Function to get session ID from cookie
  const getSessionIdFromCookie = () => {
    const cookies = document.cookie.split('; ');
    const sessionCookie = cookies.find(row => row.startsWith('session_id='));
    return sessionCookie ? sessionCookie.split('=')[1] : null;
  };

  // Use sessionId from URL, fallback to cookie, then localStorage
  const [currentSessionId, setCurrentSessionId] = useState(
    sessionId || getSessionIdFromCookie() || localStorage.getItem('ikiguide_session_id')
  );

  useEffect(() => {
    // Validate sessionId with backend
    const validateSession = async () => {
      try {
        if (!currentSessionId) {
          // If no session ID, redirect to home
          navigate('/');
          return;
        }

        // Validate session with backend
        await axios.get('http://localhost:8000/api/session_info', {
          withCredentials: true,
          params: { session_id: currentSessionId }
        });

        // Retrieve stored response for this question from localStorage
        const storedResponse = localStorage.getItem(`${currentSessionId}_response_${questionIndex + 1}`);
        setResponse(storedResponse || "");

        // Reset error when question changes
        setError(null);
      } catch (error) {
        console.error('Session validation failed:', error);
        // If session validation fails, redirect to home
        navigate('/');
      }
    };

    validateSession();
  }, [questionIndex, currentSessionId, navigate]);

  const handleSubmit = async () => {
    if (!response.trim()) {
      setError("Please provide a response");
      return;
    }

    // Ensure we have a session ID
    if (!currentSessionId) {
      setError("Session error. Please refresh the page.");
      return;
    }

    try {
      // Send response with session ID
      const responsePost = await axios.post('http://localhost:8000/api/responses', {
        session_id: currentSessionId,
        question_id: questionIndex + 1, 
        response: response.trim()
      }, {
        withCredentials: true,
        headers: {
          'Content-Type': 'application/json'
        }
      });
      
      // Store response in localStorage
      localStorage.setItem(`${currentSessionId}_response_${questionIndex + 1}`, response.trim());
      
      // Explicitly set session ID in localStorage and cookies
      localStorage.setItem('ikiguide_session_id', currentSessionId);
      document.cookie = `session_id=${currentSessionId}; path=/; SameSite=Lax`;

      // Navigate to next question or results
      if (questionIndex < 3) {
        navigate(`/question/${questionIndex + 2}/${currentSessionId}`);
      } else {
        navigate(`/results/${currentSessionId}`);
      }
    } catch (error) {
      console.error('Error submitting response:', error);
      
      // More detailed error handling
      const errorMessage = error.response 
        ? error.response.data.detail || 'Failed to submit response. Please try again.'
        : 'Network error. Please check your connection.';
      
      setError(errorMessage);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleSubmit();
    }
  };

  return (
    <div className="min-h-screen bg-white flex items-center justify-center p-8">
      <div className="content-section w-full max-w-xl">
        <h2 className="text-3xl font-bold mb-6 text-ikigai-main text-center">
          {question}
        </h2>
        <input
          type="text"
          className="w-full p-3 mb-6 border-2 border-ikigai-grey/50 rounded-lg focus:outline-none focus:border-ikigai-main transition duration-300"
          placeholder="Your answer here..."
          value={response}
          onChange={(e) => setResponse(e.target.value)}
          onKeyPress={handleKeyPress}
        />
        {error && (
          <p className="text-red-500 mb-4 text-center">{error}</p>
        )}
        <div className="flex justify-between">
          {questionIndex > 0 && (
            <Link 
              to={`/question/${questionIndex}/${currentSessionId}`} 
              className="bg-ikigai-grey/20 text-ikigai-black px-4 py-2 rounded-lg hover:bg-ikigai-grey/30 transition"
            >
              Previous
            </Link>
          )}
          <button 
            onClick={handleSubmit}
            className="bg-ikigai-main text-white px-6 py-2 rounded-lg hover:bg-ikigai-main/90 transition ml-auto"
          >
            {questionIndex < 3 ? 'Next' : 'Generate Ikigai'}
          </button>
        </div>
      </div>
    </div>
  );
}

export default QuestionPage;
