import os
from dotenv import load_dotenv
from utils import send_email

load_dotenv()

print("Testing email configuration...")
print(f"SMTP Host: {os.getenv('MAIL_HOST')}")
print(f"SMTP User: {os.getenv('MAIL_USERNAME')}")

result = send_email(
    to_email=os.getenv('ADMIN_EMAIL'),
    subject="✅ WekaSafe Email Test",
    body="If you see this, your email configuration is working perfectly!"
)

if result:
    print("\n✅ Email sent successfully! Check your inbox.")
else:
    print("\n❌ Email failed. Check your .env configuration.")