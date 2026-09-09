import asyncio
import os
import re
from pathlib import Path
from typing import Optional

import edge_tts
from dotenv import load_dotenv


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()


# ============================================================
# DIRECTORIES
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

GENERATED_DIR = BASE_DIR / "generated"
AUDIO_DIR = GENERATED_DIR / "audio"

AUDIO_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# CONFIGURATION
# ============================================================

DEFAULT_VOICE = os.getenv(
    "TTS_VOICE",
    "en-US-JennyNeural"
)

DEFAULT_RATE = os.getenv(
    "TTS_RATE",
    "+0%"
)

DEFAULT_VOLUME = os.getenv(
    "TTS_VOLUME",
    "+0%"
)

DEFAULT_PITCH = os.getenv(
    "TTS_PITCH",
    "+0Hz"
)


# ============================================================
# VOICE GENERATOR CLASS
# ============================================================

class VoiceGenerator:
    """
    Generate speech from text using Microsoft Edge TTS.
    """

    def __init__(
        self,
        voice: str = DEFAULT_VOICE,
        rate: str = DEFAULT_RATE,
        volume: str = DEFAULT_VOLUME,
        pitch: str = DEFAULT_PITCH
    ):

        self.voice = voice
        self.rate = rate
        self.volume = volume
        self.pitch = pitch

    # ========================================================
    # GENERATE SINGLE AUDIO
    # ========================================================

    async def generate_audio(
        self,
        text: str,
        output_path: str
    ) -> str:
        """
        Generate one audio file.

        Parameters
        ----------
        text : str
            Text to convert to speech.

        output_path : str
            Path where MP3 will be saved.

        Returns
        -------
        str
            Generated audio path.
        """

        if not text or not text.strip():
            raise ValueError(
                "Text cannot be empty."
            )

        output_file = Path(output_path)

        output_file.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        communicate = edge_tts.Communicate(
            text=text,
            voice=self.voice,
            rate=self.rate,
            volume=self.volume,
            pitch=self.pitch
        )

        await communicate.save(
            str(output_file)
        )

        if not output_file.exists():

            raise RuntimeError(
                f"Audio generation failed: {output_file}"
            )

        if output_file.stat().st_size == 0:

            raise RuntimeError(
                f"Generated audio file is empty: {output_file}"
            )

        print(
            f"Audio generated: {output_file}"
        )

        return str(output_file)

    # ========================================================
    # SYNCHRONOUS WRAPPER
    # ========================================================

    def generate(
        self,
        text: str,
        output_path: str
    ) -> str:
        """
        Synchronous wrapper around generate_audio().
        """

        return asyncio.run(
            self.generate_audio(
                text,
                output_path
            )
        )

    # ========================================================
    # GENERATE SLIDE AUDIO
    # ========================================================

    def generate_slide_audio(
        self,
        narration: str,
        slide_number: int
    ) -> str:
        """
        Generate audio for one slide.

        Example:

        slide_number = 1

        Result:

        generated/audio/slide_1.mp3
        """

        filename = (
            f"slide_{slide_number}.mp3"
        )

        output_path = (
            AUDIO_DIR / filename
        )

        return self.generate(
            narration,
            str(output_path)
        )

    # ========================================================
    # GENERATE ALL SLIDE AUDIO
    # ========================================================

    def generate_all_slide_audio(
        self,
        presentation_data: dict
    ) -> list:
        """
        Generate audio for every slide.

        Expected data:

        {
            "slides": [
                {
                    "title": "...",
                    "narration": "..."
                },
                ...
            ]
        }

        Returns:

        [
            {
                "slide": 1,
                "title": "...",
                "audio_path": "..."
            },
            ...
        ]
        """

        if not presentation_data:

            raise ValueError(
                "presentation_data cannot be empty."
            )

        slides = presentation_data.get(
            "slides",
            []
        )

        if not slides:

            raise ValueError(
                "No slides found."
            )

        generated_audio = []

        for index, slide in enumerate(
            slides,
            start=1
        ):

            narration = slide.get(
                "narration",
                ""
            )

            title = slide.get(
                "title",
                f"Slide {index}"
            )

            if not narration:

                print(
                    f"Warning: No narration for slide {index}"
                )

                continue

            try:

                audio_path = (
                    self.generate_slide_audio(
                        narration=narration,
                        slide_number=index
                    )
                )

                generated_audio.append(
                    {
                        "slide": index,
                        "title": title,
                        "audio_path": audio_path
                    }
                )

            except Exception as e:

                print(
                    f"Failed to generate audio "
                    f"for slide {index}: {e}"
                )

        return generated_audio

    # ========================================================
    # GENERATE COMPLETE NARRATION
    # ========================================================

    def generate_complete_narration(
        self,
        presentation_data: dict,
        filename: str = "complete_narration.mp3"
    ) -> str:
        """
        Combine all slide narrations into one MP3.

        This generates one continuous audio file.

        Note:
        For your video pipeline, individual slide audio
        files are usually more useful.
        """

        slides = presentation_data.get(
            "slides",
            []
        )

        narration_parts = []

        for slide in slides:

            narration = slide.get(
                "narration",
                ""
            )

            if narration:

                narration_parts.append(
                    narration.strip()
                )

        if not narration_parts:

            raise ValueError(
                "No narration found."
            )

        complete_text = " ".join(
            narration_parts
        )

        output_path = (
            AUDIO_DIR / filename
        )

        return self.generate(
            complete_text,
            str(output_path)
        )


# ============================================================
# SIMPLE FUNCTION
# ============================================================

def generate_voice(
    text: str,
    filename: str = "voice.mp3",
    voice: str = DEFAULT_VOICE
) -> str:
    """
    Simple function for generating one voice file.

    Example:

    generate_voice(
        "Hello, welcome to this lesson.",
        "hello.mp3"
    )
    """

    output_path = (
        AUDIO_DIR / filename
    )

    generator = VoiceGenerator(
        voice=voice
    )

    return generator.generate(
        text=text,
        output_path=str(output_path)
    )


# ============================================================
# GENERATE VOICE FROM PRESENTATION JSON
# ============================================================

def generate_slide_voices(
    presentation_data: dict,
    voice: str = DEFAULT_VOICE
) -> list:
    """
    Generate one MP3 for every slide.
    """

    generator = VoiceGenerator(
        voice=voice
    )

    return generator.generate_all_slide_audio(
        presentation_data
    )


# ============================================================
# ESTIMATE AUDIO DURATION
# ============================================================

def estimate_speech_duration(
    text: str,
    words_per_minute: int = 150
) -> float:
    """
    Estimate speech duration in seconds.

    This is only an approximation.

    Example:

    150 words ≈ 60 seconds
    """

    if not text:

        return 0.0

    words = len(
        text.split()
    )

    duration = (
        words / words_per_minute
    ) * 60

    return round(
        duration,
        2
    )


# ============================================================
# SANITIZE TEXT
# ============================================================

def clean_narration(
    text: str
) -> str:
    """
    Clean narration before sending it to TTS.
    """

    if not text:

        return ""

    text = str(text)

    # Remove markdown code blocks
    text = re.sub(
        r"```.*?```",
        "",
        text,
        flags=re.DOTALL
    )

    # Remove markdown headings
    text = re.sub(
        r"^#+\s*",
        "",
        text,
        flags=re.MULTILINE
    )

    # Remove excessive spaces
    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    print("=" * 40)
    print("Voice Generator Test")
    print("=" * 40)

    # Import test data from slide_generator
    from services.slide_generator import test_data

    # Create voice generator
    generator = VoiceGenerator()

    # Generate audio for every slide
    audio_files = generator.generate_all_slide_audio(
        presentation_data=test_data
    )

    print()
    print("=" * 40)
    print("Generated Audio Files")
    print("=" * 40)

    for audio in audio_files:

        print(
            f"Slide {audio['slide']}: "
            f"{audio['audio_path']}"
        )

    print()
    print(
        f"Total audio files generated: "
        f"{len(audio_files)}"
    )