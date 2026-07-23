# from flask_mail import Message
# from extension import mail

# def send_verification_mail(email, fullname, verification_link):
#     msg = Message(
#         subject="Verify your Email",
#         recipients=[email]
#     )
#     msg.body = f"""
#     Hello {fullname},

#     Thank you for registering.

#     Click the link below to verify your email.

#     {verification_link}

#     If you don't register, please ignore this email.

#     Regards, 
#     LearningPro
#     """

#     mail.send(msg)



import os
import requests

def send_verification_mail(email, fullname, verification_link):
    response = requests.post(
        "https://api.brevo.com/v3/smtp/email",
        headers={
            "api-key": os.getenv("BREVO_API_KEY"),
            "Content-Type": "application/json",
        },
        json={
            "sender": {"name": "LearningPro", "email": "stevenbryan0307@gmail.com"},
            "to": [{"email": email, "name": fullname}],
            "subject": "Verify your Email",
            "textContent": f"""
Hello {fullname},

Thank you for registering.

Click the link below to verify your email.

{verification_link}

If you don't register, please ignore this email.

Regards,
LearningPro
""",
        },
    )
    response.raise_for_status()