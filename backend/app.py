import os
import subprocess
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import groq
from google import genai
from google.genai import types

# Load environment variables
load_dotenv()

app = Flask(__name__)
# Increase max upload size to 100MB
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024
CORS(app)

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'mp3', 'wav', 'm4a', 'ogg', 'flac', 'mp4', 'mov', 'webm', 'mpeg', 'mpga'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return jsonify({"status": "healthy", "message": "LessonLoop API is running"})

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
    teacher_name = request.form.get('teacher_name', 'Teacher')

    # If user does not select file, browser also
    # submit an empty part without filename
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Log file size
        file_size = os.path.getsize(filepath)
        print(f"File uploaded: {filename}, Size: {file_size} bytes")

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
            print("Starting Groq transcription...")
            try:
                groq_client = groq.Groq(api_key=os.environ.get("GROQ_API_KEY"))
                with open(filepath, "rb") as file_stream:
                    transcription = groq_client.audio.transcriptions.create(
                        file=(filename, file_stream.read()),
                        model="whisper-large-v3-turbo",
                        response_format="text"
                    )
                print("Groq transcription complete.")
                print(f"Transcript Preview (500 chars):\n{transcription[:500]}")
            except Exception as e:
                print(f"Groq API Error: {e}")
                raise e

            # 2. Summarization with Gemini (Using Peggy Style)
            print("Starting Gemini summarization...")
            try:
                gemini_client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

                # Read style guide
                try:
                    current_dir = os.path.dirname(os.path.abspath(__file__))
                    style_guide_path = os.path.join(current_dir, '..', 'templates', 'Master_EmailStyle_Guide.md')
                    if os.path.exists(style_guide_path):
                        print(f"Loading style guide from: {style_guide_path}")
                        with open(style_guide_path, 'r') as f:
                            style_guide = f.read()
                        print(f"Style guide loaded (length: {len(style_guide)} chars)")
                    else:
                         print(f"Warning: Style guide NOT found at {style_guide_path}")
                         raise FileNotFoundError
                except FileNotFoundError:
                    style_guide = "Act as Peggy's Executive Teaching Assistant. Write a professional lesson summary."

                # Prompt contains ONLY the student info and transcript
                prompt = f"""
                Student Name: {student_name}
                Student Email: {student_email}
                Teacher Name: {teacher_name}

                TRANSCRIPT:
                {transcription}
                """

                # Generate content using the new client syntax
                response = gemini_client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=[prompt],
                    config=types.GenerateContentConfig(
                        system_instruction=style_guide,
                        temperature=0.7
                    )
                )

                email_content = response.text
                print("Gemini summarization complete.")
            except Exception as e:
                print(f"Gemini Summarization Error: {e}")
                # Fallback to Groq if Gemini fails
                print("Falling back to Groq for summarization...")
                try:
                    groq_client = groq.Groq(api_key=os.environ.get("GROQ_API_KEY"))

                    response = groq_client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[
                            {
                                "role": "system",
                                "content": f"""You are Peggy's Executive Teaching Assistant.
Your task is to write a lesson summary email for a student based on the provided transcript.

CRITICAL INSTRUCTIONS:
1. You MUST use the exact format defined in the Style Guide below.
2. Do NOT just copy the examples in the style guide. Use the structure, but fill it with content from the TRANSCRIPT.
3. The content must be specific to the lesson in the transcript (e.g., if they talked about "cooking", mention cooking, not "bad habits" from the example).
4. Write in Traditional Chinese for the narrative parts, and English for the key terms/titles as specified.

STYLE GUIDE:
{style_guide}
"""
                            },
                            {
                                "role": "user",
                                "content": f"Please write a summary email for student: {student_name}\nStudent Email Address: {student_email}\nTeacher Name: {teacher_name}\n\nBased on the following transcript:\n{transcription}"
                            }
                        ],
                        temperature=0.7,
                        max_tokens=2048
                    )
                    email_content = response.choices[0].message.content
                    print("Groq summarization complete (fallback).")
                except Exception as groq_e:
                    print(f"Groq Summarization Error: {groq_e}")
                    raise e

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
