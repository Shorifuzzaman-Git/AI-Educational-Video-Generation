import os
import shutil
import subprocess
from pathlib import Path
from typing import Optional


# ============================================================
# DIRECTORIES
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

GENERATED_DIR = BASE_DIR / "generated"

VIDEO_DIR = GENERATED_DIR / "videos"
RENDERED_SLIDES_DIR = GENERATED_DIR / "rendered_slides"
TEMP_DIR = GENERATED_DIR / "video_temp"

VIDEO_DIR.mkdir(
    parents=True,
    exist_ok=True
)

RENDERED_SLIDES_DIR.mkdir(
    parents=True,
    exist_ok=True
)

TEMP_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# CONFIGURATION
# ============================================================

DEFAULT_FPS = 30

DEFAULT_WIDTH = 1280
DEFAULT_HEIGHT = 720

VIDEO_CODEC = "libx264"

VIDEO_PRESET = "medium"

VIDEO_CRF = "23"

AUDIO_CODEC = "aac"

AUDIO_BITRATE = "192k"


# ============================================================
# MAIN VIDEO GENERATOR
# ============================================================

class VideoGenerator:
    """
    Convert generated PPTX slides + slide narration audio
    into an educational MP4 video.
    """

    def __init__(
        self,
        fps: int = DEFAULT_FPS,
        width: int = DEFAULT_WIDTH,
        height: int = DEFAULT_HEIGHT
    ):

        self.fps = fps

        self.width = width

        self.height = height

        self._check_dependencies()

    # ========================================================
    # CHECK DEPENDENCIES
    # ========================================================

    def _check_dependencies(self):
        """
        Check whether required system programs exist.
        """

        required = [
            "ffmpeg",
            "libreoffice",
            "pdftoppm"
        ]

        missing = []

        for command in required:

            if shutil.which(command) is None:

                missing.append(command)

        if missing:

            raise RuntimeError(
                "Missing required system programs: "
                + ", ".join(missing)
                + "\n\n"
                "Install them with:\n"
                "sudo apt install ffmpeg "
                "libreoffice poppler-utils"
            )

    # ========================================================
    # CREATE VIDEO
    # ========================================================

    def create_video(
        self,
        pptx_path: str,
        audio_files: list,
        output_filename: str = "educational_video.mp4"
    ) -> str:
        """
        Create final educational video.

        Parameters
        ----------
        pptx_path:
            Path to generated PowerPoint file.

        audio_files:
            List containing audio information.

            Example:

            [
                {
                    "slide": 1,
                    "title": "Introduction",
                    "audio_path": "generated/audio/slide_1.mp3"
                },
                {
                    "slide": 2,
                    "title": "Overview",
                    "audio_path": "generated/audio/slide_2.mp3"
                }
            ]

        output_filename:
            Name of final MP4.

        Returns
        -------
        str
            Final video path.
        """

        pptx_path = Path(pptx_path)

        if not pptx_path.exists():

            raise FileNotFoundError(
                f"PPTX file not found: {pptx_path}"
            )

        if not audio_files:

            raise ValueError(
                "No audio files provided."
            )

        print(
            "\n========================================"
        )

        print(
            "Starting video generation..."
        )

        print(
            "========================================\n"
        )

        # ----------------------------------------------------
        # Step 1: Convert PPTX to PDF
        # ----------------------------------------------------

        pdf_path = self.convert_pptx_to_pdf(
            pptx_path
        )

        # ----------------------------------------------------
        # Step 2: Convert PDF to PNG slides
        # ----------------------------------------------------

        slide_images = self.convert_pdf_to_images(
            pdf_path
        )

        if not slide_images:

            raise RuntimeError(
                "No slide images were generated."
            )

        # ----------------------------------------------------
        # Step 3: Match slides with audio
        # ----------------------------------------------------

        slide_audio_pairs = (
            self.match_slides_and_audio(
                slide_images,
                audio_files
            )
        )

        if not slide_audio_pairs:

            raise RuntimeError(
                "Could not match slides with audio."
            )

        # ----------------------------------------------------
        # Step 4: Create individual video segments
        # ----------------------------------------------------

        segment_paths = []

        for pair in slide_audio_pairs:

            slide_number = pair["slide"]

            image_path = pair["image_path"]

            audio_path = pair["audio_path"]

            segment_path = (
                TEMP_DIR
                / f"segment_{slide_number}.mp4"
            )

            print(
                f"Creating segment "
                f"{slide_number}..."
            )

            self.create_slide_segment(
                image_path=image_path,
                audio_path=audio_path,
                output_path=segment_path
            )

            segment_paths.append(
                segment_path
            )

        # ----------------------------------------------------
        # Step 5: Merge all segments
        # ----------------------------------------------------

        output_path = (
            VIDEO_DIR
            / output_filename
        )

        self.merge_segments(
            segment_paths,
            output_path
        )

        print(
            "\n========================================"
        )

        print(
            f"Video created successfully:"
        )

        print(
            output_path
        )

        print(
            "========================================\n"
        )

        return str(output_path)

    # ========================================================
    # PPTX → PDF
    # ========================================================

    def convert_pptx_to_pdf(
        self,
        pptx_path: Path
    ) -> Path:
        """
        Convert PowerPoint to PDF using LibreOffice.
        """

        output_directory = TEMP_DIR

        output_directory.mkdir(
            parents=True,
            exist_ok=True
        )

        print(
            "Converting PPTX to PDF..."
        )

        command = [
            "libreoffice",
            "--headless",
            "--convert-to",
            "pdf",
            "--outdir",
            str(output_directory),
            str(pptx_path)
        ]

        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        if result.returncode != 0:

            raise RuntimeError(
                "LibreOffice failed:\n"
                + result.stderr
            )

        pdf_path = (
            output_directory
            / f"{pptx_path.stem}.pdf"
        )

        if not pdf_path.exists():

            raise RuntimeError(
                "PDF was not created."
            )

        print(
            f"PDF created: {pdf_path}"
        )

        return pdf_path

    # ========================================================
    # PDF → PNG
    # ========================================================

    def convert_pdf_to_images(
        self,
        pdf_path: Path
    ) -> list:
        """
        Convert every PDF page into PNG.
        """

        print(
            "Converting PDF pages to images..."
        )

        output_prefix = (
            RENDERED_SLIDES_DIR
            / "slide"
        )

        # Remove previous rendered slides
        for file in RENDERED_SLIDES_DIR.glob(
            "slide-*.png"
        ):

            try:
                file.unlink()

            except Exception:
                pass

        command = [
            "pdftoppm",
            "-png",
            "-r",
            "150",
            str(pdf_path),
            str(output_prefix)
        ]

        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        if result.returncode != 0:

            raise RuntimeError(
                "PDF to image conversion failed:\n"
                + result.stderr
            )

        generated = sorted(
            RENDERED_SLIDES_DIR.glob(
                "slide-*.png"
            )
        )

        if not generated:

            raise RuntimeError(
                "No PNG slides were generated."
            )

        # Rename them to predictable names
        final_images = []

        for index, image in enumerate(
            generated,
            start=1
        ):

            final_name = (
                RENDERED_SLIDES_DIR
                / f"slide_{index}.png"
            )

            if image != final_name:

                if final_name.exists():

                    final_name.unlink()

                image.rename(
                    final_name
                )

            final_images.append(
                final_name
            )

        print(
            f"Generated {len(final_images)} slide images."
        )

        return final_images

    # ========================================================
    # MATCH SLIDES + AUDIO
    # ========================================================

    def match_slides_and_audio(
        self,
        slide_images: list,
        audio_files: list
    ) -> list:
        """
        Match slide_1.png with slide_1.mp3 etc.
        """

        audio_map = {}

        for item in audio_files:

            slide_number = item.get(
                "slide"
            )

            audio_path = item.get(
                "audio_path"
            )

            if not slide_number:
                continue

            if not audio_path:
                continue

            audio_path = Path(
                audio_path
            )

            if not audio_path.exists():

                print(
                    f"Warning: audio not found: "
                    f"{audio_path}"
                )

                continue

            audio_map[
                int(slide_number)
            ] = audio_path

        pairs = []

        for index, image_path in enumerate(
            slide_images,
            start=1
        ):

            audio_path = audio_map.get(
                index
            )

            if not audio_path:

                print(
                    f"Warning: no audio for "
                    f"slide {index}"
                )

                continue

            pairs.append(
                {
                    "slide": index,
                    "image_path": image_path,
                    "audio_path": audio_path
                }
            )

        return pairs

    # ========================================================
    # CREATE SINGLE SLIDE VIDEO
    # ========================================================

    def create_slide_segment(
        self,
        image_path: Path,
        audio_path: Path,
        output_path: Path
    ):
        """
        Create video segment from:

        PNG + MP3

        The image remains visible for the
        entire duration of the audio.
        """

        command = [
            "ffmpeg",

            "-y",

            # Image input
            "-loop",
            "1",

            "-i",
            str(image_path),

            # Audio input
            "-i",
            str(audio_path),

            # Video
            "-c:v",
            VIDEO_CODEC,

            "-preset",
            VIDEO_PRESET,

            "-crf",
            VIDEO_CRF,

            "-tune",
            "stillimage",

            # Resolution
            "-vf",
            (
                f"scale={self.width}:{self.height}:"
                "force_original_aspect_ratio=decrease,"
                f"pad={self.width}:{self.height}:"
                "(ow-iw)/2:(oh-ih)/2"
            ),

            # FPS
            "-r",
            str(self.fps),

            # Audio
            "-c:a",
            AUDIO_CODEC,

            "-b:a",
            AUDIO_BITRATE,

            # Stop when shortest input finishes
            "-shortest",

            str(output_path)
        ]

        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        if result.returncode != 0:

            raise RuntimeError(
                "FFmpeg slide segment failed:\n"
                + result.stderr
            )

        if not output_path.exists():

            raise RuntimeError(
                f"Segment was not created: "
                f"{output_path}"
            )

    # ========================================================
    # MERGE VIDEO SEGMENTS
    # ========================================================

    def merge_segments(
        self,
        segment_paths: list,
        output_path: Path
    ):
        """
        Merge all slide video segments.
        """

        if not segment_paths:

            raise ValueError(
                "No video segments."
            )

        print(
            "Merging video segments..."
        )

        concat_file = (
            TEMP_DIR
            / "concat.txt"
        )

        with open(
            concat_file,
            "w",
            encoding="utf-8"
        ) as file:

            for segment in segment_paths:

                absolute_path = (
                    segment.resolve()
                )

                # FFmpeg concat format
                file.write(
                    f"file '{absolute_path}'\n"
                )

        command = [
            "ffmpeg",

            "-y",

            "-f",
            "concat",

            "-safe",
            "0",

            "-i",
            str(concat_file),

            "-c",
            "copy",

            str(output_path)
        ]

        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        if result.returncode != 0:

            # Try re-encoding if stream copy fails
            print(
                "Stream copy failed. "
                "Trying re-encoding..."
            )

            self.merge_segments_reencode(
                segment_paths,
                output_path
            )

            return

        if not output_path.exists():

            raise RuntimeError(
                "Final video was not created."
            )

    # ========================================================
    # MERGE WITH RE-ENCODING
    # ========================================================

    def merge_segments_reencode(
        self,
        segment_paths: list,
        output_path: Path
    ):
        """
        Merge segments with video/audio re-encoding.
        """

        concat_file = (
            TEMP_DIR
            / "concat_reencode.txt"
        )

        with open(
            concat_file,
            "w",
            encoding="utf-8"
        ) as file:

            for segment in segment_paths:

                file.write(
                    f"file '{segment.resolve()}'\n"
                )

        command = [
            "ffmpeg",

            "-y",

            "-f",
            "concat",

            "-safe",
            "0",

            "-i",
            str(concat_file),

            "-c:v",
            VIDEO_CODEC,

            "-preset",
            VIDEO_PRESET,

            "-crf",
            VIDEO_CRF,

            "-c:a",
            AUDIO_CODEC,

            "-b:a",
            AUDIO_BITRATE,

            str(output_path)
        ]

        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        if result.returncode != 0:

            raise RuntimeError(
                "FFmpeg re-encoding failed:\n"
                + result.stderr
            )

        if not output_path.exists():

            raise RuntimeError(
                "Final video was not created."
            )

    # ========================================================
    # CLEAN TEMP FILES
    # ========================================================

    def cleanup(
        self,
        remove_rendered_slides: bool = False
    ):
        """
        Remove temporary video files.
        """

        print(
            "Cleaning temporary files..."
        )

        # Remove temporary files
        if TEMP_DIR.exists():

            for item in TEMP_DIR.iterdir():

                try:

                    if item.is_file():

                        item.unlink()

                    elif item.is_dir():

                        shutil.rmtree(item)

                except Exception as e:

                    print(
                        f"Could not remove "
                        f"{item}: {e}"
                    )

        # Optionally remove rendered slides
        if remove_rendered_slides:

            if RENDERED_SLIDES_DIR.exists():

                for item in (
                    RENDERED_SLIDES_DIR.iterdir()
                ):

                    try:

                        if item.is_file():

                            item.unlink()

                    except Exception:
                        pass


# ============================================================
# SIMPLE FUNCTION
# ============================================================

def create_video(
    pptx_path: str,
    audio_files: list,
    output_filename: str = "educational_video.mp4"
) -> str:
    """
    Simple function for creating a video.

    Example:

    video_path = create_video(
        "generated/slides/test.pptx",
        audio_files,
        "lesson.mp4"
    )
    """

    generator = VideoGenerator()

    return generator.create_video(
        pptx_path=pptx_path,
        audio_files=audio_files,
        output_filename=output_filename
    )


# ============================================================
# CREATE VIDEO FROM PRESENTATION DATA
# ============================================================

def create_video_from_presentation(
    pptx_path: str,
    presentation_data: dict,
    audio_files: list,
    filename: str = "educational_video.mp4"
) -> str:
    """
    Create video using PPTX + presentation data.

    The presentation_data argument is kept here because
    later you can use it for captions, slide transitions,
    metadata, or other video features.
    """

    if not presentation_data:

        raise ValueError(
            "presentation_data cannot be empty."
        )

    generator = VideoGenerator()

    return generator.create_video(
        pptx_path=pptx_path,
        audio_files=audio_files,
        output_filename=filename
    )


# ============================================================
# CLEAN GENERATED VIDEO FILES
# ============================================================

def cleanup_video_files():
    """
    Remove generated video temporary files.
    """

    generator = VideoGenerator()

    generator.cleanup(
        remove_rendered_slides=True
    )


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    print(
        "========================================"
    )

    print(
        "Video Generator Test"
    )

    print(
        "========================================"
    )

    # --------------------------------------------------------
    # Change these paths according to your generated files
    # --------------------------------------------------------

    test_pptx = (
        GENERATED_DIR
        / "slides"
        / "test_presentation.pptx"
    )

    test_audio = [

        {
            "slide": 1,
            "title": "Introduction",
            "audio_path": str(
                GENERATED_DIR
                / "audio"
                / "slide_1.mp3"
            )
        },

        {
            "slide": 2,
            "title": "Overview",
            "audio_path": str(
                GENERATED_DIR
                / "audio"
                / "slide_2.mp3"
            )
        },

        {
            "slide": 3,
            "title": "Statistics",
            "audio_path": str(
                GENERATED_DIR
                / "audio"
                / "slide_3.mp3"
            )
        },

        {
            "slide": 4,
            "title": "Process",
            "audio_path": str(
                GENERATED_DIR
                / "audio"
                / "slide_4.mp3"
            )
        },

        {
            "slide": 5,
            "title": "Conclusion",
            "audio_path": str(
                GENERATED_DIR
                / "audio"
                / "slide_5.mp3"
            )
        }

    ]

    # --------------------------------------------------------
    # Check PPTX
    # --------------------------------------------------------

    if not test_pptx.exists():

        print(
            "\nPPTX not found:"
        )

        print(
            test_pptx
        )

        print(
            "\nFirst generate the PowerPoint."
        )

        exit(1)

    # --------------------------------------------------------
    # Check audio
    # --------------------------------------------------------

    existing_audio = []

    for item in test_audio:

        audio_path = Path(
            item["audio_path"]
        )

        if audio_path.exists():

            existing_audio.append(
                item
            )

        else:

            print(
                f"Warning: missing audio: "
                f"{audio_path}"
            )

    if not existing_audio:

        print(
            "\nNo audio files found."
        )

        print(
            "Generate slide audio first."
        )

        exit(1)

    # --------------------------------------------------------
    # Generate video
    # --------------------------------------------------------

    try:

        video_path = create_video(
            pptx_path=str(
                test_pptx
            ),

            audio_files=existing_audio,

            filename="test_educational_video.mp4"
        )

        print(
            "\nVideo generated:"
        )

        print(
            video_path
        )

    except Exception as e:

        print(
            "\nVideo generation failed:"
        )

        print(
            e
        )