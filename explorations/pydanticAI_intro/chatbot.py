'''
https://ai.pydantic.dev/examples/chat-app/

Simple chat app example build with FastAPI.

Demonstrates:

reusing chat history
serializing messages
streaming responses
This demonstrates storing chat history between requests and using it to give the model context for new responses.

Most of the complex logic here is between chat_app.py which streams the response to the browser, and chat_app.ts which renders messages in the browser.
'''

