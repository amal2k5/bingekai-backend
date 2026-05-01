import random
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.template.loader import render_to_string


def generate_otp():
    return str(random.randint(100000, 999999))


def send_verification_email(email, otp):

    subject = "BingeKai Email Verification"

    html_content = render_to_string(
        "emails/verification_email.html",
        {
            "otp": otp
        }
    )

    email = EmailMultiAlternatives(
        subject,
        f"Your verification code is {otp}",
        settings.EMAIL_HOST_USER,
        [email],
    )

    email.attach_alternative(html_content, "text/html")
    email.send()