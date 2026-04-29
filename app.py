from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import faiss
import numpy as np
from openai import OpenAI
import os

app = Flask(__name__)

# OpenAI
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# Safe loading
index = None
chunks = []

if os.path.exists("index.faiss"):
    index = faiss.read_index("index.faiss")

if os.path.exists("chunks.txt"):
    with open("chunks.txt", "r", encoding="utf-8") as f:
        chunks = f.read().split("\n---\n")

# Load users safely
def load_users():
    if not os.path.exists("users.txt"):
        return []
    with open("users.txt", "r") as f:
        return [line.strip() for line in f.readlines()]

# Search function (safe)
def search(query):
    if index is None or not chunks:
        return "Knowledge base not loaded."

    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=query
    )

    query_vector = np.array([response.data[0].embedding]).astype("float32")
    D, I = index.search(query_vector, k=3)

    results = []
    for i in I[0]:
        if i < len(chunks):
            results.append(chunks[i])

    return "\n".join(results)

# WhatsApp route
@app.route("/whatsapp", methods=["POST"])
def whatsapp():
    try:
        incoming_msg = request.values.get("Body", "").strip()

        user_number = request.values.get("From", "")
        user_number = user_number.replace("whatsapp:", "")

        AUTHORIZED_USERS = load_users()

        # Access control
        if user_number not in AUTHORIZED_USERS:
            resp = MessagingResponse()
            resp.message("""🚆 IRPWM AI Assistant

💰 Subscription: ₹299/month

👉 Pay here:
https://rzp.io/l/abcd1234

After payment, send screenshot to activate access.""")
            return str(resp)

        # Search
        context = search(incoming_msg)

        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are a railway expert. Answer clearly in Hindi or English. Do not guess."
                },
                {
                    "role": "user",
                    "content": f"Context:\n{context}\n\nQuestion: {incoming_msg}"
                }
            ]
        )

        answer = completion.choices[0].message.content

        resp = MessagingResponse()
        resp.message(answer[:1500])

        return str(resp)

    except Exception as e:
        resp = MessagingResponse()
        resp.message("⚠️ System error. Please try again later.")
        print("ERROR:", str(e))
        return str(resp)

# Railway compatible run
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
