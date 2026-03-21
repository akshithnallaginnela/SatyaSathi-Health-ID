import os
from twilio.rest import Client

def send_otp_sms(phone_number: str, otp: str):
    """
    Sends a 6-digit OTP to the provided phone number using Twilio.
    Falls back to a console print if Twilio is not fully configured.
    """
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    from_phone = os.getenv("TWILIO_PHONE_NUMBER")
    
    # Ensure phone number is E.164 formatted 
    if not phone_number.startswith('+'):
        phone_number = f"+91{phone_number}"
        
    if not account_sid or not auth_token or not from_phone:
        print(f"[MOCK SMS] To: {phone_number} | Your Health ID OTP is: {otp}")
        return
        
    try:
        client = Client(account_sid, auth_token)
        message = client.messages.create(
            body=f"Your Health ID verification code is: {otp}. Do not share this with anyone.",
            from_=from_phone,
            to=phone_number
        )
        print(f"Twilio SMS sent: {message.sid}")
    except Exception as e:
        print(f"Twilio failed, falling back to mock. Error: {e}")
        print(f"[MOCK SMS] To: {phone_number} | Your Health ID OTP is: {otp}")
