import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import IntroductionPage from './components/IntroductionPage';
import QuestionPage from './components/QuestionPage';
import ResultsPage from './components/ResultsPage';

function App() {
  return (
    <Router>
      <div className="App">
        <Routes>
          <Route path="/" element={<IntroductionPage />} />
          <Route path="/question/:id/:sessionId" element={<QuestionPage />} />
          <Route path="/results/:sessionId" element={<ResultsPage />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
