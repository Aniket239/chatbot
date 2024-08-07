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
#extractig data from content.json
persona = json.dumps(data['persona'], indent=2)
goal = json.dumps(data['goal'], indent=2)
project_info = json.dumps(data['project info'], indent=2)
instructions = json.dumps(data['instructions'])
restrictions = json.dumps(data['restrictions'])
jain_group_info = json.dumps(data['Jain Group Info'], indent=2)

#creating individual context for sending in the message as system and user role
system_context= f"\n\npersona: {persona}\n\ngoal: {goal}\n\nProject Info: {project_info}\n\nJain Group Info: {jain_group_info}"
user_context = f"\n\ninstructions: {instructions}\n\nRestrictions: {restrictions}" + " With all these information try to negotiate with the customer to make them provide their flat requirement specifications and to try to negotiate with the customer to change their budget if it is a little bit low and then book a site visit anyway and you should be giving some great rebuttals if thee customer disaggres"

# Session management
sessions = {}

#saving the previous conversation in the session.json file
def save_sessions():
    with open("sessions.json", "w") as f:
        json.dump(sessions, f, indent=4)

#extracting the previous conversation from the sesison.json file
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

#for checking the status of the customer
def check_qualification(bot_reply, current_status):
    """Determines the qualification status of the lead with special transitions for follow-ups."""
    # Convert bot_reply to lowercase and remove special characters for case-insensitive comparison
    bot_reply = re.sub(r'[^a-z0-9\s]', '', bot_reply.lower())

    # Define arrays for different response types
    qualified_responses = ["this seems to meet your preferences", "shall we book the site visit", "for a better firsthand experience", "a firsthand experience can be enlightening",
                           "would you like us to schedule a site visit for you", "witnessing it firsthand makes a difference", "a site visit would be an eyeopener", "schedule a site visit", "this seems to meet your preferences", "book a site visit"]
    site_visit_responses = ["preferred date and time for the visit", "you to confirm the visit", "thank you for showing interest in booking a site visit",
                            "please provide a date and time", "provide a date and time", "thank you for providing the date and time"]
    site_visited_responses = ["we remember your last visit",
                              "do you have any feedback or concerns from your last visit were here to help"]
    site_visited_not_booked_responses = ["were there any concerns", "prevented your decision your feedback would be insightful",
                                         "with those areas clarified", "finalizing a flat with dream gurukul"]
    flat_booked_responses = ["its wonderful you chose dream gurukul"]
    follow_up_responses = ["thank you for showing continued interest in dream gurukul",
                           "ill note it down", "when would you like us to follow up with you"]

    if current_status == "enquiry":
        # Status can be upgraded to "qualified"
        if any(response in bot_reply for response in qualified_responses):
            return "qualified"
        else:
            return current_status
    return current_status

#for sending message to the openai api and getting response
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
        sessions[phone_number] = {
            'log': conversation_history, 'status': current_status}

    # Prepare the context, current status, and history for the model
    messages = [
        {"role": "system", "content": system_context},
        {"role": "user", "content": user_context}
        ]

    # Add the previous messages to the context for the model
    for msg in conversation_history:
        role = "user" if 'User' in msg else "assistant"
        content = msg.split(": ")[1].strip()
        messages.append({"role": role, "content": content})


    # Append the new user message
    messages.append({"role": "user", "content": user_input})

    # Define the models to use
    models = ["gpt-3.5-turbo-1106","gpt-3.5-turbo-1106","gpt-3.5-turbo-1106","gpt-3.5-turbo-1106"]

    # Try to get a reply from each model in turn
    for model_name in models:
        try:
            response = openai.ChatCompletion.create(
                model=model_name,
                messages=messages,
                temperature=0.1,
                presence_penalty=0,
                top_p=0.1  
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
    # Adjust the number of messages as needed
    return f"Status: {new_status}\n\n" + ''.join(conversation_history[-12:])

#for interface
demo = gr.Interface(
    fn=CustomChatGPT,
    inputs=["text", "text"],
    outputs="text",
    title="Jain Group Bot",
)

demo.launch(share=True)
