import React from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios'; // Import axios
import ikigaiDiagram from '../assets/ikigai-diagram.png';  

const IntroductionPage = () => {
  const navigate = useNavigate();

  const handleBeginJourney = () => {
    console.log('Begin journey button clicked');
    
    // Clear any existing session data and stored responses
    const sessionKeys = Object.keys(localStorage).filter(key => 
      key.startsWith('ikiguide_session_id') || 
      key.includes('_response_') || 
      key.includes('session_id')
    );
    sessionKeys.forEach(key => localStorage.removeItem(key));
    document.cookie = 'session_id=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/; SameSite=Lax';
    
    // Call backend to start a new session
    axios.post('http://localhost:8000/api/start_session', {}, {
      withCredentials: true,
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      }
    })
    .then(response => {
      console.log('Session start response:', response.data);
      const newSessionId = response.data.session_id;
      
      // Store the new session ID in both localStorage and a cookie
      localStorage.setItem('ikiguide_session_id', newSessionId);
      document.cookie = `session_id=${newSessionId}; path=/; SameSite=Lax`;
      
      // Navigate to first question with new session ID
      navigate(`/question/1/${newSessionId}`);
    })
    .catch(error => {
      console.error('Failed to start session:', error.response ? error.response.data : error.message);
      console.error('Full error object:', error);
      
      // Fallback to local session generation if backend fails
      const fallbackSessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      localStorage.setItem('ikiguide_session_id', fallbackSessionId);
      document.cookie = `session_id=${fallbackSessionId}; path=/; SameSite=Lax`;
      navigate(`/question/1/${fallbackSessionId}`);
    });
  };

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-ikigai-grey/10 p-8">
      <div className="max-w-4xl w-full bg-white shadow-lg rounded-lg p-8 flex flex-col md:flex-row items-center border-2 border-ikigai-black/20">
        <div className="md:w-1/2 mb-6 md:mb-0 md:mr-8">
          <img 
            src={ikigaiDiagram} 
            alt="Ikigai Diagram" 
            className="w-full h-auto object-contain"
          />
        </div>
        <div className="md:w-1/2">
          <h1 className="text-4xl font-bold mb-4 text-ikigai-main">Welcome to IKIGUIDE</h1>
          <p className="text-lg mb-4 text-ikigai-main">
            Discover your purpose and potential through the transformative Japanese concept of Ikigai.
          </p>
          <p className="mb-4 text-ikigai-black">
            Ikigai is about finding the intersection of:
          </p>
          <ul className="list-disc list-inside mb-6 text-ikigai-black">
            <li>What you are good at</li>
            <li>What you love doing</li>
            <li>What the world needs</li>
            <li>What you can be paid for</li>
          </ul>
          <button 
            onClick={handleBeginJourney}
            className="bg-ikigai-main hover:bg-ikigai-main/90 text-white font-bold py-3 px-6 rounded-full transition duration-300 ease-in-out transform hover:scale-105 text-lg"
          >
            Begin Your Ikigai Journey
          </button>
        </div>
      </div>
    </div>
  );
};

export default IntroductionPage;
