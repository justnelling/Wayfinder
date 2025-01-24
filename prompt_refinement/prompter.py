from dataclasses import dataclass, field
from typing import List, Optional
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIModel
from pathlib import Path
from dotenv import load_dotenv
import os
import asyncio

# Create model
root_dir = Path(__file__).resolve().parent.parent
env_path = root_dir / '.env'
load_dotenv(env_path)

llm = os.getenv('LLM_MODEL', 'deepseek/deepseek-r1')
model = OpenAIModel(
    llm,
    base_url = 'https://openrouter.ai/api/v1',
    api_key = os.getenv('OPEN_ROUTER_API_KEY')
)

# Define dependencies
@dataclass
class PrompterDependencies:
    initial_prompt: str
    conversation_history: List[dict] = field(default_factory=list)

# Define result type
class UserProfile(BaseModel):
    skill_level: Optional[str] = Field(None, description="User's current skill level")
    interests: Optional[List[str]] = Field(None, description="List of user's interests")
    time_commitment: Optional[str] = Field(None, description="User's available time commitment")
    geographical_context: Optional[str] = Field(
        None, description="User's geographical context"
    )
    learning_style: Optional[str] = Field(
        None, description="User's preferred learning style"
    )
    prior_experience: Optional[List[str]] = Field(
        None, description="User's prior experience"
    )
    goals: Optional[List[str]] = Field(None, description="User's learning goals")
    constraints: Optional[List[str]] = Field(
        None, description="User's constraints"
    )
    motivation: Optional[str] = Field(
        None, description="User's motivation for learning"
    )

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

# Create prompter agent
prompter_agent = Agent(
    model,
    system_prompt=system_prompt,
    deps_type=PrompterDependencies,
    retries=2
)

# @prompter_agent.tool
# async def start_conversation(ctx: RunContext[PrompterDependencies]) -> str:
#     """Start the conversation with the user."""
#     initial_prompt = ctx.deps.initial_prompt
#     return await prompter_agent.run(
#         f"Start a conversation with the user based on this initial prompt: {initial_prompt}"
#     )

# @prompter_agent.tool
# async def process_response(ctx: RunContext[PrompterDependencies], user_response: str) -> str:
#     """Process the user's response and ask the next question."""
#     ctx.deps.conversation_history.append({"role": "user", "content": user_response})
#     return await ctx.agent.run(
#         f"Based on this conversation history: {ctx.deps.conversation_history}, ask the next question to gather more information."
#     )

# @prompter_agent.tool
# async def build_profile(ctx: RunContext[PrompterDependencies]) -> UserProfile:
#     """Build the user profile from the collected information."""
#     profile_data = await ctx.agent.run(
#         f"Based on this conversation history: {ctx.deps.conversation_history}, create a comprehensive user profile."
#     )
#     return UserProfile(**profile_data)

# @prompter_agent.tool
# async def is_profile_complete(ctx: RunContext[PrompterDependencies]) -> bool:
#     """Check if the profile is complete."""
#     return await ctx.agent.run(
#         f"Based on this profile: {ctx.deps.conversation_history}, "
#         "is the profile complete? Return only 'true' or 'false'."
#     )

# Example usage
# async def main():
#     deps = PrompterDependencies(
#         initial_prompt="I want to learn web development"
#     )
    
#     # Start conversation
#     first_question = await prompter_agent.run(
#         "start_conversation", deps=deps
#     )
#     print(f"Assistant: {first_question}")
    
#     # Process responses
#     sample_responses = [
#         "I'm a complete beginner",
#         "I'm interested in frontend development",
#         "I can dedicate 10 hours per week"
#     ]
    
#     for response in sample_responses:
#         print(f"\nUser: {response}")
#         next_question = await prompter_agent.run(
#             "process_response", deps=deps, user_response=response
#         )
#         print(f"Assistant: {next_question}")
        
#         if await prompter_agent.run("is_profile_complete", deps=deps):
#             profile = await prompter_agent.run("build_profile", deps=deps)
#             print("\nProfile complete!")
#             print(profile)
#             break

# if __name__ == "__main__":
#     import asyncio
#     asyncio.run(main())

        
# Function to process user responses and update profile
async def build_user_profile():
    # Initialize the user profile
    user_profile = UserProfile()

    # Start the conversation
    print("Assistant: What would you like to learn or become?")
    user_input = input("User: ")
    messages = []

    # Conversation loop
    while True:
        # Get the agent's response
        response= await prompter_agent.run_sync(
            user_input,
            deps=PrompterDependencies,
            message_history=messages
        )

        # Update the user profile with new data
        for field, value in response.profile_updates.items():
            if hasattr(user_profile, field):
                if isinstance(getattr(user_profile, field), list):
                    getattr(user_profile, field).append(value)
                else:
                    setattr(user_profile, field, value)

        # Print the next question
        print(f"Assistant: {response.next_question}")
        user_input = input("User: ")

        # Append the user's response to the conversation history
        messages.append({"role": "assistant", "content": response.next_question})
        messages.append({"role": "user", "content": user_input})

        # Check if the conversation should end
        if "complete" in user_input.lower():
            break

    # Return the finalized user profile
    return user_profile

# Function to create a super prompt for search APIs
def create_super_prompt(profile: UserProfile) -> str:
    super_prompt = f"""
    Find learning resources for a user with the following profile:
    - Skill Level: {profile.skill_level}
    - Interests: {', '.join(profile.interests)}
    - Time Commitment: {profile.time_commitment}
    - Location/Context: {profile.geographical_context}
    - Learning Style: {profile.learning_style}
    - Prior Experience: {profile.prior_experience}
    - Goals: {', '.join([f"{key}: {value}" for key, value in profile.goals.items()])}
    - Constraints: {', '.join(profile.constraints)}
    - Motivation: {profile.motivation}

    Return resources that are tailored to the user's unique needs and preferences.
    """
    return super_prompt

# Main function
async def main():
    # Build the user profile
    user_profile = await build_user_profile()
    print("\nUser Profile:")
    print(user_profile.model_dump())

    # Create a super prompt for search APIs
    super_prompt = create_super_prompt(user_profile)
    print("\nSuper Prompt for Search APIs:")
    print(super_prompt)

# Run the script
if __name__ == "__main__":
    asyncio.run(main())
        