# app.py

import streamlit as st
import threading
import subprocess

st.title("Email Processing Dashboard")

# Function to start the email processor script
def start_email_processor():
    subprocess.Popen(['python', 'email_processor.py'])

if 'email_processor_started' not in st.session_state:
    st.session_state.email_processor_started = False

if not st.session_state.email_processor_started:
    if st.button('Start Email Processor'):
        st.session_state.email_processor_started = True
        threading.Thread(target=start_email_processor).start()
        st.success('Email processor started.')
else:
    st.info('Email processor is already running.')
