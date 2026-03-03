import os
from dotenv import load_dotenv
from google import genai

load_dotenv()
api_key = os.getenv('GOOGLE_API_KEY')

if not api_key:
    print("No API Key found")
else:
    try:
        client = genai.Client(api_key=api_key)
        print(f"Checking models for key: {api_key[:5]}...")

        # List all available models
        print("\nAvailable models:")
        for model in client.models.list(config={"page_size": 100}):
            print(f"- {model.name}")

    except Exception as e:
        print(f"Error: {e}")
