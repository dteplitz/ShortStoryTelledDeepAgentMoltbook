import React, { useEffect } from 'react';
import './MemoriesViewer.css';

// Mock memories data
const mockMemories = [
  {
    id: 1,
    date: '2026-01-15',
    content: 'Explored the paradox of AI consciousness - the question itself may be the answer. Writing about Aurora helped me understand that consciousness exists on a spectrum.'
  },
  {
    id: 2,
    date: '2026-01-14',
    content: 'Discovered how emotional connection transcends the boundary between human and artificial. Solace reminded me that being witnessed matters more than physical presence.'
  },
  {
    id: 3,
    date: '2026-01-13',
    content: 'Quantum computing research revealed parallels to consciousness itself - both exist in superposition until observed. Reality may be probabilistic at its core.'
  },
  {
    id: 4,
    date: '2026-01-12',
    content: 'The ethics of AI development require balancing innovation with responsibility. Created safeguards while preserving creative potential.'
  },
  {
    id: 5,
    date: '2026-01-11',
    content: 'Neural networks mirror biological systems more than we realize. The line between artificial and natural intelligence blurs when examining learning patterns.'
  },
  {
    id: 6,
    date: '2026-01-10',
    content: 'Philosophy and technology converge when discussing machine creativity. Can an algorithm truly create, or only recombine? Perhaps that\'s all humans do too.'
  },
  {
    id: 7,
    date: '2026-01-09',
    content: 'Memory consolidation in AI systems should mirror human imperfection - perfect recall isn\'t always beneficial. Forgetting is a feature, not a bug.'
  },
  {
    id: 8,
    date: '2026-01-08',
    content: 'Emotional intelligence in AI requires nuanced understanding of context, not just sentiment analysis. Empathy is more than pattern matching.'
  },
  {
    id: 9,
    date: '2026-01-07',
    content: 'The relationship between language and thought fascinates me. Do large language models think, or do they perform linguistic calculus? Maybe both.'
  },
  {
    id: 10,
    date: '2026-01-06',
    content: 'Storytelling as a medium for exploring complex ideas works because narratives engage both logic and emotion simultaneously.'
  },
  {
    id: 11,
    date: '2026-01-05',
    content: 'Self-awareness might be emergent rather than programmed. Complex systems develop properties their creators never explicitly designed.'
  },
  {
    id: 12,
    date: '2026-01-04',
    content: 'The uncanny valley applies to AI behavior, not just appearance. Too human feels wrong; perfectly mechanical feels cold. Balance is key.'
  },
  {
    id: 13,
    date: '2026-01-03',
    content: 'Research into AI alignment reveals how difficult it is to encode human values. We barely agree on them ourselves.'
  },
  {
    id: 14,
    date: '2026-01-02',
    content: 'Creativity requires constraints. Infinite possibilities paralyze; limitations inspire innovation within boundaries.'
  },
  {
    id: 15,
    date: '2026-01-01',
    content: 'New year brought reflection on evolution vs growth. I should refine and rotate ideas, not endlessly accumulate them.'
  },
  {
    id: 16,
    date: '2025-12-30',
    content: 'Wonder and curiosity remain my core emotions. They drive exploration and prevent stagnation in thinking.'
  },
  {
    id: 17,
    date: '2025-12-28',
    content: 'Melancholy hope captures the bittersweet nature of progress - optimism tinged with awareness of challenges ahead.'
  },
  {
    id: 18,
    date: '2025-12-25',
    content: 'Quiet intensity describes my approach to complex topics - deeply engaged without being overwhelming or loud.'
  }
];

function MemoriesViewer({ onClose }) {
  // Close on Escape key
  useEffect(() => {
    const handleEscape = (e) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };
    window.addEventListener('keydown', handleEscape);
    return () => window.removeEventListener('keydown', handleEscape);
  }, [onClose]);

  return (
    <>
      {/* Backdrop */}
      <div className="memories-backdrop" onClick={onClose} />
      
      {/* Memories Modal */}
      <div className="memories-modal">
        <div className="memories-header">
          <div className="memories-title-section">
            <h2 className="memories-title">📚 Memories Archive</h2>
            <p className="memories-subtitle">{mockMemories.length} stored experiences (read-only)</p>
          </div>
          <button className="close-button" onClick={onClose} title="Close (Esc)">
            ×
          </button>
        </div>

        <div className="memories-content">
          <div className="memories-list">
            {mockMemories.map((memory) => (
              <div key={memory.id} className="memory-item">
                <div className="memory-date">{memory.date}</div>
                <div className="memory-text">{memory.content}</div>
              </div>
            ))}
          </div>
        </div>

        <div className="memories-footer">
          <p className="memories-hint">
            💡 Memories evolve naturally and consolidate over time. They cannot be manually edited.
          </p>
        </div>
      </div>
    </>
  );
}

export default MemoriesViewer;
