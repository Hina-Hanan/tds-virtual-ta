import requests

# Replace with your actual ngrok URL
API_URL = "https://8707-2401-4900-8fdc-6e2a-519e-606e-2787-6a1a.ngrok-free.app/api/"

def test_api():
    questions = ["linear regression", "machine learning", "data visualization"]
    
    for question in questions:
        try:
            response = requests.post(API_URL, json={"question": question})
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Question: {question}")
                print(f"📝 Answer: {result['answer']}")
                print("🔗 Links:")
                for link in result['links']:
                    print(f"   - {link['text']} (similarity: {link.get('similarity', 'N/A')})")
                print("-" * 50)
            else:
                print(f"❌ Error: {response.status_code}")
                print(f"Response: {response.text}")
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_api()
