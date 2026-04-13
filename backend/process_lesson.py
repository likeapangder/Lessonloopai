import os
import sys
from dotenv import load_dotenv
from groq import Groq
from google import genai
from google.genai import types

load_dotenv()

groq_api_key = os.environ.get("GROQ_API_KEY")
gemini_api_key = os.environ.get("GEMINI_API_KEY")

if not groq_api_key:
    print("Error: GROQ_API_KEY not found")
    sys.exit(1)

if not gemini_api_key:
    print("Error: GEMINI_API_KEY not found")
    sys.exit(1)

groq_client = Groq(api_key=groq_api_key)
# Initialize the new GenAI client
gemini_client = genai.Client(api_key=gemini_api_key)

def transcribe_audio(file_path):
    print(f"Transcribing {file_path} using Groq Whisper...")
    with open(file_path, "rb") as file:
        return groq_client.audio.transcriptions.create(
            file=(os.path.basename(file_path), file.read()),
            model="whisper-large-v3-turbo",
            response_format="text"
        )

def generate_summary(transcript, student_name="Student", student_email=""):
    print("Generating summary using Gemini 1.5 Pro...")

    # Load style guide
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        style_guide_path = os.path.join(current_dir, '..', 'templates', 'Master_EmailStyle_Guide.md')
        with open(style_guide_path, 'r') as f:
            style_guide = f.read()
    except FileNotFoundError:
        print("Warning: Master_EmailStyle_Guide.md not found. Using default prompt.")
        style_guide = "Act as Peggy's Executive Teaching Assistant. Write a professional lesson summary."

    # Clean user prompt
    prompt = f"""
    Student Name: {student_name}
    Student Email: {student_email}

    TRANSCRIPT:
    {transcript}
    """

    try:
        # Generate content using the new client syntax
        response = gemini_client.models.generate_content(
            model="gemini-1.5-pro",
            contents=[prompt],
            config=types.GenerateContentConfig(
                system_instruction=style_guide,
                temperature=0.7
            )
        )
        return response.text
    except Exception as e:
        print(f"Gemini Summarization Error: {e}")
        print("Falling back to Groq for summarization...")

        # Fallback to Groq if Gemini fails
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
                    "content": prompt
                }
            ],
            temperature=0.7,
            max_tokens=2048
        )
        return response.choices[0].message.content

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 process_lesson.py <audio_file_path> [student_name]")
        sys.exit(1)

    audio_file = sys.argv[1]
    student_name = sys.argv[2] if len(sys.argv) > 2 else "Student"

    if not os.path.exists(audio_file):
        print(f"File not found: {audio_file}")
        sys.exit(1)

    try:
        transcript = transcribe_audio(audio_file)
        # print("\n--- Transcript ---\n")
        # print(transcript[:500] + "...")

        summary = generate_summary(transcript, student_name=student_name)
        print("\n--- Lesson Summary ---\n")
        print(summary)

    except Exception as e:
        print(f"Error: {e}")
