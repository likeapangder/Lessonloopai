# Lesson Summary Agent (Legacy)

**Note:** This README documents the original Python application architecture. The current system uses a streamlined, skill-based workflow documented in `README.md`.

An autonomous AI agent that automates your post-class workflow by generating personalized lesson summaries and emailing them to students with class materials.

## Features

- 📄 **Transcript Processing**: Load from local files or Fireflies.ai
- 🤖 **AI-Powered Summarization**: Uses Google Gemini or Claude to generate structured summaries
- 🔍 **Smart Slide Retrieval**: Automatically finds relevant class slides from Google Drive
- 📧 **Beautiful Emails**: Sends HTML-formatted summary emails via Gmail
- 💻 **CLI & Web Interface**: Use from command line or browser
- 🎯 **Flexible**: Works with or without student database

## Quick Start

### 1. Installation

```bash
cd lesson-summary-agent
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configuration

```bash
# Copy example config
cp .env.example .env

# Edit .env and add your API keys
nano .env
```

Required variables:
- `GOOGLE_API_KEY` or `ANTHROPIC_API_KEY` (choose your AI provider)
- `GMAIL_SENDER_EMAIL` (your Gmail address)
- `AI_MODEL` (e.g., `gemini-1.5-pro` or `claude-3-5-sonnet-20241022`)

### 3. Google OAuth Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable APIs:
   - Gmail API
   - Google Drive API
4. Create OAuth 2.0 credentials (Desktop app)
5. Download credentials and save as `credentials.json` in the project root

### 4. Run Setup Wizard

```bash
python -m src.cli setup
```

This will:
- Validate your configuration
- Authenticate with Google (opens browser)
- Create sample `students.json` database
- Set up directory structure

### 5. Add Your Students

Edit `students.json`:

```json
{
  "students": [
    {
      "name": "John Doe",
      "email": "john@example.com",
      "level": "intermediate",
      "preferred_language": "English",
      "notes": "Focusing on business English"
    }
  ]
}
```

### 6. Process Your First Lesson

Create a transcript file:

```bash
# Filename format: YYYY-MM-DD_StudentName_Topic.txt
echo "Today we discussed present perfect tense..." > transcripts/2026-01-05_JohnDoe_Grammar.txt
```

Process it:

```bash
python -m src.cli process transcripts/2026-01-05_JohnDoe_Grammar.txt
```

## Usage

### Command Line Interface

**Process a lesson:**
```bash
python -m src.cli process <transcript-file>
python -m src.cli process transcripts/2026-01-05_JohnDoe_Grammar.txt --email john@example.com
python -m src.cli process transcripts/2026-01-05_JohnDoe_Grammar.txt --draft
```

**Preview summary (no email):**
```bash
python -m src.cli preview transcripts/2026-01-05_JohnDoe_Grammar.txt
```

**List students:**
```bash
python -m src.cli list-students
```

**List Google Drive slides:**
```bash
python -m src.cli list-slides
python -m src.cli list-slides --folder-id <your-folder-id>
```

**Setup wizard:**
```bash
python -m src.cli setup
```

### Web Interface

Launch the Gradio web app:

```bash
python -m src.web_interface
```

Then open your browser to `http://localhost:7860`

Features:
- Drag-and-drop file upload
- Preview summaries before sending
- Visual feedback and formatted output

## File Naming Convention

Transcripts should follow this naming pattern:
```
YYYY-MM-DD_StudentName_LessonTopic.txt
```

Examples:
- `2026-01-05_JohnDoe_GrammarLesson.txt`
- `2026-01-05_MarySmith_ConversationPractice.txt`

Alternative format (also supported):
```
StudentName_LessonTopic_YYYY-MM-DD.txt
```

## Project Structure

```
lesson-summary-agent/
├── src/
│   ├── __init__.py
│   ├── config.py              # Configuration management
│   ├── models.py              # Pydantic data models
│   ├── transcript_processor.py # Load and parse transcripts
│   ├── summarizer.py          # AI summarization with LangChain
│   ├── drive_client.py        # Google Drive integration
│   ├── gmail_client.py        # Gmail email sending
│   ├── agent.py               # Main workflow orchestrator
│   ├── cli.py                 # Command-line interface
│   └── web_interface.py       # Gradio web app
├── transcripts/               # Place your transcript files here
├── credentials.json           # Google OAuth credentials (you provide)
├── token.json                 # Auto-generated after first auth
├── students.json              # Student database
├── .env                       # Your configuration (you create)
├── .env.example               # Example configuration
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

## Advanced Usage

### Using Fireflies.ai Integration

If you record lessons with Fireflies:

```bash
# Set API key in .env
FIREFLIES_API_KEY=your_key_here

# Process by meeting ID
python -m src.cli process fireflies:abc123xyz456
```

### Custom Slide Organization

Set your Google Drive slides folder ID in `.env`:

```bash
SLIDES_FOLDER_ID=your_google_drive_folder_id_here
```

The agent will search within this folder for slides matching:
- Student name
- Lesson topic
- Date

### Programmatic Usage

Use the agent in your own Python code:

```python
from src.agent import LessonSummaryAgent

agent = LessonSummaryAgent()

result = agent.process_lesson(
    transcript_source="path/to/transcript.txt",
    student_email="student@example.com",
    create_draft=True,
    sender_name="Your Name"
)

print(f"Email {result['email_status']} for {result['student']}")
```

### Switching AI Models

Edit `.env`:

```bash
# Use Google Gemini
AI_MODEL=gemini-1.5-pro
GOOGLE_API_KEY=your_key

# Or use Claude
AI_MODEL=claude-3-5-sonnet-20241022
ANTHROPIC_API_KEY=your_key
```

## Troubleshooting

### "credentials.json not found"
Download OAuth credentials from Google Cloud Console (see Setup step 3).

### "No email found for student"
Either:
- Add student to `students.json`, or
- Use `--email` flag: `python -m src.cli process transcript.txt --email student@example.com`

### "Could not parse filename"
Ensure transcript filename follows format: `YYYY-MM-DD_StudentName_Topic.txt`

### "Gmail API error: insufficient permissions"
Re-run setup to re-authenticate with correct scopes:
```bash
rm token.json
python -m src.cli setup
```

### "No slides found"
- Check `SLIDES_FOLDER_ID` in `.env`
- Verify slide filenames contain student name or date
- Use `lesson-agent list-slides` to see what's in your Drive folder

## Cost Estimation

Monthly costs (assuming 20 lessons/month):

| Service | Cost |
|---------|------|
| Google Gemini 1.5 Pro API | ~$0.50 |
| Anthropic Claude API | ~$2.00 |
| Google Workspace APIs | Free |
| **Total** | **$0.50 - $2.00/month** |

## Security Notes

- Never commit `.env`, `credentials.json`, or `token.json` to version control
- Keep your API keys secure
- Use OAuth for Google APIs (not service account keys)
- Student database (`students.json`) contains email addresses - handle appropriately

## Customization

### Email Template

Edit `src/gmail_client.py`, method `_format_html_body()` to customize the email design.

### AI Prompt

Edit `src/summarizer.py`, method `_create_prompt()` to adjust how summaries are generated.

### Summary Structure

Edit `src/models.py`, class `LessonSummary` to change summary fields.

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review configuration in `.env`
3. Run setup wizard again: `python -m src.cli setup`

## License

MIT License - See LICENSE file for details

## Acknowledgments

Built with:
- [LangChain](https://langchain.com/) - LLM orchestration
- [Google Gemini](https://deepmind.google/technologies/gemini/) - AI summarization
- [Gradio](https://gradio.app/) - Web interface
- [Click](https://click.palletsprojects.com/) - CLI framework
- [Rich](https://rich.readthedocs.io/) - Terminal formatting
