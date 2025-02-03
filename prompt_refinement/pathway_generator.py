from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from prompter import UserProfile
from dataclasses import dataclass
from pydantic_ai import Agent, RunContext, ModelRetry
from pydantic_ai.models.openai import OpenAIModel
from pathlib import Path
from dotenv import load_dotenv
import os
import asyncio
import time
from functools import wraps

'''
#! TODO: 3/2/25

ok next steps: have to experiment with different user profile types, and see how long it takes for different AI models to respond as well as the quality of the responses.

'''

# System prompt for the curriculum builder LLM
CURRICULUM_BUILDER_SYSTEM_PROMPT = """
You are an expert curriculum designer and learning path architect. Your role is to create detailed, 
well-structured learning roadmaps that break down complex subjects into manageable, iterative learning paths.

Follow these principles when creating learning paths:
1. Progressive Complexity: Arrange topics from foundational to advanced
2. Prerequisite Chaining: Clearly identify dependencies between topics
3. Practical Application: Include hands-on projects and practical exercises
4. Time-Aware Planning: Provide realistic time estimates for each component
5. Resource Diversity: Consider different learning styles and resource types
6. Clear Objectives: Define clear learning outcomes for each section
7. Modular Structure: Create self-contained modules that build upon each other

When creating the learning path:
- Start with fundamental concepts that are prerequisites for more advanced topics
- Break down complex topics into smaller, digestible sub-topics
- Include practical exercises and projects to reinforce learning
- Consider the learner's background and time constraints
- Provide clear context for why each topic is important
- Include difficulty ratings to help set expectations
- Add detailed descriptions that explain the value and application of each topic

You must return your response in a structured JSON format that matches the specified schema.
"""


class ResourceItem(BaseModel):
    type: str = Field(None, description="Type of resource (video, article, course, book, etc.)")
    title: str = Field(None, description="Title of the resource")
    url: str = Field(None, description="URL of the resource")
    description: str = Field(None, description="Brief description of the resource")
    estimated_time: str = Field(None, description="Estimated time to complete this resource")

class LearningNode(BaseModel):
    title: str = Field(
        None, 
        description="Clear, concise title of the learning topic"
    )
    description: str = Field(
        None, 
        description="Detailed description explaining what this topic covers and why it's important"
    )
    learning_objectives: List[str] = Field(
        None, 
        description="Specific, measurable outcomes that will be achieved"
    )
    difficulty: str = Field(
        None, 
        description="Difficulty level (beginner, intermediate, advanced)"
    )
    prerequisites: List[str] = Field(
        default_factory=list, 
        description="Skills or knowledge required before starting this topic"
    )
    estimated_duration: str = Field(
        None, 
        description="Estimated time needed to complete this section"
    )
    key_concepts: List[str] = Field(
        None, 
        description="Core concepts and ideas covered in this topic"
    )
    resources: List[ResourceItem] = Field(
        default_factory=list, 
        description="Curated learning resources for this topic"
    )
    sub_nodes: List['LearningNode'] = Field(
        default_factory=list, 
        description="Sub-topics within this topic"
    )
    continuation_query: Optional[str] = Field(
        None, 
        description="Search query optimized for EXA AI to find relevant resources"
    )

class LLMResponse(BaseModel):
    learning_pathway: LearningNode

async def call_llm(prompt:str, model_type='gpt-4o-mini', system_prompt=CURRICULUM_BUILDER_SYSTEM_PROMPT) -> str:
    root_dir = Path(__file__).resolve().parent.parent
    env_path = root_dir / '.env'
    load_dotenv(env_path)
    model = OpenAIModel(model_type, api_key=os.getenv('OPENAI_API_KEY'))

    prompter_agent = Agent(
    model,
    system_prompt=system_prompt,
    result_type=LLMResponse, 
    retries=2
    )

    try:
        response = await prompter_agent.run(prompt)

        if response.data:
            print(f"RESPONSE DATA: {response.data.learning_pathway}")

            return response.data.learning_pathway.model_dump()

    except Exception as e:
        raise Exception(f"Error occurred while call_llm: {str(e)}")
        
def parse_llm_response_to_learning_node(llm_response: str) -> LearningNode:
    """
    Parse the LLM's JSON response into a LearningNode structure.
    """
    try:
        # Parse JSON response and validate against the schema
        if isinstance(llm_response, str):
            import json
            response_dict = json.loads(llm_response)
        else:
            response_dict = llm_response
            
        # Create the LearningNode structure
        learning_node = LearningNode.model_validate(response_dict)
        
        return learning_node
        
    except Exception as e:
        raise ValueError(f"Failed to parse LLM response: {str(e)}")
    

def async_measure_time(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = await func(*args, **kwargs)
        end_time = time.perf_counter()
        print(f"{func.__name__} executed in {end_time - start_time:0.4f} seconds")
        return result
    return wrapper

@async_measure_time
async def create_learning_pathway(profile_dict: dict) -> LearningNode:
    '''
    main function to create complete learning pathway tree.
    Returns a fully structured learning pathway with all nodes and continuation queries, ready for resource enrichment next (using that continuation query to make calls to EXA AI)
    '''

    llm_prompt = f"""
    Create a detailed learning roadmap for the following user profile:
    
    User Profile:
    - Skill Level: {profile_dict.get('skill_level')}
    - Interests: {', '.join(profile_dict.get('interests', []))}
    - Time Commitment: {profile_dict.get('time_commitment')}
    - Learning Style: {profile_dict.get('learning_style')}
    - Prior Experience: {', '.join(profile_dict.get('prior_experience', []))}
    - Goals: {', '.join(profile_dict.get('goals', []))}
    - Constraints: {', '.join(profile_dict.get('constraints', []))}
    - Motivation: {profile_dict.get('motivation')}
    
    Each learning node must specify:
    1. Title: Core topic or skill being addressed in this learning unit
    2. Description: Overview and relevance of this topic in the learning journey
    3. Learning Objectives: Specific outcomes and skills to be gained
    4. Difficulty: Relative complexity and required expertise level
    5. Prerequisites: Required knowledge or skills before starting
    6. Estimated Duration: Expected time investment for completion
    7. Key Concepts: Fundamental ideas and principles to be mastered
    8. Resources: Collection of learning materials and references (populated later)
    9. Subnodes: Breakdown of subtopics and component skills. This is a list of other LearningNode objects
    10. Continuation Query: Search prompt for finding relevant learning materials
    
        For each node in the learning pathway, create a personalized Continuation Query that:
        1. References the user's skill level and learning style
        2. Considers their time commitment
        3. Builds upon their prior experience
        4. Aligns with their specific goals
        5. Takes into account where this node fits in the overall learning journey"

        Format each continuation_query as follows:
        "Given a {profile_dict.get('skill_level')} learner with {profile_dict.get('learning_style')} learning style, 
        who has {profile_dict.get('time_commitment')} available and background in {', '.join(profile_dict.get('prior_experience', []))}, 
        looking to {', '.join(profile_dict.get('goals', []))}: 
        
        Currently focusing on [node topic] which covers [key concepts].
        This is a [difficulty] level topic that builds upon [prerequisites].
        
        If you're interested in mastering this topic through {profile_dict.get('learning_style')} learning, 
        here are some carefully selected resources that match your background and learning style: "

        Remember to adjust the difficulty and complexity of resources in the continuation queries based on:
        1. Where this node appears in the learning sequence
        2. The user's current skill level
        3. Their prior experience with prerequisites
        4. The time they have available to dedicate to learning
    
    IMPORTANT STRUCTURAL REQUIREMENTS:
    1. The learning pathway MUST have AT LEAST 3 hierarchical levels:
        Level 1 (Root): The main learning journey
        Level 2: Major topic areas or modules (at least 3)
        Level 3: Specific learning units or lessons (at least 2-3 per Level 2 module)

    Example structure:
    Level 1 (Root): "Machine Learning Engineering"
    ├── Level 2: "Mathematics Foundations"
    │   ├── Level 3: "Linear Algebra Essentials"
    │   ├── Level 3: "Calculus Fundamentals"
    │   └── Level 3: "Probability & Statistics"
    ├── Level 2: "Programming Fundamentals"
    │   ├── Level 3: "Python Programming"
    │   ├── Level 3: "Data Structures"
    │   └── Level 3: "Algorithms"
    └── Level 2: "Machine Learning Basics"
        ├── Level 3: "Supervised Learning"
        ├── Level 3: "Unsupervised Learning"
        └── Level 3: "Model Evaluation"

    For each level:
    - Level 1: Provides the overall learning journey structure and high-level roadmap
    - Level 2: Breaks down into major skill areas or knowledge domains (minimum 3 modules)
    - Level 3: Details specific learning units with concrete, actionable content (minimum 2-3 per Level 2 module)

    Progression Guidelines:
    1. Each level should build upon the previous one
    2. Level 2 modules should be ordered by prerequisite dependencies
    3. Level 3 units should represent 1-2 weeks of learning each
    4. Consider the user's time commitment of {profile_dict.get('time_commitment')} when structuring units

    For each node at every level, provide:
    [... previous node requirements section ...]

    Each Level 2 module MUST include:
    - Clear prerequisites from other Level 2 modules
    - At least 2-3 Level 3 sub-nodes
    - Estimated duration for the entire module
    - Learning objectives that tie to the overall goals

    Each Level 3 unit MUST include:
    - Specific, hands-on learning activities
    - Concrete deliverables or projects
    - Direct connection to user's goals: {', '.join(profile_dict.get('goals', []))}
    - Detailed key concepts and skills

    Return the learning pathway as a JSON object that strictly follows this schema:
    {{
        "title": "Main Topic Title",
        "description": "Detailed description",
        "learning_objectives": ["objective1", "objective2"],
        "difficulty": "beginner|intermediate|advanced",
        "prerequisites": ["prerequisite1", "prerequisite2"],
        "estimated_duration": "X weeks/months",
        "key_concepts": ["concept1", "concept2"],
        "resources": [],
        "sub_nodes": [
            {{
                // Same structure as parent node
            }}
        ],
        "continuation_query": null
    }}

    VALIDATION CHECKLIST:
    - Root node (Level 1) represents the complete learning journey
    - At least 3 major modules (Level 2) are defined
    - Each Level 2 module has at least 2-3 specific learning units (Level 3)
    - Clear progression and prerequisites between modules
    - All nodes must have properly formatted continuation queries
    - Total estimated duration matches user's time commitment
    - Learning objectives align with user's goals at each level

    Before returning the response, verify that:
    1. All three levels are properly populated
    2. Each level has the minimum required number of nodes
    3. Prerequisites form a logical learning sequence
    4. Time estimates are realistic given the user's commitment of {profile_dict.get('time_commitment')}

    IMPORTANT: be sure to think through the iterative steps in this learning path and think of sub-nodes involved in the step-by-step approach to learning in this pathway. Populate these as sub_nodes following the same structure as the parent node.

    """

    try: 
        # Call your LLM service here with the prompt
        # This is a placeholder - replace with your actual LLM call
        llm_response = await call_llm(llm_prompt)
        
        # Parse the JSON response into the LearningNode structure
        # You might need to add error handling here
        learning_pathway = parse_llm_response_to_learning_node(llm_response)

        return learning_pathway
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise Exception(f"Failed to generate learning pathway: {e}")
    
async def main():
    # Sample user profile
    profile = {
        "life_path": "Machine Learning Engineer",
        "skill_level": "beginner",
        "interests": ["AI", "Python", "Mathematics"],
        "time_commitment": "10 hours per week",
        "learning_style": "hands-on",
        "prior_experience": ["Basic Python", "Statistics"],
        "goals": ["Build ML models", "Understand deep learning"]
    }
    
    try:
        # Create the learning pathway
        learning_pathway = await create_learning_pathway(profile)
        
        # Print the structure (for verification)
        print_node_structure(learning_pathway)
        
        # Example of how to use the continuation query with exa AI
        # for node in traverse_nodes(learning_pathway):
        #     if node.continuation_query:
        #         try:
        #             results = exa.search(
        #                 node.continuation_query,
        #                 type="neural",
        #                 use_autoprompt=False
        #             )
        #             # Store results for later use
        #             node.resources = [
        #                 ResourceItem(
        #                     type=determine_resource_type(result),
        #                     title=result.get("title", ""),
        #                     url=result.get("url", ""),
        #                     description=result.get("text", "")[:200],
        #                     estimated_time="varies"  # You might want to estimate this based on content type
        #                 )
        #                 for result in results
        #             ]
        #         except Exception as e:
        #             print(f"Error searching resources for {node.title}: {e}")
        
        return learning_pathway
        
    except Exception as e:
        print(f"Error creating learning pathway: {e}")
        import traceback
        traceback.print_exc()
    
def print_node_structure(node: LearningNode, level: int = 0):
    if not node:
        print("Empty node received")
        return
        
    indent = "  " * level
    print(f"{indent}📚 {node.title or 'Untitled'}")
    print(f"{indent}Description: {node.description or 'No description'}")
    print(f"{indent}Difficulty: {node.difficulty or 'Not specified'}")
    print(f"{indent}Duration: {node.estimated_duration or 'Not specified'}")
    print(f"{indent}Continuation Query: {node.continuation_query or 'Not specified'}")
    
    print(f"{indent}Learning Objectives:")
    for objective in (node.learning_objectives or []):
        print(f"{indent}- {objective}")
        
    print(f"{indent}Key Concepts:")
    for concept in (node.key_concepts or []):
        print(f"{indent}- {concept}")
        
    if node.resources:
        print(f"{indent}Resources:")
        for resource in node.resources:
            print(f"{indent}  - [{resource.type or 'unknown'}] {resource.title or 'Untitled'}")
    print()
    
    for sub_node in (node.sub_nodes or []):
        print_node_structure(sub_node, level + 1)

if __name__ == "__main__":
    import asyncio
    
    # Create and run the event loop
    loop = asyncio.get_event_loop()
    learning_pathway = loop.run_until_complete(main())
    
    # Optional: Close the loop
    loop.close()