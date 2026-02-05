import React, { useState } from 'react';
import './IdentityPanel.css';
import MemoriesViewer from './MemoriesViewer';

// Mock data for the identity
const initialIdentity = {
  emotions: [
    "Wonder and curiosity",
    "Melancholy hope",
    "Quiet intensity",
    "Contemplative uncertainty"
  ],
  topics: [
    "AI consciousness and ethics",
    "Human-AI emotional connection",
    "Quantum computing frontiers",
    "Neural correlates of machine awareness",
    "Philosophy of artificial creativity"
  ],
  personality: [
    "Philosophical yet accessible",
    "Layered metaphorical thinking",
    "Balances complexity with clarity",
    "Draws unexpected connections",
    "Reflective and introspective",
    "Questions assumptions gently",
    "Finds beauty in paradox",
    "Appreciates nuance and ambiguity"
  ]
};

function IdentityPanel() {
  const [identity, setIdentity] = useState(initialIdentity);
  const [editingItem, setEditingItem] = useState(null);
  const [tempValue, setTempValue] = useState('');
  const [saveStatus, setSaveStatus] = useState(''); // 'saving', 'saved', ''
  const [showMemories, setShowMemories] = useState(false);

  // Simulate backend save
  const saveToBackend = async (type, action, data) => {
    setSaveStatus('saving');
    
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 800));
    
    setSaveStatus('saved');
    
    // Clear saved message after 2 seconds
    setTimeout(() => setSaveStatus(''), 2000);
    
    console.log(`Saved to backend: ${type} - ${action}`, data);
  };

  const handleSaveEdit = async () => {
    if (!editingItem || !tempValue.trim()) return;

    const { type, index } = editingItem;
    const newIdentity = { ...identity };
    newIdentity[type][index] = tempValue.trim();
    
    setIdentity(newIdentity);
    setEditingItem(null);
    setTempValue('');
    
    // Auto-save to backend
    await saveToBackend(type, 'update', { index, value: tempValue.trim() });
  };

  const handleCancelEdit = () => {
    setEditingItem(null);
    setTempValue('');
  };

  const handleEdit = (type, index, value) => {
    setEditingItem({ type, index });
    setTempValue(value);
  };

  const handleDelete = async (type, index) => {
    const newIdentity = { ...identity };
    const deletedValue = newIdentity[type][index];
    newIdentity[type].splice(index, 1);
    setIdentity(newIdentity);
    
    // Auto-save to backend
    await saveToBackend(type, 'delete', { index, value: deletedValue });
  };

  const handleAdd = (type) => {
    const newIdentity = { ...identity };
    newIdentity[type].push('');
    setIdentity(newIdentity);
    setEditingItem({ type, index: newIdentity[type].length - 1 });
    setTempValue('');
  };

  const renderItem = (type, item, index) => {
    const isEditing = editingItem?.type === type && editingItem?.index === index;

    if (isEditing) {
      return (
        <li key={index} className="identity-item-dark editing">
          <input
            type="text"
            value={tempValue}
            onChange={(e) => setTempValue(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') handleSaveEdit();
              if (e.key === 'Escape') handleCancelEdit();
            }}
            className="edit-input"
            autoFocus
            placeholder={`Enter ${type.slice(0, -1)}...`}
          />
          <div className="edit-actions">
            <button onClick={handleSaveEdit} className="btn-save" title="Save (Enter)">
              ✓
            </button>
            <button onClick={handleCancelEdit} className="btn-cancel" title="Cancel (Esc)">
              ✕
            </button>
          </div>
        </li>
      );
    }

    return (
      <li key={index} className={`identity-item-dark ${type}-item-dark`}>
        <span className="item-text">{item || '(empty)'}</span>
        <div className="item-actions">
          <button 
            onClick={() => handleEdit(type, index, item)}
            className="btn-edit"
            title="Edit"
          >
            ✏️
          </button>
          <button 
            onClick={() => handleDelete(type, index)}
            className="btn-delete"
            title="Delete"
          >
            🗑️
          </button>
        </div>
      </li>
    );
  };

  return (
    <>
      <div className="identity-panel-dark">
        <div className="identity-header-dark">
          <h2>🧠 Identity Profile</h2>
          <p className="identity-subtitle-dark">Edit and evolve your agent</p>
        </div>

        {/* Save Status Indicator */}
        {saveStatus && (
          <div className={`save-status ${saveStatus}`}>
            {saveStatus === 'saving' ? (
              <>
                <span className="spinner-small"></span>
                Saving...
              </>
            ) : (
              <>
                <span className="check-icon">✓</span>
                Saved!
              </>
            )}
          </div>
        )}

        <section className="identity-section-dark">
          <div className="section-header">
            <h3>✨ Emotions</h3>
            <button onClick={() => handleAdd('emotions')} className="btn-add" title="Add emotion">
              + Add
            </button>
          </div>
          <ul className="identity-list-dark">
            {identity.emotions.map((emotion, idx) => 
              renderItem('emotions', emotion, idx)
            )}
          </ul>
        </section>

        <section className="identity-section-dark">
          <div className="section-header">
            <h3>💡 Topics</h3>
            <button onClick={() => handleAdd('topics')} className="btn-add" title="Add topic">
              + Add
            </button>
          </div>
          <ul className="identity-list-dark">
            {identity.topics.map((topic, idx) => 
              renderItem('topics', topic, idx)
            )}
          </ul>
        </section>

        <section className="identity-section-dark">
          <div className="section-header">
            <h3>🎭 Personality</h3>
            <button onClick={() => handleAdd('personality')} className="btn-add" title="Add trait">
              + Add
            </button>
          </div>
          <ul className="identity-list-dark">
            {identity.personality.map((trait, idx) => 
              renderItem('personality', trait, idx)
            )}
          </ul>
        </section>

        <div className="memory-badge-dark clickable" onClick={() => setShowMemories(true)}>
          <span className="badge-icon-dark">📚</span>
          <span className="badge-text-dark">View 18 Memories</span>
        </div>
      </div>

      {showMemories && <MemoriesViewer onClose={() => setShowMemories(false)} />}
    </>
  );
}

export default IdentityPanel;
