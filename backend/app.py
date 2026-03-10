import os
import subprocess
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import groq
import google.generativeai as genai

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'mp3', 'wav', 'm4a', 'ogg', 'flac'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/api/process-lesson', methods=['POST'])
def process_lesson():
    # Check if the post request has the file part
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    student_name = request.form.get('student_name', 'Student')
    student_email = request.form.get('student_email', '')

    # If user does not select file, browser also
    # submit an empty part without filename
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        try:
            # 0. Audio Compression using ffmpeg directly (subprocess)
            # Export as mono-channel .mp3 with low bitrate to ensure <25MB
            try:
                # Create compressed filename
                compressed_filename = f"compressed_{filename.rsplit('.', 1)[0]}.mp3"
                compressed_filepath = os.path.join(app.config['UPLOAD_FOLDER'], compressed_filename)

                # Construct ffmpeg command
                # -i input -ac 1 (mono) -b:a 32k (bitrate) -y (overwrite) output
                command = [
                    "ffmpeg",
                    "-i", filepath,
                    "-ac", "1",
                    "-b:a", "32k",
                    "-y",
                    compressed_filepath
                ]

                # Run ffmpeg
                result = subprocess.run(command, capture_output=True, text=True)

                if result.returncode == 0 and os.path.exists(compressed_filepath):
                    # Compression successful
                    # Clean up original
                    os.remove(filepath)
                    filepath = compressed_filepath
                    filename = compressed_filename
                else:
                    print(f"FFmpeg compression failed: {result.stderr}")
                    # Continue with original file

            except Exception as e:
                # If compression fails (e.g. ffmpeg issue), log it but proceed with original
                print(f"Compression failed: {e}")
                # Keep using original filepath

            # 1. Transcription with Groq
            groq_client = groq.Groq(api_key=os.environ.get("GROQ_API_KEY"))
            with open(filepath, "rb") as file_stream:
                transcription = groq_client.audio.transcriptions.create(
                    file=(filename, file_stream.read()),
                    model="whisper-large-v3",
                    response_format="text"
                )

            # 2. Summarization with Gemini
            genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
            model = genai.GenerativeModel("gemini-1.5-flash")

            # Read style guide
            try:
                # Use absolute path to ensure it works regardless of CWD
                current_dir = os.path.dirname(os.path.abspath(__file__))
                style_guide_path = os.path.join(current_dir, '..', 'templates', 'Master_EmailStyle_Guide.md')
                with open(style_guide_path, 'r') as f:
                    style_guide = f.read()
            except FileNotFoundError:
                style_guide = "Write a professional summary email."

            prompt = f"""
            You are a helpful teaching assistant. using the following style guide:
            {style_guide}

            Please write a summary email for student: {student_name}
            Student Email Address: {student_email}
            Based on the following transcript:
            {transcription}
            """

            response = model.generate_content(prompt)
            email_content = response.text

            # Clean up uploaded file
            os.remove(filepath)

            return jsonify({
                'success': True,
                'email': email_content,
                'transcript_preview': transcription[:500] + "..." if len(transcription) > 500 else transcription
            })

        except Exception as e:
            # Clean up uploaded file in case of error
            if os.path.exists(filepath):
                os.remove(filepath)
            return jsonify({'error': str(e)}), 500

    return jsonify({'error': 'File type not allowed'}), 400

if __name__ == '__main__':
    app.run(debug=True, port=5001)
