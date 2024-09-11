from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Dict
import autogen
from autogen import ConversableAgent
import requests
import re
import ast

app = FastAPI()

api_key = "" #add the api key here
# Mount the static directory to serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize Jinja2 templates
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "message": ""})

class ChatRequest(BaseModel):
    messages: List[str]  # List of chat messages

class ChatAnalysisResponse(BaseModel):
    old_date: str  # Previous meeting date
    old_time: str  # Previous meeting time
    new_date: str  # New meeting date
    new_time: str  # New meeting time
    mod_new_date : str
    is_reschedule: bool  # True if rescheduling, False if new meeting
    agreed : bool # True if agreed else false

# Define your function here or import it if it's in another module
def trigger_meeting_creation_ajax(sender, application_id,date_display,date,time):
    url = 'https://greatdoc1.wpcomstaging.com/?wjbp-ajax=wp_job_board_pro_ajax_create_meeting'

    data = {
        'wjbp-ajax': 'wp_job_board_pro_ajax_create_meeting',
        'date_display': date_display,
        'date': date,
        'time': time,
        'time_duration': '30',
        'message': 'hi',
        'nonce': 'PLACE_NONCE_HERE',  # Replace with the actual nonce value
        '_wp_http_referer': '/applicants-jobs/',
        'action': 'wp_job_board_pro_ajax_create_meeting',
        'application_id': application_id,
        'user_id': sender
    }
    
    try:
        response = requests.post(url, data=data, timeout=45, verify=False)  # Set verify=True in production
        
        if response.status_code == 200:
            response_data = response.json()
            if response_data.get('status'):
                print("status",response_data.get('msg'))
            else:
                print("failure",response_data.get('msg'))
        else:
            print("failure",response.status_code)
    except requests.RequestException as e:
        print("failure", str(e))

def trigger_meeting_reschedule_ajax(sender, meeting_id, date_display, date, time):
    # print("hello date_display",date_display)
    # print("hello date",date)
    # print("hello time",time)
    url = 'https://greatdoc1.wpcomstaging.com/?wjbp-ajax=wp_job_board_pro_ajax_reschedule_meeting'
    
    data = {
        'wjbp-ajax': 'wp_job_board_pro_ajax_reschedule_meeting',
        'date_display': date_display,
        'date': date,
        'time': time,
        'time_duration': '30',
        'message': 'hi',
        'nonce': '1b53dad9e1',  # Replace with the actual nonce value
        '_wp_http_referer': '/meetings-employer/',
        'action': 'wp_job_board_pro_ajax_reschedule_meeting',
        'meeting_id': meeting_id,
        'user_id': sender
    }
    
    try:
        response = requests.post(url, data=data, timeout=45, verify=False)  # Set verify=True in production
        
        if response.status_code == 200:
            response_data = response.json()
            if response_data.get('status'):
                print("status", response_data.get('msg'))
            else:
                print("failure", response_data.get('msg'))
        else:
            print("failure", response.status_code)
    except requests.RequestException as e:
        print("failure", str(e))

analyzer = autogen.ConversableAgent(
    name="analyzer",
    system_message="""
         You are an AI assistant designed to extract the intent and key details for interview scheduling from conversations between a hospital and a doctor. Use the latest message to determine the intent and, if applicable, reference previous messages to extract additional context.
    """,
    llm_config={"config_list": [{"model": "gpt-3.5-turbo", "api_key": api_key}]},
)
user_proxy = autogen.UserProxyAgent(
    name="user_proxy",
    human_input_mode="NEVER",
    max_consecutive_auto_reply=10,
    code_execution_config = False,
    is_termination_msg=lambda x: "[" in x.get("content", "").rstrip(),
)

@app.post("/analyze-chat", response_model=ChatAnalysisResponse)
async def analyze_chat(chat_request: ChatRequest):
    global last_response

    # Combine chat messages into a single text
    chat_text = " ".join(chat_request.messages)
    # Construct the task description for the assistant
    task_description = f"""use this chat and For each conversation:
    1. Determine the intent based on the latest message (e.g., schedule_interview, reschedule_interview, or cancel_interview).
    2. Extract relevant details, including:
    - Interview date
    - Interview time
    3. Set the status to `true` if both the doctor and the hospital have agreed to the interview details (intent, date, time), and `false` if agreement is pending or not confirmed whenever user mention new date or time both parties should accept to create or reschedule on mentioned date and time.
    4. In entire chat fetch the latest Job ID (if available ) 
    - Job ID associated date
    - Job ID associated time 

    If the intent is to reschedule or cancel, use previous messages (if applicable) to find the earlier date and time. Provide the output in a structured format.

    Strictly the Expected output:
    "["
    "intent" : "e.g., schedule_interview, reschedule_interview, or cancel_interview.",
    "interview_date": "<interview date> YYYY-MM-DD format",
    "interview_mod_date" : "<interview date in Month date,year eg: 'August 1, 2024' format >",
    "interview_time": "<interview time in hh:mm format>",
    "job_id": "<job ID, if available>",
    "job_id_date":"<job_id date if available YYYY-MM-DD format>"
    "job_id_time" :" <job_id time if available in hh:mm format>"
    "status": "true/false 
    "]"
    {chat_text}"""
    try:
        # Initiate chat between the user_proxy and the assistant agent
        user_proxy.initiate_chat(
            analyzer,
            message=task_description,
            summary_method="reflection_with_llm",  # This ensures the assistant reflects on the task
        )
        res = user_proxy.last_message()["content"]
        matches = re.search(r'\[(.*?)\]', res, re.DOTALL)
        if matches:
            # Get the last matched list string
            dict_content = matches.group(1).strip()
            dict_string = '{' + dict_content + '}'
            result = ast.literal_eval(dict_string)
            # Convert the string to a list using ast.literal_eval for safety
            if isinstance(result, dict):
                old_date = result["job_id_date"]
                old_time = result["job_id_time"]
                new_date = result["interview_date"]
                mod_new_date = result["interview_mod_date"]
                new_time = result["interview_time"]
                agreed = result["status"]
                intent=result["intent"]
                if intent=="reschedule_interview":
                    is_reschedule = True
                else:
                    is_reschedule = False

        else:
            return ChatAnalysisResponse(
            old_date="No agreement", old_time="00:00",
            new_date="No agreement", new_time="00:00",
            mod_new_date="No agreement",
            is_reschedule=False,agreed=False
            )
        # Return the last response from the callback
        return ChatAnalysisResponse(
            old_date=old_date,
            old_time=old_time,
            new_date=new_date,
            new_time=new_time,
            mod_new_date=mod_new_date,
            is_reschedule=is_reschedule,
            agreed=agreed
            )

    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return ChatAnalysisResponse(
            old_date="No agreement", old_time="00:00",
            new_date="No agreement", new_time="00:00",
            mod_new_date="No agreement",
            is_reschedule=False,agreed=False
        )
