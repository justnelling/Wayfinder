'''
Handles all API routing for backend + the chat functionality
'''

# src/main.py
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
import json
from src.prompt_refinement.prompter import (
    UserProfile, ChatMessage, AgentDependencies, 
    prompter_agent, check_profile_completion
)
from src.prompt_refinement.pathway_generator import generate_complete_pathway

app = FastAPI()

class ChatState:
    def __init__(self):
        self.profile = UserProfile()
        self.conversation_history = []
        self.missing_fields_deps = []

@app.websocket("/chat")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    chat_state = ChatState()
    retry_count = 0
    last_completion_percentage = 0
    
    try:
        await websocket.send_json({
            "type": "question",
            "content": "Welcome to your life path! What would you like to become?\n"
        })

        while True:
            user_input = await websocket.receive_text()
            
            chat_state.conversation_history.append(
                ChatMessage(role="user", content=user_input)
            )

            deps = AgentDependencies(
                user_profile=chat_state.profile,
                conversation_history=chat_state.conversation_history,
                missing_fields=chat_state.missing_fields_deps
            )
            
            try:
                response1 = await prompter_agent.run(user_input, deps=deps)

                if response1.data:
                    chat_state.profile = response1.data.profile
                    
                    await websocket.send_json({
                        "type": "profile_update",
                        "profile": chat_state.profile.model_dump()
                    })

                    # Get completion status
                    completion_status = chat_state.profile.is_complete()
                    current_completion = completion_status['completion_percentage']
                    
                    # Check if completion percentage hasn't improved
                    if current_completion == last_completion_percentage:
                        retry_count += 1
                        print(f"No improvement in completion ({current_completion}%), retry count: {retry_count}")
                    else:
                        retry_count = 0
                        print(f"Profile improved to {current_completion}%, reset retry count")
                    
                    last_completion_percentage = current_completion

                    # Generate pathway if:
                    # 1. Profile is 100% complete OR
                    # 2. We've retried twice with at least 80% completion
                    if completion_status['is_complete'] or (retry_count >= 2 and current_completion >= 80):
                        print(f"Generating pathway (Completion: {current_completion}%, Retries: {retry_count})")
                        learning_pathway = await generate_complete_pathway(
                            chat_state.profile.model_dump()
                        )
                        
                        await websocket.send_json({
                            "type": "complete",
                            "profile": chat_state.profile.model_dump(),
                            "learning_pathway": learning_pathway
                        })
                        return

                    # Continue with follow-up questions
                    chat_state.missing_fields_deps = (
                        completion_status['missing_critical'] + 
                        completion_status['missing_optional']
                    )
                    
                    deps = AgentDependencies(
                        user_profile=chat_state.profile,
                        conversation_history=chat_state.conversation_history,
                        missing_fields=chat_state.missing_fields_deps
                    )

                    response2 = await prompter_agent.run(user_input, deps=deps)
                    
                    await websocket.send_json({
                        "type": "question",
                        "content": response2.data.follow_up_question
                    })
                    
                    chat_state.conversation_history.append(
                        ChatMessage(
                            role="assistant",
                            content=response2.data.follow_up_question
                        )
                    )
                    
            except Exception as e:
                print(f"Error: {str(e)}")
                await websocket.send_json({
                    "type": "error",
                    "content": str(e)
                })
                return
                
    except WebSocketDisconnect:
        print("Client disconnected")

# Optional: Separate endpoint for pathway generation
@app.post("/generate-pathway")
async def generate_pathway_endpoint(profile: dict):
    try:
        learning_pathway = await generate_complete_pathway(profile)
        return {"learning_pathway": learning_pathway}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

