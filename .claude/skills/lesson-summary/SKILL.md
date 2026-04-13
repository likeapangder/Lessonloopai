---
name: lesson-summary
description: Complete workflow to process lesson videos - converts MP4 to MP3, transcribes audio to text, and generates email summary. Automatically chains convert-to-mp3, transcribe-audio, and send-email skills.
argument-hint: [video-file] [--model MODEL] [--to RECIPIENT] [--teacher TEACHER]
disable-model-invocation: true
allowed-tools: Bash(ffmpeg:*,python:*,open:*)
---

# Lesson Summary Workflow

Complete end-to-end workflow to process lesson videos: convert video to audio, transcribe to text, and generate email summary.

## Prerequisites

All required tools should already be installed:
- FFmpeg (for video conversion)
- faster-whisper (for transcription)
- Python 3.x

## How to use this skill

Basic usage - process video and generate lesson email:
```bash
python scripts/lesson_summary.py "$1" --to "${2:-student}" --teacher "${3:-Peggy}" --model ${4:-base}
```

**Note:** After the transcript is generated, you should run:
```bash
/lesson <transcript_path>
```
This will analyze the transcript with Claude Code and generate the personalized email.

## Parameters

- `$1` - Input MP4 video file path (required)
- `--to` - Recipient name/description (default: student)
- `--teacher` - Teacher name for lesson type (default: Peggy)
- `--model` - Whisper model: tiny, base, small, medium, large, large-v3 (default: base)
- `--type` - Email type: lesson, summary, followup, report (default: lesson)

## Workflow Steps

The skill automatically performs these steps:

1. **Convert MP4 to MP3**
   - Extracts audio from video
   - Uses high-quality settings (192kbps)
   - Saves as `[filename].mp3`

2. **Transcribe Audio to Text**
   - Uses faster-whisper for speed
   - Auto-detects language (Chinese/English)
   - Saves transcript as `[filename].txt`

3. **Generate and Send Email**
   - Creates email based on transcript
   - Follows Peggy's teaching style (for lesson type)
   - Opens in Mail.app ready to send

## Examples

**Basic lesson summary:**
```
/lesson-summary lesson-recording.mp4 --to "Siyu"
```

**With better transcription accuracy:**
```
/lesson-summary lesson-recording.mp4 --model base --to "Siyu" --teacher "Peggy"
```

**Generate report instead of lesson email:**
```
/lesson-summary meeting-recording.mp4 --type report --to "team members"
```

**Custom subject:**
```
/lesson-summary lesson.mp4 --to "Siyu" --subject "Lesson with Peggy"
```

## Output

The skill will:
1. Show progress for each step
2. Display processing time and speed
3. Save intermediate files (MP3 and TXT)
4. Open Mail.app with generated email
5. Display summary of all files created

Example output:
```
🎬 LESSON SUMMARY WORKFLOW
=====================================
Input: lesson-recording.mp4 (790 MB)

Step 1/3: Converting video to audio...
✓ MP3 created: lesson-recording.mp3 (73 MB)
  Time: 23 seconds

Step 2/3: Transcribing audio...
✓ Transcript created: lesson-recording.txt (32 KB)
  Model: tiny
  Time: 80 seconds (40x real-time)

Step 3/3: Generating email...
✓ Email generated and opened in Mail.app
  Type: lesson
  Recipient: Siyu
  Teacher: Peggy

=====================================
✅ WORKFLOW COMPLETE!

Files created:
📹 lesson-recording.mp3 (73 MB)
📝 lesson-recording.txt (32 KB)
📧 lesson-recording_email.txt (5 KB)

Total time: 1 minute 43 seconds
=====================================
```

## Performance

For a typical 53-minute lesson video:
- **Convert to MP3**: ~20-30 seconds
- **Transcribe (tiny)**: ~1-2 minutes
- **Transcribe (base)**: ~5 minutes
- **Generate email**: ~1-2 seconds
- **Total (tiny)**: ~2-3 minutes
- **Total (base)**: ~6-7 minutes

## Model Selection Guide

Choose transcription model based on needs:

- **tiny**: Fastest, good for quick drafts (~1-2 min for 53-min video)
- **base**: Good balance of speed and accuracy (~5 min) **[DEFAULT]**
- **small**: Better accuracy for important lessons (~10-15 min)
- **medium**: High accuracy, slower processing (~50+ min)
- **large**: Best quality, slowest (not recommended unless critical)

## Email Types

- **lesson** (default): Teaching summary following Peggy's style guide
- **summary**: Simple bullet-point summary
- **followup**: Follow-up email format
- **report**: Detailed report format

## File Management

By default, all files are kept:
- `[video-name].mp3` - Audio file
- `[video-name].txt` - Transcript
- `[video-name]_email.txt` - Email content

To clean up after, manually delete files or use:
```bash
rm lesson-recording.{mp3,txt,*_email.txt}
```

## Error Handling

Common issues:
- **Video file not found**: Check file path
- **FFmpeg error**: Ensure FFmpeg is installed
- **Whisper error**: Check faster-whisper installation
- **Out of memory**: Use smaller model (tiny or base)

## Tips

1. **Start with tiny model** for speed, upgrade if accuracy needed
2. **Review transcript before sending email** - you can edit the .txt file and regenerate email
3. **For long videos**, consider using base model for better accuracy
4. **Keep original MP4** - intermediate files can be regenerated

## Advanced Usage

**Manual Generation (if AI generation fails):**
If the automated email generation fails (e.g., due to API errors), you can manually generate the content using Claude Code and then open it in Mail.app:

1.  **Generate Content:**
    ```bash
    /lesson <path_to_transcript.txt>
    ```
2.  **Save Content:** Save the output to a file (e.g., `email_draft.txt`).
3.  **Open in Mail.app:**
    ```bash
    python3 .claude/skills/send-email/scripts/send_email.py "email_draft.txt" --type manual --to "Student Name" --subject "Lesson Summary"
    ```

**Process and edit before sending:**
```bash
# Run workflow but edit transcript first
/lesson-summary lesson.mp4 --to "Siyu"

# Edit the generated .txt file if needed
# Then regenerate email:
/send-email lesson.txt --type lesson --to "Siyu"
```

**Batch processing multiple lessons:**
```bash
for video in *.mp4; do
  /lesson-summary "$video" --to "Student Name"
done
```

## Integration with Other Skills

This skill combines:
- `/convert-to-mp3` - Video to audio conversion
- `/transcribe-audio` - Audio transcription
- `/send-email` - Email generation

You can still use these individually if needed.
