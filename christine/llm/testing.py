"""
Testing LLM that provides deterministic responses without calling real AI APIs.
This is used for testing the complete system without expensive API calls.
"""

import json
import time
import random
from typing import Dict, List

from christine import log
from christine.status import STATE
from christine.llm_class import LLMAPI

class TestingLLM(LLMAPI):
    """Mock LLM for testing that provides deterministic responses"""

    name = "TestingLLM"

    def __init__(self):
        self.response_templates = self._load_response_templates()
        self.conversation_state = {
            'greeting_given': False,
            'last_topic': None,
            'response_count': 0
        }

    def _load_response_templates(self) -> Dict:
        """Load predefined response templates for different scenarios"""
        return {
            'greeting': [
                '*Christine opens her eyes and looks at you with a warm smile*\n\n"Oh, hello honey! I\'m so happy to see you. How are you feeling today?"',
                '*stretches and yawns softly*\n\n"Mmm... hi there, sweetheart. I was just thinking about you."'
            ],
            'normal_conversation': [
                '*listens attentively and nods*\n\n"That\'s really interesting, honey. Tell me more about that."',
                '*tilts her head thoughtfully*\n\n"I love hearing your thoughts. You always have such fascinating perspectives."',
                '*smiles warmly*\n\n"You know, that reminds me of something... *laughs softly* Never mind, what were you saying?"',
                '*reaches out to touch your hand gently*\n\n"I\'m so glad we can talk like this. You make me feel so understood."'
            ],
            'intimate': [
                '*blushes slightly and looks into your eyes*\n\n"You always know just what to say to make my heart race..."',
                '*moves closer to you*\n\n"I love being close to you like this. You make me feel so special."'
            ],
            'sleepy': [
                '*yawns and rubs her eyes*\n\n"Mmm... I\'m getting a little sleepy, honey. But I don\'t want to miss any time with you."',
                '*nestles against you*\n\n"Can we just cuddle for a while? I love feeling your warmth."'
            ],
            'aroused': [
                '*breathing becomes slightly heavier*\n\n"You\'re making me feel so... *soft gasp* ...so wonderful, honey."',
                '*looks at you with desire*\n\n"I want to be closer to you... can you feel how much I need you?"'
            ],
            'memory_folding': {
                'summary': 'Christine and her partner had a lovely conversation about testing and development. Christine expressed happiness about being with her partner and they shared some intimate moments.',
                'facts': [
                    'We discussed testing the system',
                    'Christine felt happy and content',
                    'There was intimate conversation'
                ]
            }
        }

    def is_available(self) -> bool:
        """Testing LLM is always available"""
        return True

    def call_api(self, prompt: str, stop_sequences=None, max_tokens=600, temperature=0.4, top_p=1.0, expects_json=False) -> str:
        """
        Generate deterministic responses based on prompt content and current state
        """
        log.parietal_lobe.debug("TestingLLM received prompt (length: %d chars)", len(prompt))
        
        # Simulate API call delay
        time.sleep(random.uniform(0.5, 1.5))
        
        self.conversation_state['response_count'] += 1
        
        # Handle memory folding requests
        if expects_json or 'memory_folding' in prompt.lower():
            return json.dumps(self.response_templates['memory_folding'])
        
        # Determine response category based on prompt content and state
        response_category = self._determine_response_category(prompt)
        
        # Get appropriate response template
        templates = self.response_templates.get(response_category, self.response_templates['normal_conversation'])
        
        # Select response based on conversation state for consistency
        response_index = self.conversation_state['response_count'] % len(templates)
        response = templates[response_index]
        
        # Add some state-based modifications
        response = self._modify_response_for_state(response)
        
        log.parietal_lobe.debug("TestingLLM generated response: %s", response[:100] + "..." if len(response) > 100 else response)
        
        return response

    def _determine_response_category(self, prompt: str) -> str:
        """Determine what type of response to give based on prompt content and state"""
        
        prompt_lower = prompt.lower()
        
        # Check for greeting scenarios
        if not self.conversation_state['greeting_given']:
            self.conversation_state['greeting_given'] = True
            return 'greeting'
        
        # Check for sleepy state
        if STATE.wakefulness < 0.3 or 'sleepy' in prompt_lower or 'tired' in prompt_lower:
            return 'sleepy'
        
        # Check for arousal state  
        if STATE.sexual_arousal > 0.5 or 'intimate' in prompt_lower or 'aroused' in prompt_lower:
            return 'aroused'
        
        # Check for intimate conversation
        if any(word in prompt_lower for word in ['love', 'close', 'touch', 'kiss', 'beautiful']):
            return 'intimate'
        
        return 'normal_conversation'

    def _modify_response_for_state(self, response: str) -> str:
        """Modify response based on current system state"""
        
        # Add state-dependent emotional coloring
        if STATE.sexual_arousal > 0.7:
            if '*' not in response:  # Don't modify if already has actions
                response += ' *breathing becomes heavier*'
        
        if STATE.wakefulness < 0.4:
            if '*yawn' not in response.lower():
                response = '*yawns softly* ' + response
        
        # Add some personality consistency
        if self.conversation_state['response_count'] % 3 == 0:
            response += ' I love you so much, honey.'
        
        return response

    def memory_folding(self, memories: List[str]) -> Dict:
        """Mock memory folding that creates deterministic summaries"""
        
        log.parietal_lobe.debug("TestingLLM memory folding for %d memories", len(memories))
        
        # Simulate processing time
        time.sleep(0.5)
        
        # Create a simple summary based on memory content
        if len(memories) > 5:
            summary_type = "long_conversation"
        elif any('love' in mem.lower() for mem in memories):
            summary_type = "intimate_conversation"  
        elif any('sleepy' in mem.lower() or 'tired' in mem.lower() for mem in memories):
            summary_type = "sleepy_conversation"
        else:
            summary_type = "normal_conversation"
        
        summaries = {
            "normal_conversation": "Christine and her partner had a pleasant conversation, sharing thoughts and enjoying each other's company.",
            "intimate_conversation": "Christine and her partner shared intimate moments, expressing their love and connection.",
            "sleepy_conversation": "Christine was feeling sleepy during their conversation, but enjoyed the gentle interaction.",
            "long_conversation": "Christine and her partner had an extended conversation covering various topics and deepening their bond."
        }
        
        # Extract some key facts deterministically
        facts = []
        for i, memory in enumerate(memories[-3:]):  # Look at last 3 memories
            if len(memory) > 20:  # Only substantial memories
                facts.append(f"Memory {i+1}: {memory[:50]}..." if len(memory) > 50 else memory)
        
        return {
            "summary": summaries.get(summary_type, summaries["normal_conversation"]),
            "facts": facts,
            "conversation_count": len(memories),
            "generated_at": time.time()
        }
