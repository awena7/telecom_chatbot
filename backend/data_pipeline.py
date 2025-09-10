# data_pipeline.py 
import csv, json
from sentence_transformers import SentenceTransformer
import chromadb

# Initialize embedding model
embedder = SentenceTransformer("all-MiniLM-L6-v2")

# Persistent ChromaDB
chroma_client = chromadb.PersistentClient(path="chroma_storage")

# Create/get collections
faq_collection = chroma_client.get_or_create_collection("faq_embeddings")
dialogue_collection = chroma_client.get_or_create_collection("dialogue_embeddings")


# Load FAQ data (new format: type, customer_input, bot_reply)
def load_faq_data(csv_file):
    faq_data = []
    encodings_to_try = ["utf-8", "utf-8-sig", "latin-1"]

    for enc in encodings_to_try:
        try:
            with open(csv_file, newline="", encoding=enc, errors="replace") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    faq_data.append({
                        "type": row["type"],
                        "customer_input": row["customer_input"],
                        "bot_reply": row["bot_reply"]
                    })
            print(f"✅ Loaded {csv_file} using encoding={enc}")
            break
        except UnicodeDecodeError:
            print(f"⚠️ Failed to load {csv_file} with encoding={enc}, trying next...")
    
    return faq_data


# Load dialogue data (unchanged)
def load_dialogue_data(json_file):
    with open(json_file, 'r', encoding='utf-8') as f:
        return json.load(f)


# Convert dialogues into few-shots (unchanged)
def create_all_few_shots(dialogues):
    all_shots = []
    for dialogue in dialogues:
        for turn in dialogue["turns"]:
            role = "user" if turn["speaker"].lower() == "customer" else "assistant"
            all_shots.append({"role": role, "content": turn["text"]})
    return all_shots


# Store FAQ embeddings (embedding customer_input + bot_reply together)
def store_faq_embeddings(faq_data):
    existing_ids = set(faq_collection.get()['ids'])
    for i, faq in enumerate(faq_data):
        doc_id = f"faq_{i}"
        if doc_id not in existing_ids:
            combined_text = faq["customer_input"] + " " + faq["bot_reply"]
            vector = embedder.encode(combined_text).tolist()
            
            faq_collection.add(
                ids=[doc_id],
                embeddings=[vector],
                documents=[faq["bot_reply"]],
                metadatas=[{
                    "type": faq["type"],
                    "customer_input": faq["customer_input"],
                    "bot_reply": faq["bot_reply"]
                }]
            )


# Store dialogue embeddings (unchanged)
def store_dialogue_embeddings(all_shots):
    existing_ids = set(dialogue_collection.get()['ids'])
    for i, shot in enumerate(all_shots):
        if shot["role"] == "user":
            doc_id = f"dlg_{i}"
            if doc_id not in existing_ids:
                vector = embedder.encode(shot["content"]).tolist()
                dialogue_collection.add(
                    ids=[doc_id],
                    embeddings=[vector],
                    documents=[shot["content"]],
                    metadatas=[{"role": shot["role"]}]
                )


if __name__ == "__main__":
    # Load both FAQ datasets
    faq_data_1 = load_faq_data("faq_data_transformed.csv")
    faq_data_2 = load_faq_data("telecom_faq_dataset.csv")

    # Merge them
    combined_faq_data = faq_data_1 + faq_data_2

    # Load dialogues
    dialogue_data = load_dialogue_data("dialogue_data.json")
    all_few_shots = create_all_few_shots(dialogue_data)

    # Store in ChromaDB
    store_faq_embeddings(combined_faq_data)
    store_dialogue_embeddings(all_few_shots)

    print("✅ Both FAQ datasets and dialogue data successfully embedded and stored in ChromaDB.")
