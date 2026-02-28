import os
from twilio.rest import Client


def enviar_mensaje(to: str, body: str) -> str:
    """Envía un mensaje de WhatsApp usando Twilio."""

    client = Client(
        os.getenv("TWILIO_ACCOUNT_SID"),
        os.getenv("TWILIO_AUTH_TOKEN"),
    )

    message = client.messages.create(
        from_=os.getenv("TWILIO_WHATSAPP_NUMBER", "whatsapp:+14155238886"),
        body=body,
        to=to,
    )

    return message.sid
