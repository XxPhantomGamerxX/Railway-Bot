from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import os

app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running"

@app.route("/whatsapp", methods=["POST"])
def whatsapp():
    try:
        incoming_msg = request.values.get("Body", "")

        resp = MessagingResponse()
        resp.message("✅ Bot working. You said: " + incoming_msg)

        return str(resp)

    except Exception as e:
        return "Error"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
