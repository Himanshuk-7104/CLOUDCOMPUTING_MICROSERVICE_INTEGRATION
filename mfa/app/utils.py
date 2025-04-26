import pyotp
from flask_mail import Message
from . import mail

def generate_otp_secret():
    return pyotp.random_base32()

def get_totp(otp_secret):
    return pyotp.TOTP(otp_secret)

def send_otp_email(email, otp):
    msg = Message("Your MFA OTP Code", sender="vanshikajadhav0187@gmail.com", recipients=[email])
    msg.body = f"Your OTP code is: {otp}"
    mail.send(msg)
