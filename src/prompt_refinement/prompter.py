from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any, Tuple
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
model = OpenAIModel("gpt-4o-mini", api_key=os.getenv('OPENAI_API_KEY'))

# Define result type
class UserProfile(BaseModel):
    life_path: Optional[str] = Field(default=None, description="User's desired career or learning path")
    skill_level: Optional[str] = Field(default=None, description="User's current expertise level")
    interests: Optional[List[str]] = Field(default_factory=list, description="List of user's interests")
    time_commitment: Optional[str] = Field(default=None, description="Available time for learning")
    geographical_context: Optional[str] = Field(default=None, description="Location and cultural context")
    learning_style: Optional[str] = Field(default=None, description="Preferred learning methods")
    prior_experience: Optional[List[str]] = Field(default_factory=list, description="Previous relevant experiences")
    goals: Optional[List[str]] = Field(default_factory=list, description="Specific learning objectives")
    constraints: Optional[List[str]] = Field(default_factory=list, description="Limitations and restrictions")
    motivation: Optional[str] = Field(default=None, description="Core motivation for learning")

    def is_complete(self) -> Tuple[bool, List[str]]:
        """
        Check if all fields meet requirements.
        Returns (is_complete, list_of_missing_fields)
        """
        requirements = {
            'life_path': lambda x: x is not None and isinstance(x, str) and len(x) >= 5,
            'skill_level': lambda x: x is not None and isinstance(x, str) and len(x) >= 5,
            'interests': lambda x: isinstance(x, list) and len(x) >= 1 and all(isinstance(i, str) and i.strip() for i in x),
            'time_commitment': lambda x: x is not None and isinstance(x, str) and len(x) >= 5,
            'geographical_context': lambda x: x is not None and isinstance(x, str) and len(x) >= 5,
            'learning_style': lambda x: x is not None and isinstance(x, str) and len(x) >= 5,
            'prior_experience': lambda x: isinstance(x, list) and len(x) >= 1 and all(isinstance(i, str) and i.strip() for i in x),
            'goals': lambda x: isinstance(x, list) and len(x) >= 1 and all(isinstance(i, str) and i.strip() for i in x),
            'constraints': lambda x: isinstance(x, list) and len(x) >= 1 and all(isinstance(i, str) and i.strip() for i in x),
            'motivation': lambda x: x is not None and isinstance(x, str) and len(x) >= 15
        }

        missing_fields = []
        for field, requirement in requirements.items():
            value = getattr(self, field)
            if not requirement(value):
                missing_fields.append(field)

        return len(missing_fields) == 0, missing_fields

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
    missing_fields: List[str] = field(default_factory=list)
    

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
- Life Path: User's overall desired career or learning path
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
        "life_path": "string describing overall desired career or learning path",
        "skill_level": "string describing current expertise level",
        "interests": ["list of interests"],
        "time_commitment": "string describing available time",
        "geographical_context": "string describing location context",
        "learning_style": "string describing preferred learning style",
        "prior_experience": ["list of relevant experiences"],
        "goals": ["list of specific goals, short and long term"],
        "constraints": ["list of limitations or constraints"],
        "motivation": "string describing core motivation"
    },
    "follow_up_question": "Your next question to ask the user"
}
IMPORTANT: Do not make assumptions or fill in profile fields without explicit information from the user. Ask questions one by one and fill up the profile gradually.
Keep asking the follow up question until the user profile is complete and comprehensive.
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
    return f"Based on this conversation history: {ctx.deps.conversation_history} and the user's profile thus far: {ctx.deps.user_profile}, ask the next question to gather more information and especially fill in for the missing fields: {ctx.deps.missing_fields}"


#? define a tool call where it can evaluate the completeness of the userprofile, and end this chat phase and move to the next. also the followup questions are really good! but not all being captured into the prfoile. need to fix that!
async def check_profile_completion(profile: UserProfile) -> Tuple[bool, List[str]]:
    """
    Check if the user profile is complete and return completion status and missing fields.
    Args:
        profile: The UserProfile object to evaluate
    Returns:
        Tuple of (is_complete: bool, missing_fields: list[str])
    """
    is_complete, missing_fields = profile.is_complete()
    
    if not is_complete:
        print(f"Incomplete fields: {missing_fields}")
    
    return is_complete, missing_fields


async def chat_flow():
    # Initialize empty profile and conversation history
    profile = UserProfile()
    conversation_history = []
    missing_fields_deps = []
    
    print("Welcome to your life path! What would you like to become?\n")

    while True:
        # Get user input from CLI
        user_input = input("You: ").strip()

        # Exit condition
        if user_input.lower() == "exit":
            print("Goodbye!")
            return profile.model_dump() # even if incomplete return the profile
    
        # Add user input to history
        conversation_history.append(ChatMessage(role="user", content=user_input))

        deps = AgentDependencies(user_profile=profile, conversation_history=conversation_history, missing_fields=missing_fields_deps)
        
        try:
            response1 = await prompter_agent.run(user_input, deps=deps)

            if response1.data:
                # Update profile
                profile = response1.data.profile
                print("\nUpdated Profile:")
                print(profile.model_dump_json(indent=2))

                # Check profile completion
                is_complete, missing_fields = await check_profile_completion(profile)
                
                if is_complete:
                    print("\nProfile is complete! Moving to next phase...")

                    return profile.model_dump() # return as python dictionary
                
                # if there are still missing fields, we make a second call to the LLM just to generate a more targeted follow-up question
                missing_fields_deps = missing_fields

                deps = AgentDependencies(user_profile=profile, conversation_history=conversation_history, missing_fields=missing_fields_deps)

                response2 = await prompter_agent.run(user_input, deps=deps)
                
                # Print follow-up question
                print("\nFollow-up Question:")
                print(response2.data.follow_up_question)
                
                # Add assistant's follow-up question to conversation history
                conversation_history.append(ChatMessage(
                    role="assistant",
                    content=response2.data.follow_up_question
                ))
                
        except Exception as e:
            print(f"Error occurred: {str(e)}")
            import traceback
            traceback.print_exc()

async def run_LLM_prompter_chat():
    # return asyncio.run(chat_flow())
    return await chat_flow()

if __name__ == "__main__":
    completed_profile = run_LLM_prompter_chat()
