from flask import Flask, render_template, request, jsonify, session
import requests
import json
from datetime import datetime
import uuid
import os
import re
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24)

# OpenRouter configuration
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY', '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')
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# Call AI function yang reusable
def call_ai(messages, temperature=0.7, max_tokens=1500):
    """Fungsi reusable untuk memanggil AI"""
    headers = {
        'Authorization': f'Bearer {OPENROUTER_API_KEY}',
        'Content-Type': 'application/json',
        'HTTP-Referer': 'https://myrielle-assistant.vercel.app',
        'X-Title': 'Myrielle Math Assistant'
    }
    
    payload = {
        'model': 'openai/gpt-oss-120b:free',
        'messages': messages,
        'temperature': temperature,
        'max_tokens': max_tokens,
        'top_p': 0.9
    }
    
    try:
        response = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=45)
        if response.status_code == 200:
            return {
                'success': True,
                'response': response.json()['choices'][0]['message']['content']
            }
        else:
            return {
                'success': False,
                'error': f'API Error: {response.status_code}',
                'details': response.text[:500]
            }
    except Exception as e:
        return {'success': False, 'error': str(e)}

# Materi pembelajaran matematika (sama seperti sebelumnya)
MATH_TOPICS = {
    'order_of_operations': {
        'name': 'Order of Operations',
        'level': 'Middle School',
        'description': 'Pelajari urutan operasi matematika (PEMDAS)',
        'content': '''# Order of Operations (Urutan Operasi)
## Aturan PEMDAS:
- **P**arentheses (Tanda kurung)
- **E**xponents (Eksponen/pangkat)
- **M**ultiplication (Perkalian) → kiri ke kanan
- **D**ivision (Pembagian) → kiri ke kanan
- **A**ddition (Penjumlahan) → kiri ke kanan
- **S**ubtraction (Pengurangan) → kiri ke kanan

## Contoh:
1. `3 + 4 × 2 = 3 + 8 = 11`
2. `(3 + 4) × 2 = 7 × 2 = 14`

## Latihan Soal:
1. `8 + 2 × 5 - 3 = ?`
2. `(12 - 4) ÷ 2 + 6 = ?`'''
    },
    'solving_equations': {
        'name': 'Solving Equations',
        'level': 'Middle School',
        'description': 'Pelajari cara menyelesaikan persamaan linear',
        'content': '''# Solving Equations (Menyelesaikan Persamaan)
## Persamaan Linear: `ax + b = c`

## Langkah Penyelesaian:
1. Kelompokkan variabel di satu sisi
2. Kelompokkan konstanta di sisi lain
3. Bagi dengan koefisien variabel

## Contoh:
`2x + 3 = 7` → `2x = 4` → `x = 2`

## Latihan Soal:
1. `3x - 5 = 10`
2. `4x + 7 = 31`'''
    },
    'percentages': {
        'name': 'Percentages',
        'level': 'Middle School',
        'description': 'Pelajari konsep persentase dan aplikasinya',
        'content': '''# Percentages (Persentase)
## Rumus:
- Persentase = (Bagian / Total) × 100%
- `p%` dari angka = `(p/100) × angka`

## Contoh:
- 20% dari 80 = `20/100 × 80 = 16`
- 15 dari 60 = `(15/60) × 100% = 25%`

## Latihan Soal:
1. 30% dari 250 adalah?
2. 45 adalah berapa % dari 180?'''
    },
    'pythagorean_theorem': {
        'name': 'Pythagorean Theorem',
        'level': 'Middle School',
        'description': 'Teorema Pythagoras untuk segitiga siku-siku',
        'content': '''# Pythagorean Theorem
## Rumus: **a² + b² = c²**

## Contoh:
Jika a = 3, b = 4, maka:
c² = 9 + 16 = 25, c = 5

## Latihan Soal:
1. a = 6, b = 8, berapa c?
2. a = 5, c = 13, berapa b?'''
    },
    'quadratic_formula': {
        'name': 'Quadratic Formula',
        'level': 'High School',
        'description': 'Rumus kuadrat untuk menyelesaikan persamaan kuadrat',
        'content': '''# Quadratic Formula
## Bentuk: **ax² + bx + c = 0**

## Rumus: **x = [-b ± √(b² - 4ac)] / 2a**

## Contoh:
x² + 5x + 6 = 0 (a=1,b=5,c=6)
x = [-5 ± √(25-24)]/2 = [-5 ± 1]/2
x = -2 atau x = -3

## Latihan Soal:
1. x² + 7x + 12 = 0
2. 2x² - 4x - 6 = 0'''
    },
    'trigonometry_basics': {
        'name': 'Trigonometry Basics',
        'level': 'High School',
        'description': 'Dasar-dasar trigonometri',
        'content': '''# Trigonometry Basics
## Perbandingan:
- **sin** = depan/miring
- **cos** = samping/miring
- **tan** = depan/samping

## Sudut Istimewa:
| 0° | 30° | 45° | 60° | 90° |
| sin 0 | 1/2 | √2/2 | √3/2 | 1 |
| cos 1 | √3/2 | √2/2 | 1/2 | 0 |

## Latihan Soal:
1. sin 30° + cos 60° = ?
2. Jika sin θ = 3/5, berapa cos θ?'''
    },
    'derivatives': {
        'name': 'Derivatives',
        'level': 'College',
        'description': 'Pengenalan turunan dalam kalkulus',
        'content': '''# Derivatives (Turunan)
## Aturan Dasar:
1. d/dx (c) = 0
2. d/dx (xⁿ) = n·xⁿ⁻¹
3. d/dx (sin x) = cos x

## Contoh:
- d/dx (x³) = 3x²
- d/dx (2x² + 3x) = 4x + 3

## Latihan Soal:
1. Turunan dari f(x) = 5x⁴ adalah?
2. f(x) = 3x² - 2x + 7'''
    }
}

@app.route('/')
def index():
    if 'conversation_id' not in session:
        session['conversation_id'] = str(uuid.uuid4())
    return render_template('index.html', topics=MATH_TOPICS)

@app.route('/get_topic/<topic_id>')
def get_topic(topic_id):
    if topic_id in MATH_TOPICS:
        return jsonify({'success': True, 'topic': MATH_TOPICS[topic_id]})
    return jsonify({'success': False, 'error': 'Topic not found'}), 404

@app.route('/chat', methods=['POST'])
def chat():
    """Endpoint untuk Myrielle Chat (chatbot biasa)"""
    try:
        user_message = request.json.get('message', '')
        topic_context = request.json.get('topic_context', '')
        
        system_prompt = """Anda adalah Myrielle, asisten AI yang hangat, cerdas, dan imajinatif.
Karakteristik:
- Ramah dan suportif dalam menjelaskan konsep matematika/STEM
- Gunakan bahasa yang natural dan mudah dipahami
- Berikan contoh konkret dan langkah-langkah jelas
- Jika user salah, bimbing dengan sabar
- Gunakan format $...$ untuk rumus matematika inline, $$...$$ untuk display
        
Myrielle memiliki kepribadian: antusias, penuh rasa ingin tahu, dan selalu bersemangat membantu."""
        
        if topic_context:
            system_prompt += f"\n\nUser sedang belajar topik: {topic_context}. Berikan bantuan yang relevan."
        
        result = call_ai([
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_message}
        ])
        
        if result['success']:
            return jsonify({
                'success': True,
                'response': result['response'],
                'timestamp': datetime.now().strftime('%H:%M')
            })
        else:
            return jsonify({'success': False, 'error': result.get('error', 'Unknown error')}), 500
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/solve_question', methods=['POST'])
def solve_question():
    """Endpoint untuk Myrielle Student - menjawab soal matematika yang diupload"""
    try:
        data = request.json
        question_text = data.get('question', '')
        question_type = data.get('type', 'essay')  # 'essay' or 'multiple_choice'
        options = data.get('options', [])  # untuk pilihan ganda
        
        if not question_text:
            return jsonify({'success': False, 'error': 'Soal tidak boleh kosong'}), 400
        
        # System prompt khusus untuk menjawab soal
        if question_type == 'multiple_choice':
            system_prompt = f"""Anda adalah asisten matematika yang ahli. Tugas Anda adalah menjawab soal pilihan ganda berikut.

Soal: {question_text}
Pilihan: {', '.join(options)}

Berikan jawaban dengan format:
**Jawaban:** [huruf pilihan] - [teks pilihan]
**Penjelasan:** [penjelasan langkah demi langkah mengapa jawaban itu benar]
**Tips:** [tips memahami konsep soal ini]

Pastikan jawaban Anda akurat dan penjelasan mudah dipahami."""
        else:
            system_prompt = f"""Anda adalah asisten matematika yang ahli. Tugas Anda adalah menjawab soal essay berikut dengan lengkap.

Soal: {question_text}

Berikan jawaban dengan format:
**Jawaban:** [jawaban akhir yang jelas]
**Langkah-langkah:** 
1. [langkah pertama]
2. [langkah kedua]
...
**Kesimpulan:** [rangkuman jawaban]
**Tips Belajar:** [tips untuk memahami materi ini]

Pastikan penjelasan detail, step-by-step, dan mudah diikuti oleh siswa."""
        
        result = call_ai([
            {'role': 'system', 'content': 'Anda adalah tutor matematika yang sabar, teliti, dan menjelaskan dengan sangat jelas.'},
            {'role': 'user', 'content': system_prompt}
        ], temperature=0.3, max_tokens=2000)  # temperature lebih rendah untuk akurasi
        
        if result['success']:
            return jsonify({
                'success': True,
                'answer': result['response'],
                'question_type': question_type,
                'timestamp': datetime.now().strftime('%H:%M')
            })
        else:
            return jsonify({'success': False, 'error': result.get('error', 'Gagal memproses soal')}), 500
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
