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


# Replace these with your actual credentials
IMAP_SERVER = 'imap.gmail.com'
IMAP_PORT = 993
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
TARGET_EMAIL_ADDRESS = ''  # Replace with your target email address
EMAIL_PASSWORD = ''  # Use your email app password here
OPENAI_API_KEY = ''  # Replace with your OpenAI API key



def check_emails():
    while True:
        try:
            mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
            mail.login(TARGET_EMAIL_ADDRESS, EMAIL_PASSWORD)
            mail.select('inbox')

            # Search for unseen emails
            status, messages = mail.search(None, '(UNSEEN)')
            email_ids = messages[0].split()

            if not email_ids:
                print("No new emails.")
            else:
                for e_id in email_ids:
                    status, msg_data = mail.fetch(e_id, '(RFC822)')
                    for response_part in msg_data:
                        if isinstance(response_part, tuple):
                            msg = email.message_from_bytes(response_part[1])
                            
                            # Extract the sender's email
                            sender_email = email.utils.parseaddr(msg['From'])[1]
                            print(f'Processing email from: {sender_email}')

                            # Extract email body
                            email_body = extract_email_body(msg)

                            print(f'Email body extracted: {email_body}')

                            # Process the email content using OpenAI API
                            ics_content = process_email(email_body)

                            if ics_content:
                                print('ICS content generated successfully.')
                                # Save ICS content to a file and send it back to the sender
                                ics_file_path = save_ics_file(ics_content)
                                send_email(sender_email, ics_file_path)
                            else:
                                print('Failed to generate ICS content.')

                            # Mark the email as read
                            mail.store(e_id, '+FLAGS', '\\Seen')

            mail.logout()

        except Exception as e:
            print(f'Error checking emails: {e}')

        # Wait for a minute before checking again
        time.sleep(60)

def extract_email_body(msg):
    email_body = ''
    print("Full email message:")
    print(msg)  # Print the entire message to check its structure

    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get('Content-Disposition'))
            if content_type == 'text/plain' and 'attachment' not in content_disposition:
                charset = part.get_content_charset() or 'utf-8'
                email_body = part.get_payload(decode=True).decode(charset, errors='replace')
                break
    else:
        charset = msg.get_content_charset() or 'utf-8'
        email_body = msg.get_payload(decode=True).decode(charset, errors='replace')

    print(f'Email body extracted: {email_body}')  # Print the extracted body for verification
    return email_body


def process_email(email_body):
    try:
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

        # Debug: Print the user message being sent to the API
        print(f'User message to GPT-4: {user_message}')

        # Call GPT-4 for chat completions
        response = openai.ChatCompletion.create(
            model='gpt-4',
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            max_tokens=2000,
            temperature=0
        )

        ics_content = response['choices'][0]['message']['content'].strip()
        print(f'Received ICS content: {ics_content}')
        return ics_content

    except Exception as e:
        print(f'Error processing email: {e}')
        return None

def save_ics_file(ics_content):
    """Save the ICS content to a file."""
    filename = f"roster_{int(time.time())}.ics"  # Unique filename based on current timestamp
    with open(filename, 'w') as ics_file:
        ics_file.write(ics_content)
    print(f'ICS file saved: {filename}')
    return filename

def send_email(recipient_email, ics_file_path):
    """Send the generated ICS file back to the sender."""
    msg = MIMEMultipart()
    msg['From'] = TARGET_EMAIL_ADDRESS
    msg['To'] = recipient_email
    msg['Subject'] = 'Your Roster ICS File'

    body = 'Please find attached your roster in ICS format.'
    msg.attach(MIMEText(body, 'plain'))

    # Attach the ICS file
    with open(ics_file_path, 'rb') as attachment:
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(attachment.read())
        encoders.encode_base64(part)
        part.add_header(
            'Content-Disposition',
            f'attachment; filename={os.path.basename(ics_file_path)}',
        )
        msg.attach(part)

    # Send the email
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(TARGET_EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.sendmail(msg['From'], [msg['To']], msg.as_string())
        print(f'Sent ICS file to {recipient_email}')
    except Exception as e:
        print(f'Error sending email: {e}')

if __name__ == '__main__':
    email_thread = threading.Thread(target=check_emails)
    email_thread.start()
