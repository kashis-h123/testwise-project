from google import genai
from dotenv import load_dotenv
import os

# Load .env
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("❌ API key not found in .env")
    exit()

print("✅ API Key Loaded:", api_key[:10], "...")  # partial print for safety

# Initialize client
client = genai.Client(api_key=api_key)

try:
    response = client.models.generate_content(
        model="gemini-3-flash-preview",
        contents="Say hello in one line"
    )

    print("\n🎉 API WORKING!")
    print("Response:", response.text)

except Exception as e:
    print("\n❌ API ERROR:")
    print(e)