#!/usr/bin/env python3
"""
Quick test of faster-whisper transcription setup
"""
import sys
import os
import time
from faster_whisper import WhisperModel

def test_transcription(audio_file, model_size="tiny"):
    print(f"Testing transcription with {model_size} model")
    print(f"Audio file: {audio_file}")

    if not os.path.exists(audio_file):
        print(f"Error: File not found at {audio_file}")
        return False

    try:
        print(f"Loading {model_size} model...")
        start_time = time.time()

        model = WhisperModel(model_size, device="cpu", compute_type="float32")
        load_time = time.time() - start_time
        print(f"Model loaded in {load_time:.1f} seconds")

        print("Starting transcription...")
        transcribe_start = time.time()

        segments, info = model.transcribe(audio_file, language="zh")
        transcript = " ".join(segment.text for segment in segments)

        transcribe_time = time.time() - transcribe_start

        # Save transcript
        output_file = f"{audio_file.rsplit('.', 1)[0]}_{model_size}.txt"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(transcript)

        print(f"\n✓ Transcription completed!")
        print(f"Model: {model_size}")
        print(f"Time taken: {transcribe_time:.1f} seconds")
        print(f"Detected language: {info.language}")
        print(f"Language probability: {info.language_probability:.2f}")
        print(f"Output saved to: {output_file}")
        print(f"\nTranscript preview:")
        print("-" * 50)
        print(transcript[:300] + "..." if len(transcript) > 300 else transcript)
        print("-" * 50)

        return True

    except Exception as e:
        print(f"Error during transcription: {str(e)}")
        return False

if __name__ == "__main__":
    audio_file = "videos/Siyu.mp3"

    # Test with tiny model first (fastest download)
    print("Testing with tiny model (fastest)...")
    success = test_transcription(audio_file, "tiny")

    if success:
        print("\n" + "="*60)
        print("Tiny model test successful! Now trying base model...")
        print("="*60)
        test_transcription(audio_file, "base")