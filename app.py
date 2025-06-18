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
    api_key=os.environ.get("HF_TOKEN"),
)

EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# Load your scraped Discourse posts
with open("discourse_posts.json") as f:
    posts = json.load(f)

titles = [p["title"] for p in posts]
urls   = [f"https://discourse.onlinedegree.iitm.ac.in/t/{p['id']}" for p in posts]

# Fixed embedding function
def get_embedding(text: str) -> list[float]:
    try:
        print(f"Attempting to embed: '{text[:50]}...'")
        
        # Check if token exists
        if not os.environ.get("HF_TOKEN"):
            print("Error: HF_TOKEN not found")
            return []
        
        # Use the model-specific client approach
        model_client = InferenceClient(
            model=EMBED_MODEL,
            token=os.environ.get("HF_TOKEN")
        )
        
        # Call feature_extraction with the text directly
        result = model_client.feature_extraction(text)
        
        print(f"✅ Embedding successful, type: {type(result)}")
        
        # Handle different response formats
        if isinstance(result, np.ndarray):
            if result.ndim == 1:
                return result.tolist()
            elif result.ndim == 2 and result.shape[0] == 1:
                return result[0].tolist()
            else:
                return result.flatten().tolist()
        elif isinstance(result, list):
            if len(result) > 0 and isinstance(result[0], list):
                return result[0]
            return result
        else:
            print(f"Unexpected result type: {type(result)}")
            return []
            
    except Exception as e:
        print(f"❌ Error in get_embedding: {e}")
        print(f"Error type: {type(e)}")
        
        # Fallback: simple hash-based embedding
        print("Using fallback embedding method...")
        return get_embedding_fallback(text)

def get_embedding_fallback(text: str) -> list[float]:
    """Simple fallback embedding using text hashing"""
    import hashlib
    
    # Create a simple hash-based embedding (384 dimensions)
    hash_obj = hashlib.md5(text.encode())
    hash_hex = hash_obj.hexdigest()
    
    # Convert to numbers and normalize
    embedding = []
    for i in range(0, len(hash_hex), 2):
        val = int(hash_hex[i:i+2], 16) / 255.0
        embedding.append(val)
    
    # Extend to 384 dimensions
    while len(embedding) < 384:
        embedding.extend(embedding[:min(len(embedding), 384-len(embedding))])
    
    return embedding[:384]

# Precompute title embeddings once
if os.path.exists("title_embeddings.json"):
    with open("title_embeddings.json") as f:
        title_embeddings = json.load(f)
else:
    title_embeddings = []
    for i, title in enumerate(titles, 1):
        print(f"Processing {i}/{len(titles)}: {title[:50]}...")
        vec = get_embedding(title)
        title_embeddings.append(vec)
        time.sleep(0.1)  # Rate limiting

    with open("title_embeddings.json", "w") as f:
        json.dump(title_embeddings, f)

# Flask routes
@app.route("/", methods=["GET", "POST"])
def root():
    if request.method == "GET":
        return render_template("index.html")
    
    # Handle POST requests (API functionality)
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

    # Get question embedding
    q_embed_list = get_embedding(question)
    if not q_embed_list:
        return jsonify({"error": "Failed to embed question"}), 500
    
    q_embed = np.array(q_embed_list)

    # Compute cosine similarities
    def cosine(a, b):
        a, b = np.array(a), np.array(b)
        if np.linalg.norm(a) == 0 or np.linalg.norm(b) == 0:
            return 0.0
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

    sims = []
    for i, t_embed in enumerate(title_embeddings):
        if t_embed:
            sim = cosine(q_embed, t_embed)
            sims.append(sim)
        else:
            sims.append(0.0)

    # Pick top-2
    top2 = sorted(range(len(sims)), key=lambda i: sims[i], reverse=True)[:2]
    links = [{"url": urls[i], "text": titles[i], "similarity": round(sims[i], 3)} for i in top2]

    answer_text = f"Here are the most relevant discussions for: '{question}'"
    return jsonify({"answer": answer_text, "links": links})

@app.route("/api/", methods=["GET", "POST"])
def answer():
    if request.method == "GET":
        return jsonify({
            "message": "TDS Discourse Search API", 
            "usage": "Send POST request with JSON: {'question': 'your question'}",
            "example": {
                "method": "POST",
                "url": "/api/",
                "body": {"question": "machine learning"}
            }
        })
    
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
    links = [{"url": urls[i], "text": titles[i], "similarity": round(sims[i], 3)} for i in top2]

    answer_text = f"Here are the most relevant discussions for: '{question}'"
    return jsonify({"answer": answer_text, "links": links})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
