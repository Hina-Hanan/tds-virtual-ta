import os
import json
import base64
import time
from flask_cors import CORS
import numpy as np
from flask import Flask, request, jsonify, render_template
from huggingface_hub import InferenceClient

app = Flask(__name__)
CORS(app) 

# Initialize the HF InferenceClient
client = InferenceClient(
    provider="hf-inference",
    api_key=os.environ["HF_TOKEN"],
)

EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# Load your scraped Discourse posts
with open("discourse_posts.json") as f:  # Fixed filename
    posts = json.load(f)

titles = [p["title"] for p in posts]
urls   = [f"https://discourse.onlinedegree.iitm.ac.in/t/{p['id']}" for p in posts]

# Replace get_embedding with InferenceClient.feature_extraction
def get_embedding(text: str) -> list[float]:
    try:
        # client.feature_extraction returns a list of lists (batch of 1)
        result = client.feature_extraction(
            text,
            model=EMBED_MODEL
        )
        print("Length:", len(result))
        print("Sample:", result[:5] if len(result) > 5 else result)
        
        # Handle nested list structure - extract the actual embedding
        if isinstance(result, list) and len(result) > 0:
            if isinstance(result[0], list):
                return result[0]  # Extract first (and likely only) embedding
            return result
        return []
    except Exception as e:
        print("Error in get_embedding:", e)
        return []

# Precompute title embeddings once
if os.path.exists("title_embeddings.json"):
    with open("title_embeddings.json") as f:
        title_embeddings = json.load(f)
else:
    title_embeddings = []
    for i, title in enumerate(titles, 1):
        print(f"Processing {i}/{len(titles)}: {title[:50]}...")
        vec = get_embedding(title)
        if isinstance(vec, np.ndarray):  # Convert if it's a NumPy array
            vec = vec.tolist()
        title_embeddings.append(vec)
        time.sleep(0.1)  # Add small delay to avoid rate limiting

    with open("title_embeddings.json", "w") as f:
        json.dump(title_embeddings, f)

# Flask routes
@app.route("/", methods=["GET"])
def root():
    try:
        return render_template("index.html")
    except UnicodeDecodeError:
        return "<h1>TDS Discourse Search API</h1><p>API is running!</p>"


@app.route("/api/", methods=["POST"])
def answer():
    data = request.get_json()
    question = data.get("question")
    image_b64 = data.get("image")

    if not question:
        return jsonify({"error": "Question is required"}), 400

    # Optional: save image if provided
    if image_b64:
        header, b64data = (image_b64.split(",", 1)
                           if "," in image_b64 else (None, image_b64))
        img_bytes = base64.b64decode(b64data)
        os.makedirs("uploads", exist_ok=True)
        path = f"uploads/{int(time.time())}.webp"
        with open(path, "wb") as f:
            f.write(img_bytes)

    # 1) get question embedding
    q_embed_list = get_embedding(question)
    if not q_embed_list:
        return jsonify({"error": "Failed to embed question"}), 500
    
    q_embed = np.array(q_embed_list)
    
    # Check if embedding has reasonable dimensions
    if len(q_embed.shape) != 1 or q_embed.shape[0] == 0:
        return jsonify({"error": "Invalid question embedding shape"}), 500

    # 2) compute cosine similarities
    def cosine(a, b):
        a, b = np.array(a), np.array(b)
        if np.linalg.norm(a) == 0 or np.linalg.norm(b) == 0:
            return 0.0
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

    sims = []
    for i, t_embed in enumerate(title_embeddings):
        if t_embed:  # Skip empty embeddings
            sim = cosine(q_embed, t_embed)
            sims.append(sim)
        else:
            sims.append(0.0)

    # 3) pick top-2
    top2 = sorted(range(len(sims)), key=lambda i: sims[i], reverse=True)[:2]
    links = [{"url": urls[i], "text": titles[i], "similarity": sims[i]} for i in top2]

    answer_text = f"Here are the most relevant discussions for: '{question}'"
    return jsonify({"answer": answer_text, "links": links})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
