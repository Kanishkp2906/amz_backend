import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from config import EMAIL_ID, EMAIL_PASSWORD, SMTP_SERVER, SMTP_PORT

def send_email(recipient_email, subject, body):
    try:
        msg = MIMEMultipart()
        msg['from'] = EMAIL_ID
        msg['to'] = recipient_email
        msg['subject'] = subject

        msg.attach(MIMEText(body, 'html'))

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_ID, EMAIL_PASSWORD)
            server.sendmail(EMAIL_ID, recipient_email, msg.as_string())

        print(f"Email sent successfully to {recipient_email}.")

    except Exception as e:
        print(f'Error while sending the email: {e}')

if __name__ == "__main__":
    recipient_email = 'kanishkprasad6@gmail.com'
    subject = 'Final Testing the email server.'
    body = "Final Testing the smtp server to send emails form the amz_price_tracker."
    send_email(recipient_email, subject, body)
    