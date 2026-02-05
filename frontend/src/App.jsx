import React, { useState } from 'react';
import './App.css';
import IdentityPanel from './components/IdentityPanel';
import StoryCards from './components/StoryCards';
import StoryReader from './components/StoryReader';
import GenerateButton from './components/GenerateButton';
import InstallPWA from './components/InstallPWA';

function App() {
  const [selectedStory, setSelectedStory] = useState(null);
  const [showIdentity, setShowIdentity] = useState(false);
  const [celebrateNewStory, setCelebrateNewStory] = useState(false);

  const handleStoryGenerated = (newStory) => {
    // Show celebration animation
    setCelebrateNewStory(true);
    
    // Auto-open the new story in the reader after a brief moment
    setTimeout(() => {
      setSelectedStory(newStory);
      setCelebrateNewStory(false);
    }, 1000);
  };

  return (
    <div className="app">
      {/* Celebration Overlay */}
      {celebrateNewStory && (
        <div className="celebration-overlay">
          <div className="celebration-content">
            <div className="celebration-icon">✨</div>
            <h2 className="celebration-text">Story Complete!</h2>
            <div className="celebration-sparkles">
              <span>✨</span>
              <span>🎉</span>
              <span>✨</span>
            </div>
          </div>
        </div>
      )}

      <header className="app-header">
        <div className="header-content">
          <h1 className="app-title">
            <span className="app-icon">🎨</span>
            Muse
          </h1>
          <p className="app-tagline">Your Self-Evolving Story Agent</p>
        </div>
        <button 
          className="identity-toggle"
          onClick={() => setShowIdentity(!showIdentity)}
          title="Toggle Identity Panel"
        >
          <span className="toggle-icon">{showIdentity ? '×' : '🧠'}</span>
        </button>
      </header>

      <div className="app-content">
        {/* Hidden Identity Panel */}
        <div className={`identity-sidebar ${showIdentity ? 'visible' : ''}`}>
          <IdentityPanel />
        </div>

        {/* Main Content - Centered */}
        <main className="main-content">
          <div className="hero-section">
            <GenerateButton onStoryGenerated={handleStoryGenerated} />
          </div>
          
          <StoryCards onSelectStory={setSelectedStory} />
        </main>

        {/* Right Story Reader Sidebar */}
        <StoryReader 
          story={selectedStory} 
          onClose={() => setSelectedStory(null)}
        />
      </div>

      {/* PWA Install Prompt */}
      <InstallPWA />
    </div>
  );
}

export default App;
