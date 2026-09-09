# ============================================================
# main.py
# AI Educational Video Generation API
# ============================================================

from pathlib import Path
from typing import Optional
import uuid
import traceback

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

# ============================================================
# Import Services
# ============================================================

from services.llm_service import LLMService
from services.slide_generator import create_slides
from services.voice_generate import generate_slide_voices
from services.video_generator import create_video


# ============================================================
# Base Directory
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

GENERATED_DIR = BASE_DIR / "generated"

SLIDES_DIR = GENERATED_DIR / "slides"
AUDIO_DIR = GENERATED_DIR / "audio"
VIDEO_DIR = GENERATED_DIR / "videos"

# Create directories if they don't exist
GENERATED_DIR.mkdir(parents=True, exist_ok=True)
SLIDES_DIR.mkdir(parents=True, exist_ok=True)
AUDIO_DIR.mkdir(parents=True, exist_ok=True)
VIDEO_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# FastAPI App
# ============================================================

app = FastAPI(
    title="AI Educational Video Generator",
    description="Generate educational videos from a user prompt using LLM, images, TTS and FFmpeg.",
    version="1.0.0"
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# Static Files
# ============================================================

# This allows generated files to be accessed from browser.
#
# Example:
# http://127.0.0.1:8000/generated/videos/video.mp4

app.mount(
    "/generated",
    StaticFiles(directory=str(GENERATED_DIR)),
    name="generated"
)


# ============================================================
# Request Model
# ============================================================

class VideoRequest(BaseModel):

    # User's topic/prompt
    prompt: str = Field(
        ...,
        min_length=3,
        description="Topic or prompt for the educational video"
    )

    # Number of slides
    slide_count: int = Field(
        default=5,
        ge=3,
        le=15,
        description="Number of slides to generate"
    )

    # Optional research context
    research_context: Optional[str] = Field(
        default="",
        description="Optional research information to give the LLM"
    )


# ============================================================
# Response Model
# ============================================================

class VideoResponse(BaseModel):

    success: bool

    message: str

    video_url: Optional[str] = None

    pptx_url: Optional[str] = None

    audio_files: list[str] = []

    generated_by: Optional[str] = None

    model: Optional[str] = None


# ============================================================
# Initialize LLM Service
# ============================================================

llm_service = LLMService()


# ============================================================
# Root Endpoint
# ============================================================

@app.get("/")
def home():

    return {
        "message": "AI Educational Video Generator API",
        "status": "running",
        "docs": "/docs",
        "generate_video": "POST /generate-video"
    }


# ============================================================
# Health Check
# ============================================================

@app.get("/health")
def health_check():

    return {
        "status": "healthy",
        "service": "AI Educational Video Generator"
    }


# ============================================================
# Generate Video
# ============================================================

@app.post(
    "/generate-video",
    response_model=VideoResponse
)
def generate_video(request: VideoRequest):

    """
    Complete video generation pipeline.

    User Prompt
        ↓
    LLM
        ↓
    Structured Lesson
        ↓
    PPTX Slides
        ↓
    Edge TTS
        ↓
    FFmpeg
        ↓
    MP4 Video
    """

    # --------------------------------------------------------
    # Create unique ID
    # --------------------------------------------------------

    job_id = uuid.uuid4().hex[:8]

    print()
    print("=" * 70)
    print("AI EDUCATIONAL VIDEO GENERATION")
    print("=" * 70)
    print(f"Job ID       : {job_id}")
    print(f"Prompt       : {request.prompt}")
    print(f"Slide Count  : {request.slide_count}")
    print("=" * 70)


    try:

        # ====================================================
        # STEP 1 — Generate Lesson Using LLM
        # ====================================================

        print()
        print("[1/4] Generating educational content using LLM...")

        presentation_data = llm_service.generate_slides(
            topic=request.prompt,
            slide_count=request.slide_count,
            research_context=request.research_context or ""
        )

        if not presentation_data:

            raise Exception(
                "LLM did not return presentation data."
            )

        print("✓ LLM content generated")


        # ====================================================
        # STEP 2 — Generate PowerPoint Slides
        # ====================================================

        print()
        print("[2/4] Creating PowerPoint slides...")

        pptx_filename = (
            f"{safe_filename(request.prompt)}_{job_id}.pptx"
        )

        pptx_path = create_slides(
            presentation_data,
            pptx_filename
        )

        if not pptx_path:

            raise Exception(
                "PowerPoint generation failed."
            )

        pptx_path = Path(pptx_path)

        if not pptx_path.exists():

            raise Exception(
                f"PPTX file was not created: {pptx_path}"
            )

        print(f"✓ PPTX created: {pptx_path}")


        # ====================================================
        # STEP 3 — Generate Voice For Every Slide
        # ====================================================

        print()
        print("[3/4] Generating slide narration using Edge TTS...")

        audio_results = generate_slide_voices(
            presentation_data
        )

        if not audio_results:
            raise Exception(
                "No audio files were generated."
            )

        # ----------------------------------------------------
        # Convert audio results into the format expected
        # by video_generator.py
        # ----------------------------------------------------

        audio_files = []

        for index, item in enumerate(
            audio_results,
            start=1
        ):
            

            # generate_slide_voices() may return either:
            #   1. dictionary
            #   2. string path

            if isinstance(item, dict):

                    audio_path = item.get(
                    "audio_path"
                    )

                    slide_number = item.get(
                    "slide",
                    index
                )

                    title = item.get(
                    "title",
                    ""
            )

            else:

                audio_path = item

                slide_number = index

                title = ""

            if not audio_path: 
                continue

                audio_path = Path(
                    audio_path
                )
            audio_path=Path(audio_path)
            if not audio_path.exists():
                
                print(
                    f"⚠ Audio file does not exist: "
                    f"{audio_path}"
                )

                continue

        # IMPORTANT:
        # VideoGenerator expects dictionaries,
        # NOT strings.
            audio_files.append(
                {
                    "slide": int(slide_number),
                    "title": title,
                    "audio_path": str(audio_path)
                }
            )

            print(
                f"✓ Slide {slide_number} audio: "
                f"{audio_path.name}"
            )


            if not audio_files:

                raise Exception(
                "Audio generation completed but no "
                "audio files were found."
            )

        print(
            f"✓ Generated {len(audio_files)} audio files"
        )



        # ====================================================
        # STEP 4 — Generate Final Video
        # ====================================================

        print()
        print("[4/4] Creating final MP4 video using FFmpeg...")

        video_filename = (
            f"{safe_filename(request.prompt)}_{job_id}.mp4"
        )

        video_path = create_video(
            pptx_path=str(pptx_path),
            audio_files=audio_files,
            output_filename=video_filename
        )

        if not video_path:

            raise Exception(
                "Video generation failed."
            )

        video_path = Path(video_path)

        if not video_path.exists():

            raise Exception(
                f"Video file was not created: {video_path}"
            )

        print(f"✓ Video created: {video_path}")


        # ====================================================
        # Create URLs
        # ====================================================

        video_url = make_generated_url(
            video_path
        )

        pptx_url = make_generated_url(
            pptx_path
        )

        audio_urls = []

        for audio_file in audio_files:

            audio_path = audio_file.get("audio_path")

            if not audio_path:
                continue

            audio_path = Path(audio_path)

            audio_urls.append(
                make_generated_url(audio_path)
            )


        # ====================================================
        # Get LLM Information
        # ====================================================

        generated_by = presentation_data.get(
            "generated_by"
        )

        model = presentation_data.get(
            "model"
        )


        # ====================================================
        # Success
        # ====================================================

        print()
        print("=" * 70)
        print("VIDEO GENERATION COMPLETE")
        print("=" * 70)
        print(f"Video : {video_path}")
        print(f"URL   : {video_url}")
        print("=" * 70)
        print()


        return VideoResponse(

            success=True,

            message=(
                "Educational video generated successfully."
            ),

            video_url=video_url,

            pptx_url=pptx_url,

            audio_files=audio_urls,

            generated_by=generated_by,

            model=model
        )


    except Exception as e:

        # ====================================================
        # Error Handling
        # ====================================================

        print()
        print("=" * 70)
        print("VIDEO GENERATION ERROR")
        print("=" * 70)

        print(f"Error: {str(e)}")

        traceback.print_exc()

        print("=" * 70)
        print()

        raise HTTPException(
            status_code=500,
            detail={
                "message": "Video generation failed.",
                "error": str(e),
                "job_id": job_id
            }
        )


# ============================================================
# Utility Functions
# ============================================================

def safe_filename(text: str) -> str:

    """
    Convert user prompt into a safe filename.
    """

    import re

    text = text.lower().strip()

    # Replace spaces with underscores
    text = text.replace(" ", "_")

    # Remove unsafe characters
    text = re.sub(
        r"[^a-zA-Z0-9_\-]",
        "",
        text
    )

    # Limit filename length
    text = text[:50]

    if not text:

        text = "educational_video"

    return text


def make_generated_url(file_path: Path) -> str:

    """
    Convert:

    generated/videos/example.mp4

    into:

    /generated/videos/example.mp4
    """

    try:

        relative_path = file_path.relative_to(
            GENERATED_DIR
        )

    except ValueError:

        relative_path = file_path

    return (
        "/generated/"
        + relative_path.as_posix()
    )


# ============================================================
# Run Application
# ============================================================

if __name__ == "__main__":

    import uvicorn

    print()
    print("=" * 70)
    print("AI EDUCATIONAL VIDEO GENERATOR")
    print("=" * 70)
    print("Starting FastAPI server...")
    print()
    print("API:")
    print("http://127.0.0.1:8000")
    print()
    print("Swagger:")
    print("http://127.0.0.1:8000/docs")
    print()
    print("Generate Video:")
    print("POST http://127.0.0.1:8000/generate-video")
    print("=" * 70)
    print()

    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )