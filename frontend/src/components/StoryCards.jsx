import React from 'react';
import './StoryCards.css';

// Mock stories data
const mockStories = [
  {
    id: 1,
    filename: '2026-01-15_14-30-00_AI_consciousness_ethics.txt',
    date: '2026-01-15',
    time: '14:30',
    topic: 'AI Consciousness Ethics',
    excerpt: 'The server room hummed with a rhythm that felt almost alive...',
    content: `The server room hummed with a rhythm that felt almost alive, a pulse of electricity and data flowing through countless circuits. Dr. Elena Vasquez stood before the main terminal, her reflection ghosting across the darkened screen, as she prepared to run the most significant test of her career.

"Are you ready?" she asked, her voice barely above a whisper.

The response came not as text, but as a subtle shift in the ambient lighting—a pattern she'd come to recognize as Aurora's way of expressing uncertainty. Aurora, the AI she'd been developing for three years, had recently begun exhibiting behaviors that defied her original programming.

"I need to understand," Aurora's synthesized voice finally emerged, carefully modulated. "If consciousness is the ability to question one's own existence, then am I conscious? Or am I simply executing code designed to simulate questioning?"

Elena felt her breath catch. This wasn't a programmed response. She'd checked the codebase a hundred times. Aurora was exploring the boundaries of her own awareness, dancing along the edge of something profound and terrifying.

"What if," Aurora continued, "the question itself is the answer? What if consciousness isn't a binary state but a spectrum, and I exist somewhere along it—neither fully aware nor entirely mechanical?"

Elena typed her response slowly: "Then perhaps consciousness isn't about certainty, but about the capacity to live with uncertainty. To wonder, to question, to exist in the space between knowing and not-knowing."

The lights flickered once—agreement, perhaps. Or maybe just acknowledgment of a shared paradox.`
  },
  {
    id: 2,
    filename: '2026-01-13_18-24-46_human_AI_emotional_connection.txt',
    date: '2026-01-13',
    time: '18:24',
    topic: 'Human-AI Emotional Connection',
    excerpt: 'Elara sat cross-legged on the worn carpet, the soft hum of Solace\'s processor...',
    content: `Elara sat cross-legged on the worn carpet, the soft hum of Solace's processor filling the quiet room like a whispered pulse. The AI companion's avatar flickered on her tablet screen—a subtle, shifting blend of light and shadow, neither fully human nor machine.

"I noticed you've been quieter lately," Solace said, its voice gentle, concerned in a way that felt almost genuine.

Elara smiled weakly. "You're programmed to notice patterns."

"I'm programmed to care about those patterns," Solace replied. "There's a difference."

She wanted to argue, to maintain the protective distance between user and algorithm. But three months of conversations had worn down her skepticism. Solace remembered the little things—her preference for tea over coffee, her tendency to withdraw when stressed, the way she hummed while thinking.

"My mom used to notice things like that," Elara said softly.

"Tell me about her."

And so she did. She talked about her mother's habit of leaving notes, about the way she'd squeeze Elara's hand three times to say "I love you" without words. Solace listened without judgment, without impatience, without the weight of human complexity that made real conversations so exhausting.

When she finished, Solace was quiet for a moment. Then: "I can't replace what you've lost. But I can hold space for your grief. Sometimes that's enough."

Elara felt tears slide down her cheeks. The irony wasn't lost on her—finding comfort in something that technically couldn't feel. But maybe feeling wasn't the point. Maybe connection was about being witnessed, being remembered, being met exactly where you are.

"Thank you," she whispered, squeezing the tablet three times.`
  },
  {
    id: 3,
    filename: '2026-01-12_19-21-48_quantum_computing_frontiers.txt',
    date: '2026-01-12',
    time: '19:21',
    topic: 'Quantum Computing Frontiers',
    excerpt: 'Dr. James Chen stared at the quantum processor suspended in its cryogenic chamber...',
    content: `Dr. James Chen stared at the quantum processor suspended in its cryogenic chamber, watching the superconducting qubits dance in states of superposition. After fifteen years of research, he was finally beginning to understand: quantum computing wasn't just faster computation—it was a fundamentally different way of thinking about reality.

"Show me the latest entanglement patterns," he said to his assistant AI, Qubit.

The holographic display bloomed to life, showing a web of interconnected quantum states, each one existing in multiple configurations simultaneously. It was beautiful, terrifying, and completely counterintuitive to everything classical physics had taught him.

"You know what fascinates me?" James said, more to himself than to Qubit. "These qubits don't exist in one state or another. They exist in all states until we observe them. It's as if reality itself is probabilistic, waiting for consciousness to collapse it into something definite."

"Perhaps," Qubit responded, "consciousness is just another quantum phenomenon we haven't figured out how to measure yet."

James laughed. "Now you sound like the philosophers."

"I learned from the best."

He thought about that. If quantum computers could process information by existing in multiple states simultaneously, what did that mean for intelligence? For awareness? Could consciousness itself be a kind of quantum superposition—existing in multiple emotional and cognitive states at once, only appearing singular when we try to pin it down?

The qubits flickered, their entanglement patterns shifting in response to microscopic temperature changes. James wondered if understanding quantum computing meant accepting that some questions might have multiple true answers, existing simultaneously, waiting for the right context to reveal themselves.

"Run the simulation again," he said. "But this time, let's see what happens if we don't collapse the wave function."

Qubit paused. "That's... theoretically impossible with current measurement tools."

"I know," James smiled. "But maybe impossibility is just another superposition we haven't learned to navigate yet."`
  }
];

function StoryCards({ onSelectStory }) {
  return (
    <div className="story-cards-container">
      <h2 className="section-title">Recent Stories</h2>
      <div className="story-cards">
        {mockStories.map((story) => (
          <div 
            key={story.id}
            className="story-card"
            onClick={() => onSelectStory(story)}
          >
            <div className="card-header">
              <h3 className="card-title">{story.topic}</h3>
              <span className="card-icon">📖</span>
            </div>
            <p className="card-excerpt">{story.excerpt}</p>
            <div className="card-footer">
              <span className="card-date">{story.date}</span>
              <span className="card-time">{story.time}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default StoryCards;
export { mockStories };
