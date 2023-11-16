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

# Extract relevant data and convert to context string
purpose = json.dumps(data['purpose'], indent=2)
project_info = json.dumps(data['project_info'], indent=2)
contact_details = json.dumps(data['contact_details'], indent=2)
instructions = ' '.join(data['instructions'])
restrictions = ' '.join(data['restrictions'])
jain_group_info = json.dumps(data['Jain Group Info'], indent=2)

# Construct the bot's context with the provided details
context = f"purpose: {purpose}\n\nProject Info: {project_info}\n\nContact Details: {contact_details}\n\nInstructions: {instructions}\n\nRestrictions: {restrictions}\n\nJain Group Info: {jain_group_info}"

# Session management
sessions = {}

# Save sessions to a JSON file
def save_sessions():
    with open("sessions.json", "w") as f:
        json.dump(sessions, f, indent=4)

# Load sessions from a JSON file
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

# Load any existing sessions from file
load_sessions()

def CustomChatGPT(phone_number, user_input):
    global sessions

    # If phone_number is empty or blank
    if not phone_number or phone_number.strip() == "":
        return "ERROR: Phone Number cannot be blank!!!"
    
    # If phone_number is present, fetch the conversation history
    if phone_number in sessions:
        conversation_history = sessions[phone_number]
    else:
        conversation_history = []
        sessions[phone_number] = conversation_history

    # Extract past messages from conversation history for the API call
    messages = [
        {"role": "system", "content": "You are a developer of Jain Group, your purpose is to talk with the customers and understand their needs, then book a site visit if they haven't, if they have visited the site then try to sell a flat "},
        {"role": "system", "content": context},
        {"role": "assistant", "content": ""}
    ]

    for idx, msg in enumerate(conversation_history):
        role = "user" if idx % 2 == 0 else "assistant"
        content = msg.split(": ")[1].strip()
        messages.append({"role": role, "content": content})

    # Add the new user input to the messages
    messages.append({"role": "user", "content": user_input})

    # List of models in the order you want to use
    models = ["gpt-3.5-turbo","gpt-3.5-turbo-16k"]
    ChatGPT_reply = ""

    for model_name in models:
        try:
            response = openai.ChatCompletion.create(
                model=model_name,
                messages=messages,
                temperature=0.5
            )
            print(messages)
            print(response)
            ChatGPT_reply = response['choices'][0]['message']['content']
            conversation_history.append(f"User: {user_input}\n")
            conversation_history.append(f"Bot: {ChatGPT_reply}\n\n\n")
            break
        except openai.error.OpenAIError as e:
            print(f"Error with {model_name}: {e}. Trying next model...")
            continue

    save_sessions()
    return ''.join(conversation_history[-6:])  # Returning only the last 3 exchanges for brevity

def clear_input_js():
    return """
    function clearInput() {
        document.querySelector('input[name="Phone Number"]').value = '';
        document.querySelector('textarea[name="Ask our Broker"]').value = '';
    }
    document.querySelector('button[type="submit"]').addEventListener('click', clearInput);
    """

demo = gr.Interface(
    fn=CustomChatGPT,
    inputs=["text", "text"],
    outputs="text",
    title="Jain Group Bot",
    input_labels=["Phone Number", "User Input"],
    javascript=clear_input_js()  # Inject the custom JavaScript
)

demo.launch(share=True)