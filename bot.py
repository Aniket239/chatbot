import json
import openai
import gradio as gr
import os
import re
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Key management and client instantiation
api_key = os.getenv('OPENAI_API_KEY')
client = openai.OpenAI(api_key=api_key)

# Load context from JSON
with open("content.json", "r") as file:
    data = json.load(file)

# Creating system and user context from loaded data
system_context = f"\n\nPersona: {json.dumps(data['persona'], indent=2)}\n\nGoal: {json.dumps(data['goal'], indent=2)}\n\nProject Info: {json.dumps(data['project info'], indent=2)}\n\nJain Group Info: {json.dumps(data['Jain Group Info'], indent=2)}"
user_context = f"\n\nInstructions: {json.dumps(data['instructions'])}\n\nRestrictions: {json.dumps(data['restrictions'])}"

# Session management
sessions = {}

def load_sessions():
    global sessions
    try:
        with open("sessions.json", "r") as f:
            sessions = json.load(f)
    except Exception:
        sessions = {}

def save_sessions():
    with open("sessions.json", "w") as f:
        json.dump(sessions, f, indent=4)

load_sessions()

def handle_chat(phone_number, user_input):
    if not phone_number:
        return "ERROR: Phone Number cannot be blank!!!"

    if phone_number not in sessions:
        sessions[phone_number] = {'log': [], 'status': 'enquiry'}

    session = sessions[phone_number]
    messages = [{"role": "system", "content": system_context}, {"role": "user", "content": user_context}]
    messages += [{"role": "user" if "User" in msg else "assistant", "content": msg.split(": ")[1]} for msg in session['log']]
    messages.append({"role": "user", "content": user_input})
    print(messages)
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.1
        )
        # Accessing response correctly
        bot_reply = response.choices[0].message.content
        session['log'] += [f"User: {user_input}", f"Bot: {bot_reply}"]
    except Exception as e:
        return f"Error during API call: {str(e)}"

    save_sessions()
    return "\n".join(session['log'][-12:])  # You might adjust the slice as per your needs

# Gradio interface
demo = gr.Interface(fn=handle_chat, inputs=["text", "text"], outputs="text", title="Jain Group Bot")
demo.launch(share=True)
