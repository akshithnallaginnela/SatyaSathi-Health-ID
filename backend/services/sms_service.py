import os
from twilio.rest import Client


def send_otp_sms(phone_number: str, otp: str) -> bool:
    """
    Sends a 6-digit OTP via Twilio SMS.
    Returns True if sent via Twilio, False if fell back to mock (console).
    """
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    from_phone = os.getenv("TWILIO_PHONE_NUMBER")

    # Ensure E.164 format for Indian numbers
    if not phone_number.startswith('+'):
        phone_number = f"+91{phone_number}"

    if not account_sid or not auth_token or not from_phone:
        print(f"[DEV MODE — SMS not sent] OTP for {phone_number}: {otp}")
        return False

    try:
        client = Client(account_sid, auth_token)
        message = client.messages.create(
            body=f"Your VitalID verification code is: {otp}. Valid for 10 minutes. Do not share this with anyone.",
            from_=from_phone,
            to=phone_number,
        )
        print(f"✅ Twilio SMS sent to {phone_number} | SID: {message.sid}")
        return True
    except Exception as e:
        print(f"❌ Twilio error: {e}")
        # Trial accounts can only SMS verified numbers — print OTP so dev can still test
        print(f"⚠️  [DEV FALLBACK] OTP for {phone_number} is: {otp}")
        return False
