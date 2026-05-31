from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
import requests
import json
from datetime import datetime
import uuid
import os
import time
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)
app.secret_key = os.urandom(24)

# OpenRouter configuration
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY', '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')
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# Available models
AVAILABLE_MODELS = {
    'moonshotai/kimi-k2.6:free': 'Kimi K2.6',
    'openai/gpt-oss-20b:free': 'GPT-OSS 20B',
    'google/gemma-4-31b-it:free': 'Gemma 4 31B',
    'qwen/qwen3-next-80b-a3b-instruct:free': 'Qwen 3 Next 80B',
    'meta-llama/llama-3.3-70b-instruct:free': 'Llama 3.3 70B'
}

@app.route('/')
def index():
    if 'conversation_id' not in session:
        session['conversation_id'] = str(uuid.uuid4())
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    try:
        user_message = request.json.get('message', '')
        selected_model = request.json.get('model', 'moonshotai/kimi-k2.6:free')
        attachments = request.json.get('attachments', [])
        
        # Build system message with context about file uploads
        system_content = """Anda adalah Myrielle, asisten AI yang membantu, ramah, dan profesional. 
        Berikan respons yang jelas, akurat, dan membantu. Gunakan bahasa yang natural dan sopan.
        Jika pengguna mengunggah file, analisis konten file tersebut dan berikan jawaban yang relevan.
        Untuk kode program, berikan penjelasan dan contoh yang jelas dengan format markdown yang tepat."""
        
        # Add attachment info to user message if needed
        if attachments and len(attachments) > 0:
            attachment_info = "\n\n[Info: Pengguna mengunggah file berikut: " + ", ".join([a.get('name', 'file') for a in attachments]) + "]"
            user_message = user_message + attachment_info if user_message else attachment_info
        
        headers = {
            'Authorization': f'Bearer {OPENROUTER_API_KEY}',
            'Content-Type': 'application/json',
            'HTTP-Referer': 'https://myrielle-assistant.vercel.app',
            'X-Title': 'Myrielle Assistant'
        }
        
        payload = {
            'model': selected_model,
            'messages': [
                {
                    'role': 'system',
                    'content': system_content
                },
                {
                    'role': 'user',
                    'content': user_message
                }
            ],
            'temperature': 0.7,
            'max_tokens': 2000,
            'top_p': 0.9
        }
        
        # Add retry logic for rate limiting
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                response = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=45)
                
                if response.status_code == 200:
                    ai_response = response.json()['choices'][0]['message']['content']
                    return jsonify({
                        'success': True,
                        'response': ai_response,
                        'model': selected_model,
                        'timestamp': datetime.now().strftime('%H:%M')
                    })
                elif response.status_code == 429:
                    # Rate limit - wait and retry
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay * (attempt + 1))
                        continue
                    else:
                        # Try alternative model if available
                        alternative_model = get_alternative_model(selected_model)
                        if alternative_model:
                            payload['model'] = alternative_model
                            response = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=45)
                            if response.status_code == 200:
                                ai_response = response.json()['choices'][0]['message']['content']
                                return jsonify({
                                    'success': True,
                                    'response': f"[Menggunakan model alternatif: {AVAILABLE_MODELS.get(alternative_model, alternative_model)}]\n\n{ai_response}",
                                    'model': alternative_model,
                                    'timestamp': datetime.now().strftime('%H:%M')
                                })
                        
                        error_details = response.json() if response.text else {}
                        return jsonify({
                            'success': False,
                            'error': 'Rate limit exceeded. Silakan coba lagi dalam beberapa saat.',
                            'error_type': 'RateLimit',
                            'status_code': 429,
                            'api_response': error_details
                        }), 429
                else:
                    # Other errors
                    try:
                        error_details = response.json()
                    except:
                        error_details = {'error': response.text}
                    
                    return jsonify({
                        'success': False,
                        'error': f'API Error: {response.status_code}',
                        'status_code': response.status_code,
                        'api_response': error_details
                    }), response.status_code
                    
            except requests.exceptions.Timeout:
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                return jsonify({
                    'success': False,
                    'error': 'Request timeout. Silakan coba lagi.',
                    'error_type': 'Timeout'
                }), 500
                
            except requests.exceptions.ConnectionError:
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                return jsonify({
                    'success': False,
                    'error': 'Connection error. Periksa koneksi internet Anda.',
                    'error_type': 'ConnectionError'
                }), 500
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'Unexpected Error',
            'error_type': type(e).__name__,
            'error_details': str(e)
        }), 500

def get_alternative_model(current_model):
    """Get an alternative model when rate limit is hit"""
    alternatives = {
        'moonshotai/kimi-k2.6:free': 'meta-llama/llama-3.3-70b-instruct:free',
        'openai/gpt-oss-20b:free': 'qwen/qwen3-next-80b-a3b-instruct:free',
        'google/gemma-4-31b-it:free': 'moonshotai/kimi-k2.6:free',
        'qwen/qwen3-next-80b-a3b-instruct:free': 'meta-llama/llama-3.3-70b-instruct:free',
        'meta-llama/llama-3.3-70b-instruct:free': 'moonshotai/kimi-k2.6:free'
    }
    return alternatives.get(current_model)

@app.route('/models', methods=['GET'])
def get_models():
    """Endpoint to get available models"""
    return jsonify({
        'success': True,
        'models': AVAILABLE_MODELS
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)
