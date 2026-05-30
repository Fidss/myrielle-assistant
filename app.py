from flask import Flask, render_template, request, jsonify, session
import requests
import json
from datetime import datetime
import uuid
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24)

# OpenRouter configuration
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY', 'YOUR_API_KEY')
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

@app.route('/')
def index():
    if 'conversation_id' not in session:
        session['conversation_id'] = str(uuid.uuid4())
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    try:
        user_message = request.json.get('message', '')
        
        headers = {
            'Authorization': f'Bearer {OPENROUTER_API_KEY}',
            'Content-Type': 'application/json',
            'HTTP-Referer': 'https://myrielle-assistant.vercel.app',
            'X-Title': 'Myrielle Assistant'
        }
        
        payload = {
            'model': 'openai/gpt-oss-120b:free',
            'messages': [
                {
                    'role': 'system',
                    'content': """Anda adalah Myrielle, asisten AI yang membantu, ramah, dan profesional. 
                    Berikan respons yang jelas, akurat, dan membantu. Gunakan bahasa yang natural dan sopan."""
                },
                {
                    'role': 'user',
                    'content': user_message
                }
            ],
            'temperature': 0.7,
            'max_tokens': 1000,
            'top_p': 0.9
        }
        
        response = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            ai_response = response.json()['choices'][0]['message']['content']
            return jsonify({
                'success': True,
                'response': ai_response,
                'timestamp': datetime.now().strftime('%H:%M')
            })
        else:
            # Menampilkan semua respon error dari API
            try:
                error_details = response.json()
            except:
                error_details = response.text
            
            return jsonify({
                'success': False,
                'error': 'API Error',
                'status_code': response.status_code,
                'api_response': error_details,
                'response_text': response.text,
                'headers': dict(response.headers)
            }), response.status_code
            
    except requests.exceptions.Timeout as e:
        return jsonify({
            'success': False,
            'error': 'Request timeout',
            'error_type': 'Timeout',
            'error_details': str(e),
            'timestamp': datetime.now().strftime('%H:%M:%S')
        }), 500
    
    except requests.exceptions.ConnectionError as e:
        return jsonify({
            'success': False,
            'error': 'Connection Error',
            'error_type': 'ConnectionError',
            'error_details': str(e),
            'timestamp': datetime.now().strftime('%H:%M:%S')
        }), 500
    
    except requests.exceptions.RequestException as e:
        return jsonify({
            'success': False,
            'error': 'Request Exception',
            'error_type': type(e).__name__,
            'error_details': str(e),
            'timestamp': datetime.now().strftime('%H:%M:%S')
        }), 500
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'Unexpected Error',
            'error_type': type(e).__name__,
            'error_details': str(e),
            'timestamp': datetime.now().strftime('%H:%M:%S')
        }), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
