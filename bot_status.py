import json
import openai
import gradio as gr
import os
from dotenv import load_dotenv

# API Key management
load_dotenv()
openai.api_key = os.environ.get('OPENAI_API_KEY')

# Load context from JSON
with open("content.json", "r") as file:
    data = json.load(file)

purpose = json.dumps(data['purpose'], indent=2)
project_info = json.dumps(data['project_info'], indent=2)
contact_details = json.dumps(data['contact_details'], indent=2)
instructions = ' '.join(data['instructions'])
restrictions = ' '.join(data['restrictions'])
jain_group_info = json.dumps(data['Jain Group Info'], indent=2)

context = f"purpose: {purpose}\n\nProject Info: {project_info}\n\nContact Details: {contact_details}\n\nInstructions: {instructions}\n\nRestrictions: {restrictions}\n\nJain Group Info: {jain_group_info}"
context_status= f"Project Info: {project_info}\n\nContact Details: {contact_details}\n\nJain Group Info: {jain_group_info}"
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

def determine_status(conversation_history):
    print("status")
    print(conversation_history)
    # Define the instructions based on which the status will be determined
    instructions = """Based on the conversation, determine the customer's status. And answer only the status. Use the following criteria to evaluate:
    1. Inquiry: This status applies when the customer is initiating the conversation for the first time. Look for generic questions or introductory remarks.
    2. Qualified: Check if the conversation indicates that the customer's requirements align with the project's offerings. Signs could be positive remarks about the amenities, location, pricing, or features that the project provides.
    3. Site Visit Interested: Determine this status if the customer has explicitly shown interest in booking or scheduling a site visit. Look for phrases like "I'd like to visit", "Can I see the property?", or "How do I schedule a viewing?".
    4. Site Visited: If the customer mentions having visited the site already or makes references to specific things they saw during a visit, classify them under this status.
    5. Site Visited But Not Booked: For customers who have visited but are hesitant or have concerns preventing them from booking, this status applies. Indicators can be phrases like "I visited, but...", "I liked it, but...", or "I'm still considering after the visit".
    Review the conversation and determine the most appropriate status."""
    # Prepare messages as a list of dictionaries
    messages = [{"role": "system", "content": instructions}]
    for msg in conversation_history:
        role, content = msg.split(": ", 1)
        role = "user" if role == "User" else "assistant"
        messages.append({"role": role, "content": content.strip()})
    messages.append({"role": "assistant", "content": context_status})

    # Call the OpenAI API to get the model's response
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,  
            temperature=0  # Adjust the temperature for desired randomness
        )
        print(messages)
        print(response)
        predicted_status = response['choices'][0]['message']['content']
        print(predicted_status)

        if "Inquiry" in predicted_status:
            status_name = "Inquiry"
        elif "Qualified" in predicted_status:
            status_name = "Qualified"
        elif "Site Visit Interested" in predicted_status:
            status_name = "Site Visit Interested"
        elif "Site Visit Booked" in predicted_status:
            status_name = "Site Visit Booked"
        elif "Site Visited" in predicted_status:
            status_name = "Site Visited"
        elif "Site Visited But Not Booked" in predicted_status:
            status_name = "Site Visited But Not Booked"
        else:
            status_name = "Unknown"  # Handle unrecognized status

        return status_name
    except openai.error.OpenAIError as e:
        print(f"Error with OpenAI API: {e}")
        return "Error"
    
def CustomChatGPT(phone_number, user_input):
    print("bot")
    global sessions
    if not phone_number or phone_number.strip() == "":
        return "ERROR: Phone Number cannot be blank!!!"

    if phone_number in sessions:
        conversation_history = sessions[phone_number]['log']
        current_status = sessions[phone_number]['status']
    else:
        conversation_history = []
        current_status = 'enquiry'  # Start with "enquiry" stage
        sessions[phone_number] = {'log': conversation_history, 'status': current_status}

    # Modify the "messages" list to include the role and content as dictionaries
    messages = [
        {"role": "system",
         "content": "You are a developer of Jain Group, your purpose is to talk with the customers and understand their needs, then book a site visit if they haven't, if they have visited the site then try to sell a flat "},
        {"role": "assistant", "content": context}
    ]

    for msg in conversation_history:
        role = "user" if 'User' in msg else "assistant"
        content = msg.split(": ")[1].strip()
        messages.append({"role": role, "content": content})

    messages.append({"role": "user", "content": user_input})

    models = ["gpt-3.5-turbo", "gpt-3.5-turbo-16k"]
    ChatGPT_reply = ""

    for model_name in models:
        try:
            response = openai.ChatCompletion.create(
                model=model_name,
                messages=messages,
                temperature=0
            )
            print(messages)
            print(response)
            ChatGPT_reply = response['choices'][0]['message']['content']
            conversation_history.append(f"User: {user_input}" + "\n")
            conversation_history.append(f"Bot: {ChatGPT_reply}" + "\n")
            break
        except openai.error.OpenAIError as e:
            print(f"Error with {model_name}: {e}. Trying the next model...")
            continue

    # Determine status based on the conversation using the second API call
    status = determine_status(conversation_history)  # Pass conversation_history as a parameter
    sessions[phone_number]['status'] = status

    save_sessions()

    # Return the latest conversation with the status of the customer
    return f"Status: {sessions[phone_number]['status']}\n\n" + ''.join(conversation_history[-6:])

demo = gr.Interface(
    fn=CustomChatGPT,
    inputs=["text", "text"],
    outputs="text",
    title="Jain Group Bot",
)

demo.launch(share=True)
