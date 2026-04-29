from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import os

app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running"

from openai import OpenAI
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

@app.route("/whatsapp", methods=["POST"])
def whatsapp():
    try:
        incoming_msg = request.values.get("Body", "")

        try:
            completion = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a railway assistant."},
                    {"role": "user", "content": incoming_msg}
                ]
            )
            answer = completion.choices[0].message.content

        except Exception as e:
            answer = "⚠️ AI temporarily unavailable."

        resp = MessagingResponse()
        resp.message(answer[:1500])

        return str(resp)

    except Exception:
        return "Error"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
