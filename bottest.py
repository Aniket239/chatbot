import json
import openai
import gradio as gr
import os
import re
from dotenv import load_dotenv

# API Key management
load_dotenv()
openai.api_key = os.environ.get('OPENAI_API_KEY')

# Load context from JSON
with open("content.json", "r") as file:
    data = json.load(file)

Objective = json.dumps(data['Objective'], indent=2)
contextjson = json.dumps(data['context'], indent=2)
details = json.dumps(data['details'], indent=2)
constrains = json.dumps(data['instructions'])

context = f"Objective: {Objective}\n\ context: {contextjson}\n\nDetails: {details}\n\nconstrains: {constrains}"

# Session management
sessions = {}

def save_sessions():
    with open("sessions.json", "w") as f:
        json.dump(sessions, f, indent=4)

def load_sessions():
    global sessions
    try:
        with open("sessions.json", "r") as f:
            content = f.read()
            if content:
                sessions = json.loads(content)
            else:
                print("sessions.json file is empty. Starting fresh!")
    except (FileNotFoundError, json.JSONDecodeError):
        print("No previous session data found or invalid JSON. Starting fresh!")

load_sessions()

def check_qualification(bot_reply, current_status):
    """Determines the qualification status of the lead with special transitions for follow-ups."""
    # Convert bot_reply to lowercase and remove special characters for case-insensitive comparison
    bot_reply = re.sub(r'[^a-z0-9\s]', '', bot_reply.lower())

    # Define arrays for different response types
    qualified_responses = ["this seems to meet your preferences", "shall we book the site visit", "for a better firsthand experience", "a firsthand experience can be enlightening", "would you like us to schedule a site visit for you", "witnessing it firsthand makes a difference", "a site visit would be an eyeopener","schedule a site visit","this seems to meet your preferences","book a site visit"]
    site_visit_responses = ["preferred date and time for the visit", "you to confirm the visit", "thank you for showing interest in booking a site visit", "please provide a date and time", "provide a date and time", "thank you for providing the date and time"]
    site_visited_responses = ["we remember your last visit", "do you have any feedback or concerns from your last visit were here to help"]
    site_visited_not_booked_responses = ["were there any concerns", "prevented your decision your feedback would be insightful", "with those areas clarified", "finalizing a flat with dream gurukul"]
    flat_booked_responses = ["its wonderful you chose dream gurukul"]
    follow_up_responses = ["thank you for showing continued interest in dream gurukul", "ill note it down", "when would you like us to follow up with you"]

    if any(response in bot_reply for response in follow_up_responses):
        return "follow-up"
    
    # If not a follow-up, proceed with checking other responses
    # Ensure the status does not downgrade
    if current_status == "flat booked":
        # If a flat is booked, status should not change to any other status
        return current_status
    elif current_status == "site visited but not booked":
        # Status can be upgraded to "flat booked"
        if any(response in bot_reply for response in flat_booked_responses):
            return "flat already booked"
        else:
            return current_status
    elif current_status == "site visited":
        # Status can be upgraded to "flat booked" or "site visited but not booked"
        if any(response in bot_reply for response in flat_booked_responses):
            return "flat already booked"
        elif any(response in bot_reply for response in site_visited_not_booked_responses):
            return "site visited but not booked"
        else:
            return current_status
    elif current_status == "site visit booked":
        # Status can be upgraded to "site visited"
        if any(response in bot_reply for response in site_visited_responses):
            return "site visited"
        else:
            return current_status
    elif current_status == "qualified":
        # Status can be upgraded to "site visit booked"
        if any(response in bot_reply for response in site_visit_responses):
            return "site visit booked"
        else:
            return current_status
    elif current_status == "enquiry":
        # Status can be upgraded to "qualified"
        if any(response in bot_reply for response in qualified_responses):
            return "qualified"
        else:
            return current_status
    return current_status

def CustomChatGPT(phone_number, user_input):
    global sessions
    if not phone_number or phone_number.strip() == "":
        return "ERROR: Phone Number cannot be blank!!!"
    
    # Initialize ChatGPT_reply
    ChatGPT_reply = ""

    # Check if the session exists for the phone_number and initialize accordingly
    if phone_number in sessions:
        conversation_history = sessions[phone_number]['log']
        current_status = sessions[phone_number]['status']
    else:
        conversation_history = []
        current_status = 'enquiry'  # Set the initial status as 'enquiry'
        sessions[phone_number] = {'log': conversation_history, 'status': current_status}

    # Prepare the context, current status, and history for the model
    messages = [
        {"role": "system", "content": "You are a developer of Jain Group, your purpose is to understand the status continuously and try to move the status from enquiry to qualified, qualified to site visit booked, site visited to flat booked "},
        {"role": "assistant", "content": context},
        {"role": "system", "content": f"status is {current_status}."}  # Include the current status in the system message
    ]

    # Add the previous messages to the context for the model
    for msg in conversation_history:
        role = "user" if 'User' in msg else "assistant"
        content = msg.split(": ")[1].strip()
        messages.append({"role": role, "content": content})

    # Append the new user message
    messages.append({"role": "user", "content": user_input})

    # Define the models to use
    models = ["gpt-3.5-turbo", "gpt-3.5-turbo-16k"]

    # Try to get a reply from each model in turn
    for model_name in models:
        try:
            response = openai.ChatCompletion.create(
                model=model_name,
                messages=messages,
                temperature=0
            )
            print(response)
            print(messages)
            ChatGPT_reply = response['choices'][0]['message']['content']
            conversation_history.append(f"User: {user_input}\n")
            conversation_history.append(f"Bot: {ChatGPT_reply}\n\n")
            break
        except openai.error.OpenAIError as e:
            print(f"Error with {model_name}: {e}. Trying next model...")
            continue

    # If we don't get a reply from any model, return an error message
    if ChatGPT_reply == "":
        return "ERROR: Unable to get a response from the models."

    # Update the status based on the bot's reply using the check_qualification function
    new_status = check_qualification(ChatGPT_reply, current_status)
    sessions[phone_number]['status'] = new_status

    # Save the updated sessions
    save_sessions()

    # Return the latest conversation with the updated status of the customer
    return f"Status: {new_status}\n\n" + ''.join(conversation_history[-12:])  # Adjust the number of messages as needed

demo = gr.Interface(
    fn=CustomChatGPT,
    inputs=["text", "text"],
    outputs="text",
    title="Jain Group Bot",
)

demo.launch(share=True)