from flask_cors import CORS
import os
import json
import logging
import subprocess
import threading
import uuid
import time
from flask import Flask, request, jsonify, render_template
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from groq import Groq
import requests

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
RESULTS_FOLDER = 'results'
ALLOWED_EXTENSIONS = {'mp3', 'mp4', 'mpeg', 'mpga', 'm4a', 'wav', 'webm'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size

# Ensure directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULTS_FOLDER, exist_ok=True)

# In-memory task tracker (In a real production app, use Redis/Postgres)
# { "task_id": {"status": "processing", "progress": 10, "result": None, "error": None} }
tasks = {}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def process_lesson_background(task_id, filepath, original_filename, student_name, teacher_name, groq_api_key, google_api_key):
    """Background worker thread to handle the heavy lifting without blocking the HTTP request."""
    try:
        tasks[task_id]['status'] = 'compressing'
        tasks[task_id]['progress'] = 10
        
        # 0. Audio Compression
        logger.info(f"Task {task_id}: Starting audio compression...")
        filename = original_filename
        try:
            compressed_filename = f"compressed_{uuid.uuid4().hex[:8]}_{filename.rsplit('.', 1)[0]}.mp3"
            compressed_filepath = os.path.join(app.config['UPLOAD_FOLDER'], compressed_filename)
            
            # Compress to mono 32k mp3
            command = [
                "ffmpeg", "-i", filepath,
                "-ac", "1", "-b:a", "32k", "-y",
                compressed_filepath
            ]
            result = subprocess.run(command, capture_output=True, text=True)
            
            if result.returncode == 0 and os.path.exists(compressed_filepath):
                logger.info(f"Task {task_id}: Compression successful!")
                os.remove(filepath)
                filepath = compressed_filepath
                filename = compressed_filename
            else:
                logger.warning(f"Task {task_id}: FFmpeg failed, using original file: {result.stderr}")
        except Exception as e:
            logger.error(f"Task {task_id}: Error during compression: {e}")

        tasks[task_id]['status'] = 'transcribing'
        tasks[task_id]['progress'] = 40

        # Step 1: Transcribe with Groq (Whisper)
        logger.info(f"Task {task_id}: Transcribing file: {filename}")
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

        tasks[task_id]['status'] = 'generating_email'
        tasks[task_id]['progress'] = 75

        # Step 2: Generate email with Google Gemini via REST API
        logger.info(f"Task {task_id}: Generating email draft with Gemini REST API")
        
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
                
            if gemini_response.status_code == 503 and attempt < max_retries - 1:
                logger.warning(f"Task {task_id}: Gemini API overloaded. Retrying in {retry_delay}s... (Attempt {attempt+1}/{max_retries})")
                time.sleep(retry_delay)
                retry_delay *= 2 
                continue
                
            error_msg = gemini_response.json().get('error', {}).get('message', gemini_response.text)
            raise Exception(f"Gemini API Error: {error_msg}")
            
        response_data = gemini_response.json()
        email_content = response_data['candidates'][0]['content']['parts'][0]['text']

        # Clean up uploaded file
        if os.path.exists(filepath):
            os.remove(filepath)

        # Mark task as complete
        tasks[task_id]['status'] = 'completed'
        tasks[task_id]['progress'] = 100
        tasks[task_id]['result'] = {
            'email': email_content,
            'transcript_preview': str(transcript_text)[:500] + "..."
        }
        
        # Save to disk as a backup (in case memory gets wiped, though Render containers reset on deploy)
        with open(os.path.join(RESULTS_FOLDER, f"{task_id}.json"), 'w') as f:
            json.dump(tasks[task_id], f)

    except Exception as e:
        logger.error(f"Task {task_id}: Error processing lesson: {e}")
        if os.path.exists(filepath):
            os.remove(filepath)
        
        tasks[task_id]['status'] = 'failed'
        tasks[task_id]['progress'] = 0
        
        if "Payload Too Large" in str(e) or "413" in str(e):
            tasks[task_id]['error'] = 'The file is too large for the transcription API even after compression. Please upload a shorter audio file.'
        else:
            tasks[task_id]['error'] = f'Processing Error: {str(e)}'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/process-lesson', methods=['POST'])
def process_lesson():
    """Endpoint to ACCEPT the upload and start the background task."""
    groq_api_key = os.environ.get("GROQ_API_KEY")
    google_api_key = os.environ.get("GOOGLE_API_KEY")
    
    if not groq_api_key:
        return jsonify({'error': 'GROQ_API_KEY is not set on the server.'}), 500
    if not google_api_key:
        return jsonify({'error': 'GOOGLE_API_KEY is not set on the server.'}), 500

    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    student_name = request.form.get('student_name', 'Student')
    teacher_name = request.form.get('teacher_name', 'Teacher')

    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # Add uuid to filename to prevent collisions between concurrent users
        task_id = str(uuid.uuid4())
        unique_filename = f"{task_id}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(filepath)

        # Initialize the task status
        tasks[task_id] = {
            'status': 'queued',
            'progress': 0,
            'result': None,
            'error': None
        }

        # Start the background thread
        thread = threading.Thread(
            target=process_lesson_background, 
            args=(task_id, filepath, filename, student_name, teacher_name, groq_api_key, google_api_key)
        )
        thread.daemon = True
        thread.start()

        # Return IMMEDIATELY so Render doesn't timeout!
        return jsonify({
            'success': True,
            'task_id': task_id,
            'message': 'Upload successful. Processing started in background.'
        })

    return jsonify({'error': 'File type not allowed'}), 400

@app.route('/api/status/<task_id>', methods=['GET'])
def get_status(task_id):
    """Endpoint for the frontend to poll for task status."""
    task = tasks.get(task_id)
    
    if not task:
        # Check if we saved it to disk
        try:
            with open(os.path.join(RESULTS_FOLDER, f"{task_id}.json"), 'r') as f:
                task = json.load(f)
        except FileNotFoundError:
            return jsonify({'error': 'Task not found or expired'}), 404
            
    return jsonify(task)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
