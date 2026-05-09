# LessonLoop AI

LessonLoop AI is an automated teaching assistant tool that transcribes lesson recordings and generates personalized, structured lesson summary emails for students using AI.

## Architecture

The project is split into a separated frontend and backend to allow for scalable deployment:

*   **Frontend (`lessonloop.ai/`):** A modern React application built with Vite, TypeScript, Tailwind CSS, and Radix UI components. It provides a clean drag-and-drop interface for teachers. Deployed on **Vercel**.
*   **Backend (`backend/`):** A Flask Python server that handles the heavy lifting. It processes audio/video uploads, uses **Groq (Whisper-large-v3)** for lightning-fast transcription, and uses **Anthropic (Claude 3.5 Sonnet)** to generate the final lesson summary based on a customizable style guide. Deployed on **Render** via Docker.

## Features

*   **Drag & Drop Upload:** Supports audio and video formats (MP4, MP3, WAV, M4A, WEBM, etc.).
*   **Fast Transcription:** Utilizes Groq's Whisper API to transcribe audio in seconds.
*   **Intelligent Summarization:** Claude 3.5 Sonnet generates structured emails (in Traditional Chinese/English) following a specific pedagogical style guide.
*   **1-Click Actions:** Copy the generated email to clipboard or immediately open a pre-filled Gmail draft.

## Local Development Setup

### 1. Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
pip install -r ../requirements.txt
```

Create a `.env` file in the root directory with your API keys:
```
GROQ_API_KEY=your_groq_key
ANTHROPIC_API_KEY=your_anthropic_key
FLASK_ENV=development
```

Start the Flask server:
```bash
flask run --port 5001
```

### 2. Frontend Setup

In a new terminal window:
```bash
cd lessonloop.ai
npm install
```

Create a `.env` file inside the `lessonloop.ai` folder (optional for local dev, defaults to localhost):
```
VITE_API_URL=http://127.0.0.1:5001
```

Start the Vite development server:
```bash
npm run dev
```

## Deployment Instructions

### Deploying the Backend (Render)

1. Create a new **Web Service** on Render.
2. Connect your GitHub repository.
3. Select **Docker** as the environment (Render will automatically read the `Dockerfile` in the root).
4. Add the following Environment Variables in the Render dashboard:
   * `GROQ_API_KEY`: (your key)
   * `ANTHROPIC_API_KEY`: (your key)
   * `FLASK_ENV`: `production`
5. Deploy. Render will automatically install system dependencies like `ffmpeg` and run the app using `gunicorn`.

### Deploying the Frontend (Vercel)

1. Import the repository into Vercel.
2. Under **Project Settings > General**, set the **Root Directory** to `lessonloop.ai`.
3. Under **Project Settings > Environment Variables**, add:
   * `VITE_API_URL`: `https://your-render-backend-url.onrender.com` (Ensure there is no trailing slash).
4. Deploy the project.

## Customizing the Email Style

You can modify the tone, structure, and language of the generated emails by editing the `backend/templates/Master_EmailStyle_Guide.md` file. Claude will read this file during generation and strictly adhere to its formatting rules.
