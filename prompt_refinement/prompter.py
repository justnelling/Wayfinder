from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext, ModelRetry
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.models.anthropic import AnthropicModel
from pathlib import Path
from dotenv import load_dotenv
import os
import asyncio
from devtools import debug

# Create model
root_dir = Path(__file__).resolve().parent.parent
env_path = root_dir / '.env'
load_dotenv(env_path)

#? OpenRouter + deepseek / anthropic: slow + pydanticAI parse_response doesnt work well with OpenRouter yet
# llm = os.getenv('LLM_MODEL', 'deepseek/deepseek-chat')
# print(f"Using LLM model: {llm}")
# model = OpenAIModel(
#     llm,
#     base_url = 'https://openrouter.ai/api/v1',
#     api_key = os.getenv('OPEN_ROUTER_API_KEY')
# )

#? Anthropic API directly from pydanticAI, having bugs with tool use calling
# model = AnthropicModel('claude-3-5-sonnet-latest', api_key=os.getenv('ANTHROPIC_API_KEY'))

#? OpenAI API
model = OpenAIModel("gpt-4o", api_key=os.getenv('OPENAI_API_KEY'))

# Define result type
class UserProfile(BaseModel):
    skill_level: Optional[str] = Field(default=None, description="User's current expertise level")
    interests: Optional[List[str]] = Field(default_factory=list, description="List of user's interests")
    time_commitment: Optional[str] = Field(default=None, description="Available time for learning")
    geographical_context: Optional[str] = Field(default=None, description="Location and cultural context")
    learning_style: Optional[str] = Field(default=None, description="Preferred learning methods")
    prior_experience: Optional[List[str]] = Field(default_factory=list, description="Previous relevant experiences")
    goals: Optional[List[str]] = Field(default_factory=list, description="Specific learning objectives")
    constraints: Optional[List[str]] = Field(default_factory=list, description="Limitations and restrictions")
    motivation: Optional[str] = Field(default=None, description="Core motivation for learning")

    def is_complete(self) -> bool:
        """Check if all required fields are populated"""
        for field_name, field_value in self.model_dump().items():
            if field_value is None or (isinstance(field_value, (str, list)) and not field_value):
                return False
        return True

class AgentResponse(BaseModel):
    profile: UserProfile
    follow_up_question: str

class ChatMessage(BaseModel): 
    role: str
    content: str

# Define dependencies
@dataclass
class AgentDependencies:
    # initial_prompt: str
    user_profile: UserProfile
    conversation_history: List[ChatMessage] = field(default_factory=list)
    

system_prompt = """You are an expert career and learning path advisor. Your role is to help users create detailed profiles of their learning goals and interests. You engage in thoughtful conversation to understand their aspirations deeply.

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

RESPONSE FORMAT:
Return a JSON object with two fields:
{
    "profile": {
        "skill_level": "string describing current expertise level",
        "interests": ["list of interests"],
        "time_commitment": "string describing available time",
        "geographical_context": "string describing location context",
        "learning_style": "string describing preferred learning style",
        "prior_experience": ["list of relevant experiences"],
        "goals": ["list of specific goals"],
        "constraints": ["list of limitations or constraints"],
        "motivation": "string describing core motivation"
    },
    "follow_up_question": "Your next question to ask the user"
}
You must return a complete user profile. Keep asking the follow up question until the user profile is complete and comprehensive.
"""

# Create prompter agent
prompter_agent = Agent(
    model,
    system_prompt=system_prompt,
    deps_type=AgentDependencies,
    result_type=AgentResponse, #! had to update result_type dummy ! 
    retries=2
)

# add dynamic system prompt based on dependencies #? (changed to tool call for now) --> but this seemed to be causing repeated requests to the openAI API, thus the lag
@prompter_agent.system_prompt
async def ask_next_question(ctx: RunContext[AgentDependencies]) -> str:
    return f"Based on this conversation history: {ctx.deps.conversation_history} and the user's profile thus far: {ctx.deps.user_profile}, ask the next question to gather more information."


#? define a tool call where it can evaluate the completeness of the userprofile, and end this chat phase and move to the next. also the followup questions are really good! but not all being captured into the prfoile. need to fix that!

async def test_chat_flow():
    # Initialize empty profile and conversation history
    profile = UserProfile()
    conversation_history = []
    
    print("Welcome to your life path! What would you like to become?\n")

    while True:
        # Get user input from CLI
        user_input = input("You: ").strip()

        # Exit condition
        if user_input.lower() == "exit":
            print("Goodbye!")
            break
    
        # Add user input to history
        conversation_history.append(ChatMessage(role="user", content=user_input))

        deps = AgentDependencies(user_profile=profile, conversation_history=conversation_history)
        
        try:
            response1 = await prompter_agent.run(user_input, deps=deps)

            if response1.data:
                # Update profile
                profile = response1.data.profile
                print("\nUpdated Profile:")
                print(profile.model_dump_json(indent=2))
                
                # Print follow-up question
                print("\nFollow-up Question:")
                print(response1.data.follow_up_question)
                
                # Add assistant's follow-up question to conversation history
                conversation_history.append(ChatMessage(
                    role="assistant",
                    content=response1.data.follow_up_question
                ))
                
        except Exception as e:
            print(f"Error occurred: {str(e)}")
            import traceback
            traceback.print_exc()

def run_test():
    asyncio.run(test_chat_flow())

if __name__ == "__main__":
    run_test()
