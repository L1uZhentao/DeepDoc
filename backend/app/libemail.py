import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

class EmailSender:
    def __init__(self, recipient_email, subject, body, markdown_content, file_name, smtp_server='smtp.gmail.com', smtp_port=587):
        self.sender_email = os.getenv("SENDER_EMAIL")
        self.recipient_email = recipient_email
        self.subject = subject
        self.body = body
        self.markdown_content = markdown_content
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.message = MIMEMultipart()
        self.smtp_username = os.getenv("SMTP_USERNAME")
        self.smtp_password = os.getenv("SMTP_PASSWORD")
        self.file_name = file_name  

        if not self.sender_email:
            raise ValueError("SENDER_EMAIL environment variable must be set.")
        if not self.smtp_username or not self.smtp_password:
            raise ValueError("SMTP_USERNAME and SMTP_PASSWORD environment variables must be set.")

    def setup_email(self):
        # Set up the MIME
        self.message['From'] = self.sender_email
        self.message['To'] = self.recipient_email
        self.message['Subject'] = self.subject

        # Attach the email body text
        self.message.attach(MIMEText(self.body, 'plain'))
        filename = self.file_name.split(".")[0] if "." in self.file_name else "content"
        # Attach the markdown content
        if self.markdown_content:
            mime_base = MIMEBase('application', 'octet-stream')
            mime_base.set_payload(self.markdown_content.encode('utf-8'))
            encoders.encode_base64(mime_base)
            mime_base.add_header('Content-Disposition', f'attachment; filename="{filename}.md"')
            self.message.attach(mime_base)
        else:
            raise ValueError("Markdown content is empty.")

    def send_email(self):
        # Connect to the SMTP server and send the email
        try:
            smtp_username, smtp_password = self.smtp_username, self.smtp_password
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.sendmail(self.sender_email, self.recipient_email, self.message.as_string())
            server.close()
            print("Email sent successfully!")
        except Exception as e:
            print(f"Failed to send email. Error: {str(e)}")

class DeepDocEmailSender(EmailSender):

    def __init__(self, content, file_name, recipient_email):
        subject = "DeepDoc: Result Available for Download"
        body = "This is the generated markdown content for your document."
        markdown_content = content

        smtp_server = "smtp.gmail.com"
        smtp_port = 587

        # Create an instance of EmailSender
        super().__init__(recipient_email, subject, body, markdown_content, file_name, smtp_server, smtp_port)

