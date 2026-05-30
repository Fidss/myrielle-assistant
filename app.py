from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
import requests
import json
from datetime import datetime
import uuid
import os
import traceback
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)
app.secret_key = os.urandom(24)

# OpenRouter configuration
OPENROUTER_API_KEY = "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"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    try:
        user_message = request.json.get('message', '')
        
        headers = {
            'Authorization': f'Bearer {OPENROUTER_API_KEY}',
            'Content-Type': 'application/json',
            'HTTP-Referer': 'http://localhost:5000',
            'X-Title': 'Myrielle Assistant'
        }
        
        payload = {
            'model': 'openai/gpt-3.5-turbo',
            'messages': [
                {
                    'role': 'system',
                    'content': "Anda adalah Myrielle, asisten AI yang membantu, ramah, dan profesional."
                },
                {
                    'role': 'user',
                    'content': user_message
                }
            ],
            'temperature': 0.7,
            'max_tokens': 1000
        }
        
        print("Sending request to OpenRouter...")
        print(f"Headers: {headers}")
        print(f"Payload: {json.dumps(payload, indent=2)}")
        
        response = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=60)
        
        # Get response data
        try:
            response_json = response.json()
        except:
            response_json = {"raw_response": response.text}
        
        print(f"Status Code: {response.status_code}")
        print(f"Full Response: {json.dumps(response_json, indent=2)}")
        
        if response.status_code == 200:
            ai_response = response_json['choices'][0]['message']['content']
            return jsonify({
                'success': True,
                'response': ai_response,
                'timestamp': datetime.now().strftime('%H:%M'),
                'debug': {
                    'status_code': response.status_code,
                    'model_used': response_json.get('model', 'unknown')
                }
            })
        else:
            # Return full error response to frontend
            return jsonify({
                'success': False,
                'error': f'API Error: {response.status_code}',
                'full_response': response_json,
                'status_code': response.status_code,
                'headers_sent': headers,
                'payload_sent': payload
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

@app.route('/test', methods=['GET'])
def test():
    """Test endpoint to check API connection"""
    try:
        headers = {
            'Authorization': f'Bearer {OPENROUTER_API_KEY}',
            'Content-Type': 'application/json',
        }
        
        # Simple test request
        test_payload = {
            'model': 'openai/gpt-3.5-turbo',
            'messages': [{'role': 'user', 'content': 'Say hello'}],
            'max_tokens': 10
        }
        
        response = requests.post(OPENROUTER_URL, headers=headers, json=test_payload, timeout=30)
        
        return jsonify({
            'status': 'test_completed',
            'status_code': response.status_code,
            'response': response.json() if response.status_code == 200 else response.text
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

if __name__ == '__main__':
    print("Starting Flask server...")
    print(f"OpenRouter API Key: {OPENROUTER_API_KEY[:20]}...")
    app.run(debug=True, port=5000)
