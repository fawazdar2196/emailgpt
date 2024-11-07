import imaplib
import email
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import openai
import threading
import time
import os
import streamlit as st

# Email and OpenAI configurations
IMAP_SERVER = 'imap.gmail.com'
IMAP_PORT = 993
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
TARGET_EMAIL_ADDRESS = 'dtools.incorporation@gmail.com'  # Your email address
EMAIL_PASSWORD = 'mnkonzasbyuwocgv'  # Your app password
OPENAI_API_KEY = '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'  # Your OpenAI API key

# Initialize Streamlit app
st.title("My Custom GPT for Roster Processing")

# Initialize chat history in session state
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

# Function to add messages to chat history
def add_to_chat(role, message):
    st.session_state.chat_history.append({"role": role, "message": message})

# Function to check emails
def check_emails():
    """Continuously check for new emails."""
    while True:
        try:
            mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
            mail.login(TARGET_EMAIL_ADDRESS, EMAIL_PASSWORD)
            mail.select('inbox')

            # Search for unseen emails
            status, messages = mail.search(None, '(UNSEEN)')
            email_ids = messages[0].split()

            if email_ids:
                for e_id in email_ids:
                    status, msg_data = mail.fetch(e_id, '(RFC822)')
                    for response_part in msg_data:
                        if isinstance(response_part, tuple):
                            msg = email.message_from_bytes(response_part[1])
                            sender_email = email.utils.parseaddr(msg['From'])[1]
                            email_body = extract_email_body(msg)

                            # Log the email processing
                            add_to_chat("User", f"Email from: {sender_email}\n{email_body}")

                            # Process the email and get the ICS content
                            ics_content = process_email(email_body)

                            if ics_content:
                                # Send ICS file back to the sender
                                send_email(sender_email, ics_content)
                                add_to_chat("Assistant", "ICS content generated and sent back.")
                            else:
                                add_to_chat("Assistant", "Failed to generate ICS content.")

                            # Mark the email as read
                            mail.store(e_id, '+FLAGS', '\\Seen')

            mail.logout()
            time.sleep(60)  # Wait before checking again
        except Exception as e:
            print(f'Error checking emails: {e}')
            time.sleep(60)  # Delay before retrying

def extract_email_body(msg):
    """Extract the body of the email."""
    email_body = ''
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            if content_type == 'text/plain':
                email_body = part.get_payload(decode=True).decode()
                break
    else:
        email_body = msg.get_payload(decode=True).decode()
    return email_body

def process_email(email_body):
    """Process the email body and generate ICS content using OpenAI API."""
    openai.api_key = OPENAI_API_KEY
    system_prompt = """
You are an assistant that processes rosters and converts them into Apple iOS iCalendar (.ics) format according to specific rules.
"""

    user_message = f"""
Instructions:

1. The Date is the current Year (2024) and current Month (Nov).
2. If the Date is beyond the date of this month, automatically consider it as next month.
3. Create an event for the line with a flight number (Example NX001). The start time is the first 4 digits after the departure airport, the end time is the second 4 digits after the departure airport, then end with the destination airport.
4. The event time uses the local time (Example MFM uses UTC+8, KIX uses UTC+9, etc.).
5. The event shows from which airport to which airport as the title (MFM > NRT).
6. In case of a flight event, there are 2 times in a row; the first time is the departure airport local time, the second time is the arrival airport local time.
7. Complete the above steps then convert all the events into Apple iOS iCalendar format.

Roster:

{email_body}

Export the ics text for me; I will manually copy it to my ICS file.
"""

    try:
        # Call OpenAI for chat completions
        response = openai.ChatCompletion.create(
            model='gpt-4',
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            max_tokens=2000,
            temperature=0
        )

        ics_content = response.choices[0].message.content.strip()
        return ics_content
    except Exception as e:
        print(f"Error communicating with OpenAI: {e}")
        return None

def send_email(recipient_email, ics_content):
    """Send the generated ICS file back to the sender."""
    msg = MIMEMultipart()
    msg['From'] = TARGET_EMAIL_ADDRESS
    msg['To'] = recipient_email
    msg['Subject'] = 'Your Roster ICS File'

    body = 'Please find attached your roster in ICS format.'
    msg.attach(MIMEText(body, 'plain'))

    # Create the ICS file content
    filename = 'roster.ics'
    with open(filename, 'w') as f:
        f.write(ics_content)

    # Attach the ICS file
    with open(filename, 'rb') as attachment:
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(attachment.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f'attachment; filename={filename}')
        msg.attach(part)

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(TARGET_EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.sendmail(msg['From'], [msg['To']], msg.as_string())

# Start email checking in a separate thread
email_thread = threading.Thread(target=check_emails)
email_thread.daemon = True  # Allow thread to exit when main program exits
email_thread.start()

# Display chat history
if st.session_state.chat_history:
    for chat in st.session_state.chat_history:
        st.markdown(f"**{chat['role']}**: {chat['message']}")

# The email checking will keep running in the background
