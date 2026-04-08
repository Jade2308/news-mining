import os
import requests
from dotenv import load_dotenv

load_dotenv()
api_key = os.environ.get("GEMINI_API_KEY")

if not api_key:
    print("Không tìm thấy GEMINI_API_KEY trong file .env")
    exit(1)

url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
resp = requests.get(url)

if resp.status_code == 200:
    models = resp.json().get('models', [])
    print("\n=== DANH SÁCH MÃ MODEL GOOGLE HỖ TRỢ CHO API KEY NÀY ===")
    for m in models:
        name = m.get('name')
        if 'generateContent' in m.get('supportedGenerationMethods', []):
            print(f"- {name}")
    print("========================================================\n")
else:
    print(f"Lỗi: {resp.status_code} - {resp.text}")
