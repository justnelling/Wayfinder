import asyncio
import websockets
import json
from websockets.exceptions import ConnectionClosedError, ConnectionClosedOK

async def test_chat():
    try:
        async with websockets.connect('ws://localhost:8000/chat') as websocket:
            # Receive initial greeting
            response = await websocket.recv()
            parsed = json.loads(response)
            print(f"\nAssistant: {parsed['content']}")

            while True:
                try:
                    # Get user input
                    message = input("\nYou: ")
                    
                    # Send message to server
                    await websocket.send(message)
                    
                    # Keep receiving messages until we get a question or complete/error
                    while True:
                        try:
                            response = await websocket.recv()
                            parsed_response = json.loads(response)
                            
                            if parsed_response['type'] == 'profile_update':
                                print("\nProfile Updated:")
                                print(json.dumps(parsed_response['profile'], indent=2))
                                # Don't break here - wait for follow-up question
                                
                            elif parsed_response['type'] == 'question':
                                print(f"\nAssistant: {parsed_response['content']}")
                                # Now we can break and get next user input
                                break
                                
                            elif parsed_response['type'] == 'complete':
                                print("\nProfile Complete!")
                                print("\nFinal Profile:")
                                print(json.dumps(parsed_response['profile'], indent=2))
                                print("\nLearning Pathway:")
                                print(json.dumps(parsed_response['learning_pathway'], indent=2))
                                return
                                
                            elif parsed_response['type'] == 'error':
                                print(f"\nError: {parsed_response['content']}")
                                return

                            # Add a small delay to prevent flooding
                            await asyncio.sleep(0.1)
                            
                        except ConnectionClosedError:
                            print("\nConnection was closed unexpectedly.")
                            return
                        except ConnectionClosedOK:
                            print("\nConnection closed normally.")
                            return
                        except Exception as e:
                            print(f"\nError receiving message: {str(e)}")
                            return
                            
                except Exception as e:
                    print(f"\nError sending message: {str(e)}")
                    return
                    
    except Exception as e:
        print(f"\nError connecting to server: {str(e)}")
        return

if __name__ == "__main__":
    try:
        asyncio.run(test_chat())
    except KeyboardInterrupt:
        print("\nChat session terminated by user.")
    except Exception as e:
        print(f"\nUnexpected error: {str(e)}")