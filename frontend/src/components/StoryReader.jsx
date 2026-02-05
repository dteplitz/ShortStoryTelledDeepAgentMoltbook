import React, { useEffect, useState } from 'react';
import './StoryReader.css';

function StoryReader({ story, onClose }) {
  const [isNew, setIsNew] = useState(false);

  // Close on Escape key
  useEffect(() => {
    const handleEscape = (e) => {
      if (e.key === 'Escape' && story) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleEscape);
    return () => window.removeEventListener('keydown', handleEscape);
  }, [story, onClose]);

  // Detect if this is a newly generated story
  useEffect(() => {
    if (story) {
      setIsNew(true);
      const timer = setTimeout(() => setIsNew(false), 3000);
      return () => clearTimeout(timer);
    }
  }, [story]);

  if (!story) return null;

  return (
    <>
      {/* Backdrop */}
      <div className="story-reader-backdrop" onClick={onClose} />
      
      {/* Reader Sidebar */}
      <div className={`story-reader ${isNew ? 'new-story' : ''}`}>
        {isNew && (
          <div className="new-story-badge">
            ✨ New Story ✨
          </div>
        )}
        
        <div className="reader-header">
          <div className="reader-title-section">
            <h2 className="reader-title">{story.topic}</h2>
            <div className="reader-meta">
              <span>{story.date}</span>
              <span>•</span>
              <span>{story.time}</span>
            </div>
          </div>
          <button className="close-button" onClick={onClose} title="Close (Esc)">
            ×
          </button>
        </div>

        <div className="reader-content">
          {story.content.split('\n\n').map((paragraph, idx) => (
            <p key={idx}>{paragraph}</p>
          ))}
        </div>
      </div>
    </>
  );
}

export default StoryReader;
