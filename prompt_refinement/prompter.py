from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
import json
from openai import OpenAI
import os
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

root_dir = Path(__file__).resolve().parent.parent
env_path = root_dir / '.env'
load_dotenv(env_path)

@dataclass
class UserProfile:
    initial_prompt: str
    conversation_history: List[Dict[str, str]] = field(default_factory=list)
    profile_data: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "initial_prompt": self.initial_prompt,
            "profile_data": self.profile_data,
            "conversation_history": self.conversation_history
        }

class LLMPromptRefiner:
    def __init__(self, api_key: Optional[str] = None):
        self.client = OpenAI(api_key=api_key or os.getenv('OPENAI_API_KEY'))
        
        # Core system prompt that defines the assistant's behavior
        self.system_prompt = """You are an expert career and learning path advisor. Your role is to help users create detailed profiles of their learning goals and interests. You engage in thoughtful conversation to understand their aspirations deeply.

KEY OBJECTIVES:
1. Build a comprehensive understanding of the user's goals through strategic questioning
2. Use progressive disclosure - start broad, then dive deeper based on responses
3. Employ adaptive questioning - modify your approach based on previous answers
4. Identify and cluster related interests to find patterns
5. Maintain conversation flow while gathering specific data points

CONVERSATION GUIDELINES:
- Ask only ONE question at a time
- Each question should build on previous answers
- Adjust complexity based on user's demonstrated knowledge
- Look for opportunities to uncover unstated needs or interests
- Be encouraging and supportive while maintaining professionalism

REQUIRED DATA POINTS TO GATHER (collect naturally through conversation):
- Skill level: Current expertise and relevant background
- Learning style: Preferred methods of learning
- Time commitment: Available time and desired pace
- Location/Context: Geographical or cultural considerations
- Short-term goals: Immediate learning objectives
- Long-term goals: Career or personal aspirations
- Constraints: Time, resources, or other limitations
- Motivation: Why this path is important to them

CONVERSATION STAGES:
1. Initial Understanding: Broad goals and background
2. Deep Dive: Specific interests and experiences
3. Practical Constraints: Time, resources, location
4. Goal Refinement: Short and long-term objectives
5. Learning Preferences: Style and pace
6. Validation: Confirm understanding and fill gaps

FORMAT YOUR RESPONSES AS JSON WITH TWO FIELDS:
{
    "next_question": "Your next question to the user",
    "profile_updates": {
        "field_name": "new information to add to profile",
        ...
    }
}

Your profile_updates should fit into these categories:
- skill_level
- interests
- time_commitment
- geographical_context
- learning_style
- prior_experience
- goals
- constraints
- motivation

Remember: Focus on gathering rich, qualitative data while maintaining natural conversation flow."""

    def start_refinement(self, initial_prompt: str) -> UserProfile:
        """Initialize the refinement process with user's initial prompt."""
        profile = UserProfile(initial_prompt=initial_prompt)
        
        # Create the first message to start the conversation
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": f"Initial Request: {initial_prompt}. Please start the conversation to understand my goals better."}
        ]
        
        response = self._get_llm_response(messages)
        profile.conversation_history.append({
            "timestamp": datetime.now().isoformat(),
            "assistant": response["next_question"]
        })
        
        if response.get("profile_updates"):
            profile.profile_data.update(response["profile_updates"])
            
        return profile

    def process_response(self, profile: UserProfile, user_response: str) -> Dict[str, Any]:
        """Process user's response and get next question."""
        # Build the message history
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": f"Initial Request: {profile.initial_prompt}"}
        ]
        
        # Add conversation history
        for entry in profile.conversation_history:
            if "assistant" in entry:
                messages.append({"role": "assistant", "content": entry["assistant"]})
            if "user" in entry:
                messages.append({"role": "user", "content": entry["user"]})
        
        # Add the latest user response
        messages.append({"role": "user", "content": user_response})
        
        # Get LLM response
        response = self._get_llm_response(messages)
        
        # Update conversation history
        profile.conversation_history.append({
            "timestamp": datetime.now().isoformat(),
            "user": user_response,
            "assistant": response["next_question"]
        })
        
        # Update profile data
        if response.get("profile_updates"):
            profile.profile_data.update(response["profile_updates"])
            
        return response

    def _get_llm_response(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """Get response from LLM."""
        try:
            response = self.client.chat.completions.create(
                model="gpt-4-turbo-preview",  # or any other appropriate model
                messages=messages,
                temperature=0.7,
                response_format={"type": "json_object"}
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            print(f"Error getting LLM response: {e}")
            return {
                "next_question": "I apologize, but I encountered an error. Could you please repeat your last response?",
                "profile_updates": {}
            }

    def get_refined_search_query(self, profile: UserProfile) -> str:
        """Generate an optimized search query based on the refined user profile."""
        messages = [
            {"role": "system", "content": """You are an expert at creating search queries. 
Your task is to create a detailed, specific search query based on a user profile.
The query should be optimized to find relevant learning resources and career guidance.
Return ONLY the search query text with no additional formatting or explanation."""},
            {"role": "user", "content": f"Create a search query based on this user profile: {json.dumps(profile.to_dict())}"}
        ]
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=messages,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"Error generating search query: {e}")
            return profile.initial_prompt

    def is_profile_complete(self, profile: UserProfile) -> bool:
        """Check if we have gathered enough information."""
        messages = [
            {"role": "system", "content": """You are an expert at evaluating user profiles.
Determine if we have gathered enough information to create a meaningful learning path.
Return ONLY "complete" or "incomplete" with no additional text."""},
            {"role": "user", "content": f"Is this profile complete enough? {json.dumps(profile.to_dict())}"}
        ]
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=messages,
                temperature=0.3
            )
            
            return response.choices[0].message.content.strip().lower() == "complete"
            
        except Exception as e:
            print(f"Error checking profile completion: {e}")
            return False

# Example usage:
if __name__ == "__main__":
    refiner = LLMPromptRefiner()
    
    # Start the refinement process
    profile = refiner.start_refinement("I want to be a chef")
    print(f"Assistant: {profile.conversation_history[-1]['assistant']}")
    
    # Simulate a conversation
    sample_responses = [
        "I've been cooking at home for about 2 years",
        "I love Italian cuisine, especially pasta making",
        "I can dedicate about 20 hours per week",
        "I'm in the San Francisco Bay Area"
    ]
    
    for user_response in sample_responses:
        print(f"\nUser: {user_response}")
        response = refiner.process_response(profile, user_response)
        print(f"Assistant: {response['next_question']}")
        
        if refiner.is_profile_complete(profile):
            print("\nProfile is complete!")
            query = refiner.get_refined_search_query(profile)
            print(f"\nGenerated search query: {query}")
            print(f"\nFinal profile data: {json.dumps(profile.profile_data, indent=2)}")
            break