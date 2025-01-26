from dataclasses import dataclass, field, asdict
from typing import List, Optional
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

# llm = os.getenv('LLM_MODEL', 'deepseek/deepseek-chat')
# print(f"Using LLM model: {llm}")
# model = OpenAIModel(
#     llm,
#     base_url = 'https://openrouter.ai/api/v1',
#     api_key = os.getenv('OPEN_ROUTER_API_KEY')
# )
model = AnthropicModel('claude-3-5-sonnet-latest', api_key=os.getenv('ANTHROPIC_API_KEY'))

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


class ChatMessage(BaseModel): 
    role: str
    content: str

# Define dependencies
@dataclass
class PrompterDependencies:
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
You must return a complete UserProfile object with these fields:
{
    "skill_level": "string describing current expertise level",
    "interests": ["list of interests"],
    "time_commitment": "string describing available time",
    "geographical_context": "string describing location context",
    "learning_style": "string describing preferred learning style",
    "prior_experience": ["list of relevant experiences"],
    "goals": ["list of specific goals"],
    "constraints": ["list of limitations or constraints"],
    "motivation": "string describing core motivation"
}

Also include a follow-up question to gather missing information. Focus each question on filling gaps in the profile data.

Continue the conversation until ALL fields have meaningful content. Ask focused questions to fill gaps in the profile."""

# Create prompter agent
prompter_agent = Agent(
    model,
    system_prompt=system_prompt,
    deps_type=PrompterDependencies,
    result_type=UserProfile,
    retries=2
)

# add dynamic system prompt based on dependencies
@prompter_agent.system_prompt
async def add_previous_chat_history(ctx: RunContext[PrompterDependencies]) -> str:
    return f"Based on this conversation history: {ctx.deps.conversation_history} and the user's profile thus far: {ctx.deps.user_profile}, ask the next question to gather more information."

# add function tool for it to evaluate if the user profile is complete, else send ModelRetry
@prompter_agent.tool
async def evaluate_profile(ctx: RunContext[PrompterDependencies]) -> dict:
    """
    Evaluate the completeness of the user profile and provide feedback.
    
    Returns:
        dict: A dictionary containing the evaluation results and profile data
    """
    user_profile = ctx.deps.user_profile
    profile_data = user_profile.model_dump()
    
    # Check for empty fields
    empty_fields = []
    for field_name, field_value in profile_data.items():
        if field_value is None or (isinstance(field_value, (str, list)) and not field_value):
            empty_fields.append(field_name)
    
    evaluation_result = {
        "profile": profile_data,
        "is_complete": len(empty_fields) == 0,
        "empty_fields": empty_fields
    }
    
    if empty_fields:
        raise ModelRetry(f"Profile incomplete. Missing information for: {', '.join(empty_fields)}. Continue asking user questions to fill in the gaps.")
    
    return evaluation_result

#? try run_sync
def main():
    
    # Initialize with empty profile
    initial_profile = UserProfile(
        skill_level="",
        interests=[],
        time_commitment="",
        geographical_context="",
        learning_style="",
        prior_experience=[],
        goals=[],
        constraints=[],
        motivation=""
    )
    
    try:
        deps = PrompterDependencies(
            conversation_history=[],
            user_profile=initial_profile
        )
        
        response = prompter_agent.run_sync(
            "I want to learn web development",
            deps=deps
        )
        debug(response)
        print('-----------------------------------')
        print(response.all_messages())
        print('-----------------------------------')
        print(response.data.model_dump_json(indent=2))
        
    except Exception as e:
        print(f"Error occurred: {e}")

if __name__ == "__main__":
    main()

#? try run
# async def manage_chat(prompter_agent: Agent, initial_prompt: str) -> UserProfile:
#     dependencies = PrompterDependencies(UserProfile())
#     current_prompt = initial_prompt
    
#     # Add initial user message to conversation history
#     dependencies.conversation_history.append(
#         ChatMessage(role="user", content=initial_prompt)
#     )

#     while True:
#         # Get response from LLM
#         try:
#             response = await prompter_agent.run(
#                 current_prompt,
#                 deps=dependencies
#             )
            
#             debug(response)
#         except Exception as e:
#             raise e

# async def main():
#     initial_prompt = input("User: ")
#     try:
#         user_profile = await manage_chat(prompter_agent, initial_prompt)
#         print("\nFinal User Profile:")
#         print(user_profile.model_dump_json(indent=2))
#     except Exception as e:
#         print(f"An error occurred: {e}")

# if __name__ == "__main__":
#     # Suppress logfire warning``
#     os.environ['LOGFIRE_IGNORE_NO_CONFIG'] = '1'
    
#     asyncio.run(main())


# response.all_messages()
# print(response.data.model_dump_json(indent=2)) 

# def is_profile_complete(profile: UserProfile) -> bool:
#     """Check if all required fields in the profile are meaningfully filled."""
    
#     # Helper function to check if a string is meaningful
#     def is_meaningful(s: str) -> bool:
#         return s and len(s) > 0 and s not in ["<UNKNOWN>", "unknown", "Unknown"]
    
#     # Helper function to check if a list is meaningful
#     def is_meaningful_list(lst: List[str]) -> bool:
#         return (
#             len(lst) > 0 and 
#             not any(item.lower().startswith("unknown") for item in lst)
#         )
    
#     return all([
#         is_meaningful(profile.skill_level),
#         is_meaningful_list(profile.interests),
#         is_meaningful(profile.time_commitment),
#         is_meaningful(profile.geographical_context),
#         is_meaningful(profile.learning_style),
#         is_meaningful_list(profile.prior_experience),
#         is_meaningful_list(profile.goals),
#         is_meaningful_list(profile.constraints),
#         is_meaningful(profile.motivation)
#     ])

# async def manage_chat(prompter_agent: Agent, initial_prompt: str) -> UserProfile:
#     dependencies = PrompterDependencies()
#     current_prompt = initial_prompt
    
#     # Add initial user message to conversation history
#     dependencies.conversation_history.append(
#         ChatMessage(role="user", content=initial_prompt)
#     )

#     while True:
#         # Get response from LLM
#         result = await prompter_agent.run(
#             current_prompt,
#             deps=dependencies
#         )
        
#         debug(result)
        
#         # Get current profile state
#         current_profile = result.data
#         print("\nCurrent Profile State:")
#         print(current_profile.model_dump_json(indent=2))

#         # Let the LLM generate the next interaction
#         llm_response = await prompter_agent.run(
#             "Based on the current profile state, what specific question should we ask next to gather missing or incomplete information?",
#             deps=dependencies
#         )
        
#         # Get the LLM's question
#         next_question = llm_response.data
#         print(f"\nAI: {next_question}")
        
#         # Get user input
#         user_response = input("You: ")
        
#         # Check if user wants to end conversation
#         if user_response.lower() in ['quit', 'exit', 'done']:
#             break
        
#         # Update conversation history with the actual exchange
#         dependencies.conversation_history.extend([
#             ChatMessage(role="assistant", content=str(next_question)),
#             ChatMessage(role="user", content=user_response)
#         ])
        
#         # Update current prompt for next iteration
#         current_prompt = user_response

#     return current_profile


# async def main():
#     initial_prompt = input("User: ")
#     try:
#         user_profile = await manage_chat(prompter_agent, initial_prompt)
#         print("\nFinal User Profile:")
#         print(user_profile.model_dump_json(indent=2))
#     except Exception as e:
#         print(f"An error occurred: {e}")

# if __name__ == "__main__":
#     # Suppress logfire warning
#     os.environ['LOGFIRE_IGNORE_NO_CONFIG'] = '1'
    
#     asyncio.run(main())
    




def hidden():
    
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

        
# # Function to process user responses and update profile
# async def build_user_profile():
#     # Initialize the user profile
#     user_profile = UserProfile()

#     # Start the conversation
#     print("Assistant: What would you like to learn or become?")
#     user_input = input("User: ")
#     messages = []

#     # Conversation loop
#     while True:
#         # Get the agent's response
#         response= await prompter_agent.run(
#             user_input,
#             deps=PrompterDependencies,
#             message_history=messages
#         )

#         print(response.data)

#         # # Update the user profile with new data
#         # for field, value in response.profile_updates.items():
#         #     if hasattr(user_profile, field):
#         #         if isinstance(getattr(user_profile, field), list):
#         #             getattr(user_profile, field).append(value)
#         #         else:
#         #             setattr(user_profile, field, value)

#         # # Print the next question
#         # print(f"Assistant: {response.next_question}")
#         # user_input = input("User: ")

#         # # Append the user's response to the conversation history
#         # messages.append({"role": "assistant", "content": response.next_question})
#         # messages.append({"role": "user", "content": user_input})

#         # # Check if the conversation should end
#         # if "complete" in user_input.lower():
#         #     break

#     # Return the finalized user profile
#     return user_profile

# # Function to create a super prompt for search APIs
# def create_super_prompt(profile: UserProfile) -> str:
#     super_prompt = f"""
#     Find learning resources for a user with the following profile:
#     - Skill Level: {profile.skill_level}
#     - Interests: {', '.join(profile.interests)}
#     - Time Commitment: {profile.time_commitment}
#     - Location/Context: {profile.geographical_context}
#     - Learning Style: {profile.learning_style}
#     - Prior Experience: {profile.prior_experience}
#     - Goals: {', '.join([f"{key}: {value}" for key, value in profile.goals.items()])}
#     - Constraints: {', '.join(profile.constraints)}
#     - Motivation: {profile.motivation}

#     Return resources that are tailored to the user's unique needs and preferences.
#     """
#     return super_prompt

# # Main function
# async def main():
#     # Build the user profile
#     user_profile = await build_user_profile()
#     print("\nUser Profile:")
#     print(user_profile.model_dump())

#     # Create a super prompt for search APIs
#     super_prompt = create_super_prompt(user_profile)
#     print("\nSuper Prompt for Search APIs:")
#     print(super_prompt)

# # Run the script
# if __name__ == "__main__":
#     asyncio.run(main())
    pass