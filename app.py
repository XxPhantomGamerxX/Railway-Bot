def load_users():
    with open("users.txt", "r") as f:
        return [line.strip() for line in f.readlines()]
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import faiss
import numpy as np
from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

client = OpenAI(api_key="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")

app = Flask(__name__)

# Load FAISS index
index = faiss.read_index("index.faiss")

# Load text chunks
with open("chunks.txt", "r", encoding="utf-8") as f:
    chunks = f.read().split("\n---\n")

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

@app.route("/whatsapp", methods=["POST"])
def whatsapp():
    incoming_msg = request.values.get("Body", "").strip()
    user_number = request.values.get("From", "")
user_number = user_number.replace("whatsapp:", "")

AUTHORIZED_USERS = load_users()

if user_number not in AUTHORIZED_USERS:
    resp = MessagingResponse()
    resp.message("""🚆 IRPWM AI Assistant

💰 Subscription: ₹1000/user/year

👉 Pay here:
https://rzp.io/rzp/ORkwHM1

After payment, send screenshot to activate access.""")
    
    return str(resp)

    context = search(incoming_msg)

    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "You are a senior Indian Railways Permanent Way Engineer. Answer in Hindi or English based on user language. Keep answers clear and practical."
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

if __name__ == "__main__":
    app.run(port=5000)
