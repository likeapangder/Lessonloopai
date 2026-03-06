# Lesson Summary Agent (Skills Edition)

A lightweight, CLI-first workflow to automate post-class summaries using Claude Code skills. This project has evolved from a complex Python application into a streamlined set of specialized tools that handle video processing, transcription, and email generation.

## 🚀 Quick Start

This workflow is designed to be simple: **Video In → Email Out**.

### Prerequisites

1.  **Claude Code**: Ensure you have the Claude CLI tool installed and authenticated.
2.  **Dependencies**: The skills rely on a few Python packages and system tools:
    ```bash
    # Install Python dependencies
    pip install faster-whisper

    # Install FFmpeg (required for video/audio processing)
    # On macOS:
    brew install ffmpeg
    ```

### The 2-Step Workflow

**Step 1: Process the Video**
Use the `/lesson-summary` skill to convert your lesson recording into a transcript. This runs locally using `ffmpeg` and `faster-whisper`.

```bash
# Basic usage
/lesson-summary <path_to_video.mp4> --to "Student Name"

# Example
/lesson-summary /Users/peggylin/Downloads/Lesson_0305.mp4 --to "Howard"
```

*What happens:*
*   Extracts audio from the video (saves to `tmp/`).
*   Transcribes audio to text using the local Whisper model.
*   Saves the transcript to `tmp/<filename>.txt`.
*   *(Optional)* Attempts to generate an email automatically if keys are configured, but **Step 2** is the recommended manual fallback for higher quality.

**Step 2: Generate & Review Email**
Use the `/lesson` skill to have Claude read the transcript and write a personalized email following your specific style guide.

```bash
/lesson tmp/<filename>.txt
```

*What happens:*
*   Claude reads the transcript and the `Master_EmailStyle_Guide.md`.
*   It generates a structured, bilingual summary email (Traditional Chinese + English).
*   You can review the output in the terminal.

**Step 3: Send (Open in Mail.app)**
Once you are happy with the text from Step 2, use the `send-email` script to open it directly in macOS Mail.

1.  Copy the email text to a file (e.g., `email_draft.txt`).
2.  Run:
    ```bash
    python3 .claude/skills/send-email/scripts/send_email.py "email_draft.txt" --type manual --to "Student Name" --subject "Lesson Summary"
    ```

---

## 🛠️ Available Skills

The system is built on these core skills located in `.claude/skills/`:

### `/lesson-summary`
**The Orchestrator.** Chains together video conversion and transcription.
*   **Input**: Video file (MP4, MOV, etc.)
*   **Output**: MP3 audio and TXT transcript.
*   **Key Flags**: `--model` (tiny/base/small/medium), `--to` (student name).

### `/lesson`
**The Writer.** A prompt-based skill that instructs Claude to act as your Teaching Assistant.
*   **Context**: Reads `templates/Master_EmailStyle_Guide.md` to ensure consistent tone and formatting.
*   **Input**: Transcript text file.
*   **Output**: Formatted email text.

### `/transcribe-audio`
**The Ear.** Standalone wrapper for `faster-whisper`.
*   **Use directly if**: You already have an audio file and just want text.
*   **Command**: `/transcribe-audio <file.mp3> --model base`

### `/send-email`
**The Courier.** Python script to bridge the CLI and macOS Mail.
*   **Function**: Creates a new draft in Mail.app with the subject, recipient, and body pre-filled.

---

## 📂 Project Structure

```
lesson-summary-agent/
├── .claude/
│   └── skills/              # The brain of the operation
│       ├── lesson-summary/  # Video -> Transcript workflow
│       ├── lesson/          # Transcript -> Email prompt
│       ├── send-email/      # Email -> Mail.app script
│       └── transcribe-audio/# Audio -> Text script
├── templates/
│   └── Master_EmailStyle_Guide.md  # The "Peggy Style" definition
├── tmp/                     # Temporary artifacts (transcripts, audio)
└── LEGACY_README.md         # Old documentation for the deprecated Python app
```

## 📝 Configuration

*   **Style Guide**: Edit `templates/Master_EmailStyle_Guide.md` to change how Claude writes your emails (tone, structure, bilingual rules).
*   **Models**: The transcription defaults to `base`. Use `--model medium` or `--model large-v3` in `/lesson-summary` for higher accuracy (slower).

## ⚠️ Troubleshooting

*   **"ffmpeg not found"**: Run `brew install ffmpeg`.
*   **"faster-whisper module not found"**: Run `pip install faster-whisper`.
*   **Mail.app doesn't open**: Ensure you are running on macOS and have granted Terminal accessibility permissions if prompted.
