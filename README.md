# telecom_chatbot
A Generative AI-based customer support assistant for telecom services.  
This chatbot helps users troubleshoot internet issues, answer FAQs, log complaints, and provide quick solutions in a conversational manner.

## Features
- **Generative AI Responses** using [Ollama](https://ollama.ai/) with `llama3:8b`.
- **Semantic Search** powered by SentenceTransformers + ChromaDB.
- **Hybrid Approach**:
  - Short FAQs retrieved from pre-embedded datasets.
  - Multi-turn dialogues handled via few-shot examples.
- **Feedback Mechanism** → stores user feedback in `feedback.csv`.
- **Web UI** built with HTML, CSS, and JS.
- **Flask Backend** for API routes 

## Getting Started  

### 1. Install Requirements  
```bash
pip install -r requirements.txt

### 2. Run Data Pipeline (first time only)  

Before starting the chatbot, you need to embed the FAQ + dialogue data into **ChromaDB**:  

```bash
python data_pipeline.py

### 3. Run the Flask Backend  

Start the backend server:  

```bash
python app.py

### 4. Ollama Setup  

This project uses **Ollama** to run the **Llama 3 (8B)** model locally.  

1. Install Ollama → [Download here](https://ollama.ai)  
2. Pull the Llama 3 model:  

```bash
ollama pull llama3:8b



