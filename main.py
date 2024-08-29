from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx

app = FastAPI()

# Mount the static directory to serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize Jinja2 templates
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "message": ""})
 

class ChatRequest(BaseModel):
    messages: list[str]  # List of chat messages

# Define the API key and URL for the Gemini API
API_KEY = "AIzaSyBSnnUpQG1Hwoahpnpjr2z9icLkbHl-DlQ"
API_URL = f"https://generativelanguage.googleapis.com/v1/models/gemini-pro:generateContent?key={API_KEY}"

@app.post("/analyze-chat")
async def analyze_chat(chat_request: ChatRequest):
    # Combine chat messages into a single text
    chat_text = " ".join(chat_request.messages)
    print("chat_text:", chat_text)
    
    # Construct the request payload for the Gemini API
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {
                       "text": f"Determine if the following conversation includes discussion of scheduling a meeting or call and whether both parties agreed on a specific date. Respond with 'true' if they agreed to meet or 'false' otherwise. Here is the conversation: {chat_text}"
                    }
                ]
            }
        ]
    }
    
    # Make a POST request to the Gemini API
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(API_URL, json=payload)
            response.raise_for_status()  # Raise an exception for HTTP errors
            
            # Extract and analyze the response from Gemini API
            response_data = response.json()
            print("response_data:", response_data)
            
            # Check if the response has the expected structure
            if 'candidates' in response_data and len(response_data['candidates']) > 0:
                candidate = response_data['candidates'][0]
                if 'content' in candidate and 'parts' in candidate['content'] and len(candidate['content']['parts']) > 0:
                    response_text = candidate['content']['parts'][0].get('text', '')
                    
                    # Determine if the response indicates an agreement
                    if 'true' in response_text.lower():
                        return True  # Return boolean true
                    elif 'false' in response_text.lower():
                        return False  # Return boolean false
            
            # Return False if the response format is unexpected
            return False
        
        except Exception as e:
            # Handle any other exceptions
            raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")

