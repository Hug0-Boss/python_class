from flask_mail import Message
from extension import mail

def send_verification_mail(email, fullname, verification_link):
    msg = Message(
        subject="Verify your Email",
        recipients=[email]
    )
    msg.body = f"""
    Hello {fullname},

    Thank you for registering.

    Click the link below to verify your email.

    {verification_link}

    If you don't register, please ignore this email.

    Regards, 
    LearningPro
    """

    mail.send(msg)