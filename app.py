from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import faiss
import numpy as np
from openai import OpenAI
import os

app = Flask(__name__)

# Load OpenAI
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# Load FAISS index
index = faiss.read_index("index.faiss")

# Load text chunks
with open("chunks.txt", "r", encoding="utf-8") as f:
    chunks = f.read().split("\n---\n")

# Load users
def load_users():
    if not os.path.exists("users.txt"):
        return []
    with open("users.txt", "r") as f:
        return [line.strip() for line in f.readlines()]

# Search function
def search(query):
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=query
    )
    query_vector = np.array([response.data[0].embedding]).astype("float32")

    D, I = index.search(query_vector, k=3)
    results = [chunks[i] for i in I[0]]
    return "\n".join(results)

# WhatsApp webhook
@app.route("/whatsapp", methods=["POST"])
def whatsapp():
    incoming_msg = request.values.get("Body", "").strip()

    user_number = request.values.get("From", "")
    user_number = user_number.replace("whatsapp:", "")

    AUTHORIZED_USERS = load_users()

    # 🔒 Access control
    if user_number not in AUTHORIZED_USERS:
        resp = MessagingResponse()
        resp.message("""🚆 IRPWM AI Assistant

💰 Subscription: ₹299/month

👉 Pay here:
https://rzp.io/l/abcd1234

After payment, send screenshot to activate access.""")
        return str(resp)

    # 🔍 Search + AI response
    context = search(incoming_msg)

    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "You are a railway expert. Answer in Hindi or English based on user language. Be clear and practical."
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

# Railway compatible run
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
