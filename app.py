from flask import Flask, render_template, request, jsonify, session
import requests
from datetime import datetime
import uuid
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(name)
app.secret_key = os.urandom(24)

OpenRouter Configuration

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

@app.route('/')
def index():
if 'conversation_id' not in session:
session['conversation_id'] = str(uuid.uuid4())
return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
try:
data = request.get_json()

    if not data:
        return jsonify({
            "success": False,
            "error": "Request body kosong"
        }), 400

    user_message = data.get("message", "").strip()

    if not user_message:
        return jsonify({
            "success": False,
            "error": "Pesan tidak boleh kosong"
        }), 400

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://myrielle-assistant.vercel.app",
        "X-Title": "Myrielle Assistant"
    }

    payload = {
        "model": "openai/gpt-oss-120b:free",
        "messages": [
            {
                "role": "system",
                "content": """Anda adalah Myrielle, asisten AI yang membantu, ramah, dan profesional.

Berikan respons yang jelas, akurat, dan membantu.
Gunakan bahasa yang natural dan sopan."""
},
{
"role": "user",
"content": user_message
}
],
"temperature": 0.7,
"max_tokens": 1000,
"top_p": 0.9
}

    response = requests.post(
        OPENROUTER_URL,
        headers=headers,
        json=payload,
        timeout=30
    )

    try:
        api_response = response.json()
    except Exception:
        api_response = response.text

    # Jika sukses
    if response.status_code == 200:

        if (
            isinstance(api_response, dict)
            and "choices" in api_response
            and len(api_response["choices"]) > 0
        ):
            ai_response = api_response["choices"][0]["message"]["content"]

            return jsonify({
                "success": True,
                "response": ai_response,
                "timestamp": datetime.now().strftime("%H:%M")
            })

        return jsonify({
            "success": False,
            "error": "Format response tidak valid",
            "api_response": api_response
        }), 500

    # Jika OpenRouter mengembalikan error
    return jsonify({
        "success": False,
        "status_code": response.status_code,
        "api_response": api_response
    }), response.status_code

except requests.exceptions.Timeout:
    return jsonify({
        "success": False,
        "error": "Request timeout",
        "details": "Server OpenRouter terlalu lama merespons"
    }), 504

except requests.exceptions.ConnectionError as e:
    return jsonify({
        "success": False,
        "error": "Connection Error",
        "details": str(e)
    }), 500

except requests.exceptions.RequestException as e:
    return jsonify({
        "success": False,
        "error": "Request Exception",
        "details": str(e)
    }), 500

except Exception as e:
    return jsonify({
        "success": False,
        "error": "Internal Server Error",
        "details": str(e)
    }), 500

if name == "main":
app.run(debug=True, port=5000)
