#!/usr/bin/env python3
"""
Test different language detection strategies for mixed Chinese-English content
"""
import sys
import os
import time
from faster_whisper import WhisperModel

def test_language_strategies(audio_file):
    """Test different language detection approaches"""

    if not os.path.exists(audio_file):
        print(f"Error: File not found at {audio_file}")
        return

    print("Testing different language detection strategies...")

    strategies = [
        ("auto", None),  # Let model auto-detect
        ("zh", "zh"),    # Force Chinese (current approach)
        ("en", "en"),    # Force English
    ]

    for strategy_name, lang_code in strategies:
        print(f"\n{'='*50}")
        print(f"Strategy: {strategy_name}")
        print(f"Language code: {lang_code}")
        print(f"{'='*50}")

        try:
            model = WhisperModel("base", device="cpu", compute_type="float32")

            start_time = time.time()
            if lang_code is None:
                # Auto-detect
                segments, info = model.transcribe(audio_file)
            else:
                # Force language
                segments, info = model.transcribe(audio_file, language=lang_code)

            transcript = " ".join(segment.text for segment in segments)
            transcribe_time = time.time() - start_time

            # Save transcript
            output_file = f"{audio_file.rsplit('.', 1)[0]}_{strategy_name}.txt"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(transcript)

            print(f"Detected language: {info.language}")
            print(f"Language probability: {info.language_probability:.2f}")
            print(f"Time taken: {transcribe_time:.1f} seconds")
            print(f"Output saved to: {output_file}")
            print(f"Preview (first 200 chars):")
            print("-" * 40)
            print(transcript[:200] + "..." if len(transcript) > 200 else transcript)
            print("-" * 40)

        except Exception as e:
            print(f"Error with {strategy_name}: {str(e)}")

if __name__ == "__main__":
    audio_file = "videos/Siyu.mp3"
    test_language_strategies(audio_file)