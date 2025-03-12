import streamlit as st
import json
from datetime import datetime
import os

def save_to_json(human_input, ai_output):
    data = {
        "messages": [
            {"role": "human", "content": human_input},
            {"role": "assistant", "content": ai_output}
        ]
    }
    
    filename = f"chat_data_{datetime.now().strftime('%Y%m%d')}.jsonl"
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    return filename

def read_json_file(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data

st.title("ChatTemplate Input/Output App")

# Initialize session state
if 'human_input' not in st.session_state:
    st.session_state.human_input = ""
if 'ai_output' not in st.session_state:
    st.session_state.ai_output = ""
if 'saved_message' not in st.session_state:
    st.session_state.saved_message = ""

# Function to update inputs
def update_inputs():
    st.session_state.human_input = human_input
    st.session_state.ai_output = ai_output

# Create input fields
human_input = st.text_area("Human Input", value=st.session_state.human_input, height=200, on_change=update_inputs)
ai_output = st.text_area("AI Output", value=st.session_state.ai_output, height=200, on_change=update_inputs)

if st.button("Save"):
    if human_input and ai_output:
        filename = save_to_json(human_input, ai_output)
        st.session_state.saved_message = f"Data saved to {filename}"
        st.session_state.human_input = ""
        st.session_state.ai_output = ""
        st.rerun()
    else:
        st.warning("Please enter both input and output before saving.")

# Display saved message
if st.session_state.saved_message:
    st.success(st.session_state.saved_message)
    st.session_state.saved_message = ""

st.header("Saved Data")
json_files = [f for f in os.listdir('.') if f.endswith('.json')]
selected_file = st.selectbox("Select a file to view", json_files)

if selected_file:
    data = read_json_file(selected_file)
    st.json(data)