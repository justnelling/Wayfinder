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

def generate_continuation_queries_recursive(node: LearningNode) -> LearningNode:
    """
    Recursively generate continuation queries for each node and its subnodes.
    """
    # Generate continuation query for current node
    context_text = f"""
        f"Context: {node.description}\n"
        f"Looking for learning resources about {node.title} "
        f"including tutorials, guides, and practical examples covering: "
        f"{', '.join(node.key_concepts)}. "
        f"Focus on {node.difficulty} level content."
    """

    node.continuation_query = context_text + "Given the above requirements, here are the top most relevant resources that you can use to learn more about this topic:"

    
    # Recursively generate queries for subnodes
    for sub_node in node.sub_nodes:
        generate_continuation_queries_recursive(sub_node)
    
    return node

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
    
    For each node's continuation_query, format it as follows:
    "[Topic Description and Context] If you want to learn more about [topic], here are the top practical tutorials, guides, and learning resources you should follow: "

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
    
    IMPORTANT: be sure to think through the iterative steps in this learning path and think of sub-nodes involved in the step-by-step approach to learning in this pathway. Populate these as sub_nodes following the same structure as the parent node.

    """

    try: 
        # Call your LLM service here with the prompt
        # This is a placeholder - replace with your actual LLM call
        llm_response = await call_llm(llm_prompt)
        
        # Parse the JSON response into the LearningNode structure
        # You might need to add error handling here
        learning_pathway = parse_llm_response_to_learning_node(llm_response)

        #! generate the continuation queries
        # learning_pathway = generate_continuation_queries_recursive(learning_pathway)
        
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