import React, { useState, useEffect, useRef } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import axios from 'axios';

// Separate component for loading state
const LoadingScreen = () => {
  const [progress, setProgress] = useState(0);
  const [message, setMessage] = useState('');

  useEffect(() => {
    const wittyMessages = [
      'Unearthing your hidden potential...',
      'Connecting the dots of your life\'s purpose...',
      'Brewing your personalized Ikigai recipe...',
      'Decoding the secrets of your passion...',
      'Aligning stars for your life\'s mission...',
      'Crafting your unique life compass...'
    ];

    // Initial message
    setMessage(wittyMessages[Math.floor(Math.random() * wittyMessages.length)]);

    // Progress animation
    const progressIntervals = [10, 30, 50, 70, 90, 99, 100];
    let currentIndex = 0;

    const progressTimer = setInterval(() => {
      if (currentIndex < progressIntervals.length) {
        setProgress(progressIntervals[currentIndex]);
        
        // Change message occasionally
        if (currentIndex % 2 === 0) {
          setMessage(wittyMessages[Math.floor(Math.random() * wittyMessages.length)]);
        }

        currentIndex++;
      } else {
        clearInterval(progressTimer);
      }
    }, 1500); // Change progress every 1.5 seconds

    return () => clearInterval(progressTimer);
  }, []);

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-white">
      <div className="w-full max-w-md px-4">
        <div className="mb-4 text-center text-ikigai-main text-lg font-semibold">
          {message}
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2.5">
          <div 
            className="bg-ikigai-main h-2.5 rounded-full transition-all duration-500 ease-in-out" 
            style={{ width: `${progress}%` }}
          ></div>
        </div>
      </div>
    </div>
  );
};

const ResultsPage = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [paths, setPaths] = useState([]);
  const [showEmailModal, setShowEmailModal] = useState(false);
  const [emailAddress, setEmailAddress] = useState('');
  const [emailStatus, setEmailStatus] = useState(null);
  const [emailSendAttempts, setEmailSendAttempts] = useState(0);
  const [userResponses, setUserResponses] = useState({
    'What You\'re Good At': '',
    'What You Love': '',
    'What the World Needs': '',
    'What You Can Get Paid For': ''
  });

  const startOver = async () => {
    try {
      // Clear all local storage items related to the current session
      const currentSessionId = localStorage.getItem('ikiguide_session_id');
      
      // Remove all session-related items
      if (currentSessionId) {
        // Remove all response-related items for this session
        localStorage.removeItem(`${currentSessionId}_response_1`);
        localStorage.removeItem(`${currentSessionId}_response_2`);
        localStorage.removeItem(`${currentSessionId}_response_3`);
        localStorage.removeItem(`${currentSessionId}_response_4`);
      }
      
      // Remove the current session ID
      localStorage.removeItem('ikiguide_session_id');

      // Optional: Call backend to invalidate the current session
      try {
        await axios.post('http://localhost:8000/api/reset_session', 
          { session_id: currentSessionId }, 
          { withCredentials: true }
        );
      } catch (error) {
        console.error('Error resetting session on backend:', error);
      }

      // Hard reload to ensure complete reset
      window.location.href = '/';
    } catch (error) {
      console.error('Error in startOver:', error);
      // Fallback navigation
      window.location.href = '/';
    }
  };

  const isValidEmail = (email) => {
    // Comprehensive email validation
    if (!email) {
      console.error(' Email Validation: Email is empty or undefined');
      return false;
    }

    const trimmedEmail = String(email).trim();
    const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
    const isValid = emailRegex.test(trimmedEmail);

    console.log(' Email Validation Details:', {
      originalEmail: email,
      trimmedEmail,
      isValid,
      attempts: emailSendAttempts
    });

    return isValid;
  };

  const emailResults = async (forceEmail) => {
    console.log('emailResults called with:', {
      emailAddress,
      forceEmail,
      attempts: emailSendAttempts
    });

    // Increment send attempts
    setEmailSendAttempts(prev => prev + 1);

    try {
      // Use forced email if provided, otherwise use state
      const emailToSend = forceEmail || emailAddress;

      // Validate email
      if (!isValidEmail(emailToSend)) {
        console.error(' Invalid email:', emailToSend);
        setEmailStatus('Please enter a valid email address');
        return false;
      }

      // Get session ID
      const sessionId = localStorage.getItem('ikiguide_session_id');
      if (!sessionId) {
        setEmailStatus('No session found. Please restart the process.');
        return false;
      }

      // Send email request
      const response = await axios.post(
        'http://localhost:8000/api/email_results', 
        {
          email: emailToSend.trim(),
        },
        {
          withCredentials: true,
          headers: {
            'Content-Type': 'application/json'
          }
        }
      );

      // Handle successful email
      setEmailStatus('Results sent successfully!');
      
      // Close modal after a short delay
      setTimeout(() => {
        setShowEmailModal(false);
        setEmailStatus(null);
      }, 2000);

      return true;

    } catch (error) {
      console.error(' Email sending error:', error);
      setEmailStatus(
        error.response?.data?.message || 
        'Failed to send email. Please try again.'
      );
      return false;
    }
  };

  const EmailModal = () => {
    const [localEmailAddress, setLocalEmailAddress] = useState('');

    useEffect(() => {
      // Initialize local state when modal opens
      setLocalEmailAddress(emailAddress);
    }, [showEmailModal, emailAddress]);

    const handleSendEmail = async () => {
      console.log(' Handle Send Email - Initial State:', {
        localEmailAddress,
        currentEmailAddress: emailAddress,
        attempts: emailSendAttempts
      });

      // Validate local email
      if (!localEmailAddress) {
        setEmailStatus('Please enter a valid email address');
        return;
      }

      // Update parent state
      setEmailAddress(localEmailAddress);

      // Attempt to send email immediately with forced email
      const sendResult = await emailResults(localEmailAddress);
      
      console.log(' Send Result:', sendResult);
    };

    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white p-6 rounded-lg shadow-xl w-96">
          <h2 className="text-xl font-bold mb-4 text-ikigai-main">
            Email Your Ikiguide Results
          </h2>
          
          <input 
            type="email" 
            placeholder="Your Email Address" 
            value={localEmailAddress}
            onChange={(e) => setLocalEmailAddress(e.target.value)}
            className="w-full p-2 border rounded mb-4"
            required
          />
          
          {emailStatus && (
            <div className={`mb-4 p-2 rounded ${
              emailStatus.includes('successfully') 
                ? 'bg-green-100 text-green-800' 
                : 'bg-red-100 text-red-800'
            }`}>
              {emailStatus}
            </div>
          )}
          
          <div className="flex justify-between">
            <button 
              onClick={() => setShowEmailModal(false)}
              className="bg-gray-200 text-gray-800 px-4 py-2 rounded hover:bg-gray-300"
            >
              Cancel
            </button>
            <button 
              onClick={handleSendEmail}
              className="bg-[var(--color-secondary)] text-white px-4 py-2 rounded hover:opacity-80"
              disabled={emailStatus?.includes('successfully')}
            >
              Send Email
            </button>
          </div>
        </div>
      </div>
    );
  };

  useEffect(() => {
    let isMounted = true;

    const fetchResults = async () => {
      try {
        // Use consistent session ID key
        const sessionId = localStorage.getItem('ikiguide_session_id');
        
        if (!sessionId) {
          throw new Error('No session ID found');
        }

        // Check if we have all the required responses stored
        const requiredResponses = [
          localStorage.getItem(`${sessionId}_response_1`),
          localStorage.getItem(`${sessionId}_response_2`),
          localStorage.getItem(`${sessionId}_response_3`),
          localStorage.getItem(`${sessionId}_response_4`)
        ];

        // If any response is missing, redirect to home
        if (requiredResponses.some(response => !response)) {
          console.warn('Incomplete session responses');
          localStorage.removeItem('ikiguide_session_id');
          requiredResponses.forEach((_, index) => {
            localStorage.removeItem(`${sessionId}_response_${index + 1}`);
          });
          navigate('/');
          return;
        }

        // First, validate the session
        try {
          const sessionValidation = await axios.get('http://localhost:8000/api/session_info', {
            withCredentials: true,
            params: { session_id: sessionId }
          });
          console.log('Session Validation Response:', sessionValidation.data);
        } catch (validationError) {
          console.error('Session validation failed:', validationError);
          console.log('Validation Error Details:', {
            status: validationError.response?.status,
            data: validationError.response?.data,
            headers: validationError.response?.headers
          });

          // If session validation fails, clear local storage and redirect
          localStorage.removeItem('ikiguide_session_id');
          for (let i = 1; i <= 4; i++) {
            localStorage.removeItem(`${sessionId}_response_${i}`);
          }
          navigate('/');
          return;
        }

        // Retrieve responses from localStorage
        const responses = {
          'What You\'re Good At': localStorage.getItem(`${sessionId}_response_1`) || 'Not specified',
          'What You Love': localStorage.getItem(`${sessionId}_response_2`) || 'Not specified',
          'What the World Needs': localStorage.getItem(`${sessionId}_response_3`) || 'Not specified',
          'What You Can Get Paid For': localStorage.getItem(`${sessionId}_response_4`) || 'Not specified'
        };

        // Log the session ID being used
        console.log('Fetching results for session ID:', sessionId);

        const response = await axios.get(`http://localhost:8000/api/results`, {
          params: { session_id: sessionId },
          withCredentials: true,
          headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
          }
        });

        // Ensure we have a paths property
        const allPaths = response.data.paths || response.data || [];
        console.log('Full API Response:', response.data);
        console.log('Raw Paths:', JSON.stringify(allPaths, null, 2));

        const summaryPath = allPaths.find(path => path.startsWith('SUMMARY:'));
        
        const ikigaiPaths = allPaths.filter(path => 
          path && 
          !path.startsWith('SUMMARY:') && 
          !path.startsWith('NO PATH:')
        );

        // Add summary to ikigaiPaths if found
        if (summaryPath) {
          ikigaiPaths.unshift('SUMMARY');
          ikigaiPaths.unshift(summaryPath.replace('SUMMARY:', '').trim());
        }

        console.log('Filtered Ikigai Paths:', JSON.stringify(ikigaiPaths, null, 2));

        // Only update state if component is still mounted
        if (isMounted) {
          setPaths(ikigaiPaths);
          setUserResponses(responses);
          setLoading(false);
        }
      } catch (err) {
        console.error('Error fetching results:', err);
        
        // Log detailed error information
        console.log('Error Details:', {
          name: err.name,
          message: err.message,
          status: err.response?.status,
          data: err.response?.data,
          headers: err.response?.headers
        });
        
        // Only update state if component is still mounted
        if (isMounted) {
          // More specific error handling
          if (err.response) {
            // The request was made and the server responded with a status code
            // that falls out of the range of 2xx
            setError(`Server error: ${err.response.status} - ${err.response.data.detail || 'Unknown error'}`);
          } else if (err.request) {
            // The request was made but no response was received
            setError('No response received from server. Please check your connection.');
          } else {
            // Something happened in setting up the request that triggered an Error
            setError(`Error: ${err.message || 'Unable to fetch results'}`);
          }
          
          setLoading(false);
          
          // Redirect to home page if there's a critical error
          navigate('/');
        }
      }
    };

    // Only fetch if not already loaded
    if (loading) {
      fetchResults();
    }

    // Cleanup function to prevent state updates on unmounted component
    return () => {
      isMounted = false;
    };
  }, [loading]); // Depend on loading to prevent unnecessary refetches

  // Render loading screen if still loading
  if (loading) {
    return <LoadingScreen />;
  }

  // Render error if there is an error
  if (error) {
    return (
      <div className="min-h-screen bg-white flex items-center justify-center p-8">
        <div className="w-full max-w-2xl bg-red-100 p-8 rounded-xl shadow-lg text-center">
          <h1 className="text-4xl font-bold text-red-600 mb-4">Oops! Something went wrong</h1>
          <p className="text-red-800 mb-6">{error}</p>
          <div className="flex justify-center space-x-4">
            <button 
              onClick={() => {
                setLoading(true);
                setError(null);
              }} 
              className="px-6 py-3 bg-ikigai-secondary text-white rounded-lg hover:bg-opacity-90 transition"
            >
              Retry
            </button>
            <button 
              onClick={startOver}
              className="px-6 py-3 bg-ikigai-main text-white rounded-lg hover:bg-opacity-90 transition"
            >
              Start Over
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-white p-6 flex justify-center">
      <div className="w-full max-w-2xl">
        <h1 className="text-4xl font-bold text-ikigai-main text-center mb-8">Your Ikigai Journey</h1>
        
        <div className="mb-8 bg-white p-6 rounded-lg shadow-md">
          <h2 className="text-2xl font-semibold text-ikigai-main mb-4">Your Inputs</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <p className="font-bold">What You're Good At:</p>
              <p>{userResponses['What You\'re Good At'] || 'Not specified'}</p>
            </div>
            <div>
              <p className="font-bold">What You Love:</p>
              <p>{userResponses['What You Love'] || 'Not specified'}</p>
            </div>
            <div>
              <p className="font-bold">What the World Needs:</p>
              <p>{userResponses['What the World Needs'] || 'Not specified'}</p>
            </div>
            <div>
              <p className="font-bold">What You Can Get Paid For:</p>
              <p>{userResponses['What You Can Get Paid For'] || 'Not specified'}</p>
            </div>
          </div>
        </div>

        <div className="space-y-6">
          <h2 className="text-3xl font-bold text-ikigai-main text-center mb-6">Your Potential Paths</h2>
          {paths.length === 0 && (
            <div className="text-center text-gray-600">
              No paths found. Please check the data source.
            </div>
          )}
          {(() => {
            // Group paths into title-description pairs, excluding SUMMARY
            const displayPaths = [];
            for (let i = 0; i < paths.length; i += 2) {
              // Exclude summary from initial paths
              if (paths[i] !== 'SUMMARY' && paths[i+1] !== 'SUMMARY') {
                displayPaths.push({
                  title: paths[i],
                  description: paths[i+1]
                });
              }
            }

            // Add summary at the end if it exists
            const summaryIndex = paths.indexOf('SUMMARY');
            if (summaryIndex !== -1) {
              displayPaths.push({
                title: 'SUMMARY',
                description: paths[summaryIndex + 1]
              });
            }

            return displayPaths.map((path, index) => (
              <div 
                key={index} 
                className={`bg-white p-6 rounded-lg shadow-md ${path.title === 'SUMMARY' ? 'mt-6 border-2 border-ikigai-main' : 'mb-4'}`}
              >
                <h3 className="text-2xl font-semibold text-ikigai-main mb-4">
                  {path.title === 'SUMMARY' ? 'SUMMARY OF PATHS' : path.title}
                </h3>
                <p className="text-ikigai-black">{path.description}</p>
              </div>
            ));
          })()}
        </div>

        <div className="mt-6 flex flex-col items-center space-y-4">
          <button 
            onClick={startOver}
            className="bg-[var(--color-main)] text-white px-6 py-3 rounded-lg hover:opacity-80 transition duration-300"
          >
            Start Over
          </button>
          <button 
            onClick={() => setShowEmailModal(true)}
            className="bg-[var(--color-secondary)] text-white px-6 py-3 rounded-lg hover:opacity-80 transition duration-300"
          >
            Email My Results
          </button>
        </div>

        {showEmailModal && <EmailModal />}
      </div>
    </div>
  );
};

export default ResultsPage;