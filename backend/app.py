from flask_cors import CORS
import os
import json
import logging
import subprocess
from flask import Flask, request, jsonify, render_template
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from groq import Groq
import requests
import time

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
# More permissive CORS specifically for the API route
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'mp3', 'mp4', 'mpeg', 'mpga', 'm4a', 'wav', 'webm'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/process-lesson', methods=['POST'])
def process_lesson():
    # check if the post request has the file part
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    student_name = request.form.get('student_name', 'Student')
    teacher_name = request.form.get('teacher_name', 'Teacher')

    # if user does not select file, browser also
    # submit an empty part without filename
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        try:
            # 0. Audio Compression (to bypass Groq's 25MB limit)
            logger.info("Starting audio compression...")
            try:
                compressed_filename = f"compressed_{filename.rsplit('.', 1)[0]}.mp3"
                compressed_filepath = os.path.join(app.config['UPLOAD_FOLDER'], compressed_filename)
                
                # Compress to mono 32k mp3
                command = [
                    "ffmpeg", "-i", filepath,
                    "-ac", "1", "-b:a", "32k", "-y",
                    compressed_filepath
                ]
                result = subprocess.run(command, capture_output=True, text=True)
                
                if result.returncode == 0 and os.path.exists(compressed_filepath):
                    logger.info("Compression successful!")
                    os.remove(filepath)
                    filepath = compressed_filepath
                    filename = compressed_filename
                else:
                    logger.warning(f"FFmpeg failed, using original file: {result.stderr}")
            except Exception as e:
                logger.error(f"Error during compression: {e}")

            # Step 1: Transcribe with Groq (Whisper)
            groq_api_key = os.environ.get("GROQ_API_KEY")
            if not groq_api_key:
                return jsonify({'error': 'GROQ_API_KEY is not set on the server.'}), 500
            
            logger.info(f"Transcribing file: {filename}")
            
            # Using REST API for Groq directly
            url = "https://api.groq.com/openai/v1/audio/transcriptions"
            headers = {"Authorization": f"Bearer {groq_api_key}"}
            
            with open(filepath, "rb") as file_obj:
                files = {
                    "file": (filename, file_obj),
                    "model": (None, "whisper-large-v3"),
                    "response_format": (None, "text")
                }
                groq_response = requests.post(url, headers=headers, files=files)
                
            if not groq_response.ok:
                error_msg = groq_response.json().get('error', {}).get('message', groq_response.text)
                raise Exception(f"Groq API Error: {error_msg}")
                
            transcript_text = groq_response.text

            # Step 2: Generate email with Google Gemini via REST API
            logger.info("Generating email draft with Gemini REST API")
            
            google_api_key = os.environ.get("GOOGLE_API_KEY")
            if not google_api_key:
                return jsonify({'error': 'GOOGLE_API_KEY is not set on the server.'}), 500

            # Load style guide
            style_guide = ""
            try:
                current_dir = os.path.dirname(os.path.abspath(__file__))
                style_guide_path = os.path.join(current_dir, 'templates', 'Master_EmailStyle_Guide.md')
                with open(style_guide_path, 'r') as f:
                    style_guide = f.read()
            except FileNotFoundError:
                style_guide = "Please write a summary email for the lesson. Act as an expert teaching assistant."

            prompt = f"""
            Student Name: {student_name}
            Teacher Name: {teacher_name}

            TRANSCRIPT:
            {transcript_text}
            """

            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={google_api_key}"
            payload = {
                "system_instruction": {"parts": [{"text": style_guide}]},
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.7}
            }
            headers = {"Content-Type": "application/json"}
            
            # Add simple retry logic for Gemini "High Demand" errors (503)
            max_retries = 3
            retry_delay = 2 # seconds
            
            for attempt in range(max_retries):
                gemini_response = requests.post(url, json=payload, headers=headers)
                
                if gemini_response.ok:
                    break
                    
                # If it's a 503 Service Unavailable (High Demand), wait and try again
                if gemini_response.status_code == 503 and attempt < max_retries - 1:
                    logger.warning(f"Gemini API overloaded. Retrying in {retry_delay}s... (Attempt {attempt+1}/{max_retries})")
                    time.sleep(retry_delay)
                    retry_delay *= 2 # Exponential backoff (2s, 4s)
                    continue
                    
                # If we exhausted retries or it's a different error, raise it
                error_msg = gemini_response.json().get('error', {}).get('message', gemini_response.text)
                raise Exception(f"Gemini API Error: {error_msg}")
                
            response_data = gemini_response.json()
            email_content = response_data['candidates'][0]['content']['parts'][0]['text']

            # Clean up uploaded file
            os.remove(filepath)

            return jsonify({
                'success': True,
                'email': email_content,
                'transcript_preview': str(transcript_text)[:500] + "..."
            })

        except Exception as e:
            logger.error(f"Error processing lesson: {e}")
            if os.path.exists(filepath):
                os.remove(filepath)
            
            if "Payload Too Large" in str(e) or "413" in str(e):
                return jsonify({'error': 'The file is too large for the Groq API even after compression. Please upload a shorter audio file.'}), 413
                
            return jsonify({'error': f'Processing Error: {str(e)}'}), 500

    return jsonify({'error': 'File type not allowed'}), 400

if __name__ == '__main__':
    app.run(debug=True, port=5000)
