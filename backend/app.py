from flask import Flask, request, jsonify, render_template  
import ollama
import csv
import os
from sentence_transformers import SentenceTransformer
import chromadb

# Paths relative to backend/app.py
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, "..", "frontend")

# Correct structure: templates + static
TEMPLATE_DIR = os.path.join(FRONTEND_DIR, "templates")
STATIC_DIR = os.path.join(FRONTEND_DIR, "static")

app = Flask(
    __name__,
    static_folder=STATIC_DIR,
    template_folder=TEMPLATE_DIR
)

chat_history = []

# Initialize embedder
embedder = SentenceTransformer('all-MiniLM-L6-v2')

# Persistent ChromaDB (already filled by data_pipeline.py)
chroma_client = chromadb.PersistentClient(path="chroma_storage")
faq_collection = chroma_client.get_collection("faq_embeddings")
dialogue_collection = chroma_client.get_collection("dialogue_embeddings")

# ----------------- Search Functions -----------------
def search_faqs(user_input, limit=3):
    vector = embedder.encode(user_input).tolist()
    results = faq_collection.query(query_embeddings=[vector], n_results=limit)
    faq_examples = []
    for meta, answer in zip(results["metadatas"][0], results["documents"][0]):
        faq_examples.append({"role": "user", "content": meta["customer_input"]})
        faq_examples.append({"role": "assistant", "content": answer})
    return faq_examples

def search_dialogues(user_input, limit=6):
    vector = embedder.encode(user_input).tolist()
    results = dialogue_collection.query(query_embeddings=[vector], n_results=limit)
    few_shots = []
    for doc in results["documents"][0]:
        few_shots.append({"role": "user", "content": doc})
    return few_shots

# ----------------- Prompt Builder -----------------
def build_prompt(user_input, few_shots, faq_examples):
    prompt = (
        "You are a helpful telecom support assistant. "
        "Always give clear, short answers (2-3 sentences max). "
        "Do NOT simulate entire conversations. "
        "Base your answers on the following relevant info if useful:\n\n"
    )

    if faq_examples:
        prompt += "Relevant FAQs:\n"
        for ex in faq_examples:
            prompt += f"- Q: {ex['content'] if ex['role']=='user' else ''} A: {ex['content'] if ex['role']=='assistant' else ''}\n"
        prompt += "\n"

    # Only last 2 turns from chat_history to keep it focused
    for shot in chat_history[-4:]:
        role = "User" if shot["role"] == "user" else "Assistant"
        prompt += f"{role}: {shot['content']}\n"

    prompt += f"User: {user_input}\nAssistant:"
    return prompt


# ----------------- Routes -----------------
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    user_input = data.get("user_input")

    if not user_input:
        return jsonify({"error": "Missing user_input"}), 400

    selected_faqs = search_faqs(user_input)
    selected_shots = search_dialogues(user_input)
    prompt = build_prompt(user_input, selected_shots, selected_faqs)

    try:
        response = ollama.generate(model="llama3:8b", prompt=prompt)
        bot_reply = response['response'].strip()

        chat_history.append({"role": "user", "content": user_input})
        chat_history.append({"role": "assistant", "content": bot_reply})

        return jsonify({
            "response": bot_reply,
            "original_input": user_input
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/feedback", methods=["POST"])
def save_feedback():
    data = request.json
    original_input = data.get("original_input")
    bot_reply = data.get("bot_reply")
    feedback = data.get("feedback")

    with open("feedback.csv", "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([original_input, bot_reply, feedback])

    return jsonify({"message": "Feedback saved successfully"})

# ----------------- Reset Route -----------------
@app.route("/reset", methods=["POST"])
def reset_chat():
    global chat_history
    chat_history = []
    return jsonify({"message": "Chat history cleared"})

if __name__ == "__main__":
    app.run(debug=True)
