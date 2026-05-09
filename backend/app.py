from flask_cors import CORS
import os
import json
import logging
from flask import Flask, request, jsonify, render_template
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from groq import Groq
from google import genai
from google.genai import types

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'mp3', 'mp4', 'mpeg', 'mpga', 'm4a', 'wav', 'webm'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize API clients
try:
    groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
    # Note: google-genai reads GOOGLE_API_KEY directly from env
    gemini_client = genai.Client()
except Exception as e:
    logger.error(f"Failed to initialize API clients: {e}")

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
            # Step 1: Transcribe with Groq (Whisper)
            logger.info(f"Transcribing file: {filename}")
            with open(filepath, "rb") as file_obj:
                transcription = groq_client.audio.transcriptions.create(
                    file=(filename, file_obj.read()),
                    model="whisper-large-v3",
                    response_format="text"
                )

            # Step 2: Generate email with Google Gemini
            logger.info("Generating email draft with Gemini")

            # Load style guide
            style_guide = ""
            try:
                # Need to use absolute path or relative from backend/
                current_dir = os.path.dirname(os.path.abspath(__file__))
                style_guide_path = os.path.join(current_dir, 'templates', 'Master_EmailStyle_Guide.md')
                with open(style_guide_path, 'r') as f:
                    style_guide = f.read()
            except FileNotFoundError:
                logger.warning("Style guide not found, using default prompt")
                style_guide = "Please write a summary email for the lesson. Act as an expert teaching assistant."

            prompt = f"""
            Student Name: {student_name}
            Teacher Name: {teacher_name}

            TRANSCRIPT:
            {transcription}
            """

            response = gemini_client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[prompt],
                config=types.GenerateContentConfig(
                    system_instruction=style_guide,
                    temperature=0.7
                )
            )

            email_content = response.text

            # Clean up uploaded file
            os.remove(filepath)

            return jsonify({
                'success': True,
                'email': email_content,
                'transcript_preview': str(transcription)[:500] + "..."
            })

        except Exception as e:
            logger.error(f"Error processing lesson: {e}")
            # Clean up file in case of error
            if os.path.exists(filepath):
                os.remove(filepath)
            return jsonify({'error': str(e)}), 500

    return jsonify({'error': 'File type not allowed'}), 400

if __name__ == '__main__':
    app.run(debug=True, port=5000)
