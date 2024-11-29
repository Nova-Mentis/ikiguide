import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import axios from 'axios';

const questions = [
  "What are you good at?",
  "What do you love doing?", 
  "What does the world need?",
  "What can you get paid for?"
];

const questionGuidance = {
  "What are you good at?": [
    "Think about skills you've developed over time",
    "Consider compliments you've received from others",
    "Reflect on tasks that come naturally to you",
    "List areas where you consistently perform well",
    "Identify skills you've learned through work, hobbies, or education"
  ],
  "What do you love doing?": [
    "Recall activities that make you lose track of time",
    "Think about what energizes and excites you",
    "Consider hobbies or tasks you'd do even without payment",
    "Reflect on moments of pure joy and engagement",
    "List activities that feel meaningful and fulfilling"
  ],
  "What does the world need?": [
    "Consider global or local challenges that move you",
    "Think about problems you wish could be solved",
    "Reflect on causes or issues you're passionate about",
    "Consider how your skills could help others",
    "Identify areas where you see opportunities for positive change"
  ],
  "What can you get paid for?": [
    "List your professional skills and qualifications",
    "Consider current job market trends",
    "Reflect on potential career paths",
    "Think about services or products you could offer",
    "Explore ways to monetize your talents and passions"
  ]
};

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
    // Simplified session check
    const validateSession = async () => {
      try {
        if (!currentSessionId) {
          // If no session ID, redirect to home
          navigate('/');
          return;
        }

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
        <div className="bg-ikigai-light/20 p-4 rounded-lg mb-6">
          <h3 className="text-xl font-semibold mb-3 text-ikigai-main">Guidance Prompts:</h3>
          <ul className="list-disc pl-6 text-gray-700 space-y-2">
            {questionGuidance[question].map((guidance, index) => (
              <li key={index} className="text-base">{guidance}</li>
            ))}
          </ul>
        </div>
        <input
          type="text"
          className="w-full p-3 mb-6 border-2 border-ikigai-grey/50 rounded-lg focus:outline-none focus:border-ikigai-main transition duration-300"
          placeholder="Your answer here..."
          value={response}
          onChange={(e) => setResponse(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleSubmit()}
        />
        {error && (
          <p className="text-red-500 text-sm mb-4 text-center">{error}</p>
        )}
        <div className="flex justify-between">
          {questionIndex > 0 && (
            <Link 
              to={`/question/${questionIndex}/${currentSessionId}`} 
              className="px-4 py-2 bg-ikigai-grey/20 text-ikigai-main rounded hover:bg-ikigai-grey/30 transition"
            >
              Previous
            </Link>
          )}
          <button 
            onClick={handleSubmit}
            className="px-6 py-2 bg-ikigai-main text-white rounded hover:bg-ikigai-main/90 transition ml-auto"
          >
            {questionIndex < 3 ? 'Next' : 'Finish'}
          </button>
        </div>
      </div>
    </div>
  );
}

export default QuestionPage;
