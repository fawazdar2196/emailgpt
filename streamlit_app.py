import streamlit as st
import subprocess
import sys
import time

st.title('Roster Email Processor')

# Initialize session state for 'process' if it doesn't exist
if 'process' not in st.session_state:
    st.session_state['process'] = None
if 'last_run' not in st.session_state:
    st.session_state['last_run'] = time.time()

def start_processor():
    """Starts the email processor as a subprocess."""
    if st.session_state['process'] is None or st.session_state['process'].poll() is not None:
        try:
            st.write('Starting email processor...')
            st.session_state['process'] = subprocess.Popen(
                [sys.executable, 'email_processor.py'],
                stdout=subprocess.PIPE,  # Capture output for debugging
                stderr=subprocess.PIPE
            )
            st.write('Email processor started.')
        except Exception as e:
            st.write(f'Failed to start email processor: {e}')

def check_processor():
    """Check the status of the email processor and restart if necessary."""
    if st.session_state['process'] is not None and st.session_state['process'].poll() is None:
        return True
    else:
        start_processor()  # Restart the process if it's not running
        return False

# Check the processor status every few seconds
if time.time() - st.session_state['last_run'] > 5:
    check_processor()
    st.session_state['last_run'] = time.time()  # Update the last run time

# Display current status of the email processor
if st.session_state['process'] is not None and st.session_state['process'].poll() is None:
    st.write('Email processor is running.')
else:
    st.write('Email processor is not running.')

# Display process output for debugging
if st.session_state['process'] is not None:
    output = st.session_state['process'].stdout.readline()
    if output:
        st.write(output.decode('utf-8').strip())
    error = st.session_state['process'].stderr.readline()
    if error:
        st.write(f"Error: {error.decode('utf-8').strip()}")
