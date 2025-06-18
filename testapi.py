import requests
import json

# Your API endpoint
API_URL = "http://127.0.0.1:5000/api/"

def test_api(question):
    """Test the API with a question"""
    try:
        # Prepare the data
        data = {"question": question}
        
        # Make the POST request
        response = requests.post(API_URL, json=data)
        
        # Check if request was successful
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Question: {question}")
            print(f"📝 Answer: {result['answer']}")
            print("🔗 Related Links:")
            for i, link in enumerate(result['links'], 1):
                print(f"   {i}. {link['text']}")
                print(f"      URL: {link['url']}")
                if 'similarity' in link:
                    print(f"      Similarity: {link['similarity']:.3f}")
            print("-" * 50)
            
            # Now we actually use the json module for pretty printing
            print("📋 Full JSON Response:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            print("=" * 50)
            
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
    
    except requests.exceptions.ConnectionError:
        print("❌ Error: Cannot connect to API. Make sure your Flask app is running!")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    # Test with different questions
    test_questions = [
        "linear regression",
        "machine learning", 
        "data visualization",
        "python pandas",
        "statistics"
    ]
    
    print("🧪 Testing TDS Discourse Search API")
    print("=" * 50)
    
    for question in test_questions:
        test_api(question)

