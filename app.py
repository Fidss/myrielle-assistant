from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

OPENROUTER_API_KEY = os.environ.get('OPENROUTER_API_KEY', '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')

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        user_message = data.get('message', '')
        model = data.get('model', 'moonshotai/kimi-k2.6:free')
        
        response = requests.post(
            'https://openrouter.ai/api/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {OPENROUTER_API_KEY}',
                'Content-Type': 'application/json'
            },
            json={
                'model': model,
                'messages': [{'role': 'user', 'content': user_message}]
            },
            timeout=30
        )
        
        return jsonify(response.json())
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Vercel handler
app.debug = False
