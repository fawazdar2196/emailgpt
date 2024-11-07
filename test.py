import imaplib
import email
import time
# Replace these with your actual credentials
IMAP_SERVER = 'imap.gmail.com'
IMAP_PORT = 993
TARGET_EMAIL_ADDRESS = 'dtools.incorporation@gmail.com'  # Replace with your target email address
EMAIL_PASSWORD = 'mnkonzasbyuwocgv'  # Use your email app password here

def fetch_email():
    try:
        # Connect to the email server
        mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
        mail.login(TARGET_EMAIL_ADDRESS, EMAIL_PASSWORD)
        mail.select('inbox')

        print("Checking for new emails...")

        # Search for unseen emails
        status, messages = mail.search(None, '(UNSEEN)')
        email_ids = messages[0].split()

        if not email_ids:
            print("No new emails.")
            return
        
        # Fetch the first unseen email
        e_id = email_ids[0]  # Change index to fetch different emails
        status, msg_data = mail.fetch(e_id, '(RFC822)')
        
        for response_part in msg_data:
            if isinstance(response_part, tuple):
                msg = email.message_from_bytes(response_part[1])

                # Extract the main body
                email_body = extract_email_body(msg)
                print(f'Email body extracted:\n{email_body}')  # Only the main body

        mail.logout()

    except Exception as e:
        print(f'Error fetching emails: {e}')

def extract_email_body(msg):
    email_body = ''
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            if content_type == 'text/plain':  # Get plain text
                charset = part.get_content_charset() or 'utf-8'
                email_body = part.get_payload(decode=True).decode(charset, errors='replace')
                break  # Stop after getting the first plain text part
    else:
        # If it's not multipart, just get the payload
        charset = msg.get_content_charset() or 'utf-8'
        email_body = msg.get_payload(decode=True).decode(charset, errors='replace')

    return email_body.strip()  # Remove leading/trailing whitespace

if __name__ == '__main__':
    while True:
        fetch_email()
        time.sleep(60)  # Wait for 1 minute before checking again
