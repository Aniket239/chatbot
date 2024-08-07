import json
import openai
import gradio as gr
import os
from dotenv import load_dotenv

# API Key management
load_dotenv()
openai.api_key = os.environ.get('OPENAI_API_KEY')

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
        {"role": "system", "content": "You are a salesman of Jain Group, your purpose is to talk with the customers and understand their needs, then book a site visit if they haven't, if they have visited the site then try to sell a flat "},
        {"role": "assistant", "content": "Welcome to Dream Gurukul, a unique residential project where homes are crafted to foster the next generation of superstars. As I can see you have shown interest in our Dream Gurukul project. Tell me about your preferences and budget"}
    ]

    for idx, msg in enumerate(conversation_history):
        role = "user" if idx % 2 == 0 else "assistant"
        content = msg.split(": ")[1].strip()
        messages.append({"role": role, "content": content})

    # Add the new user input to the messages
    messages.append({"role": "user", "content": user_input})

    # List of models in the order you want to use
    models = ["ft:gpt-3.5-turbo-0613:personal::8DQhMpPn"]
    ChatGPT_reply = ""

    for model_name in models:
        try:
            response = openai.ChatCompletion.create(
                model=model_name,
                messages=messages
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


demo = gr.Interface(
    fn=CustomChatGPT,
    inputs=["text", "text"],
    outputs="text",
    title="Jain Group Bot",
    input_labels=["Phone Number", "Ask our Broker"],
)

demo.launch(share=True)