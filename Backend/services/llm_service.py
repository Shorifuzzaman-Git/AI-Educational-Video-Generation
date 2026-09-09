# ============================================================
# services/llm_service.py
# LLM Service
#
# Flow:
# Groq LLM
#     ↓
# If Groq fails
#     ↓
# Local Gemma through Ollama
# ============================================================

import os
import json
import re
import requests

from groq import Groq
from dotenv import load_dotenv


# ============================================================
# Load Environment Variables
# ============================================================

load_dotenv()


# ============================================================
# LLM Service
# ============================================================

class LLMService:

    def __init__(self):

        # ----------------------------------------------------
        # Groq Configuration
        # ----------------------------------------------------

        self.groq_api_key = os.getenv(
            "GROQ_API_KEY"
        )

        self.groq_model = os.getenv(
            "GROQ_MODEL",
            "llama-3.3-70b-versatile"
        )

        self.groq_client = None

        if self.groq_api_key:

            self.groq_client = Groq(
                api_key=self.groq_api_key
            )

        # ----------------------------------------------------
        # Ollama / Gemma Configuration
        # ----------------------------------------------------

        self.ollama_url = os.getenv(
            "OLLAMA_URL",
            "http://localhost:11434"
        )

        self.gemma_model = os.getenv(
            "GEMMA_MODEL",
            "gemma3:4b"
        )

    # ========================================================
    # Main Public Method
    # ========================================================

    def generate_slides(
        self,
        topic: str,
        slide_count: int = 5,
        research_context: str = ""
    ):
        """
        Generate structured presentation content.

        Flow:

        1. Try Groq
        2. If Groq fails -> try local Gemma
        3. Validate JSON
        4. Return presentation data
        """

        prompt = self._build_prompt(
            topic=topic,
            slide_count=slide_count,
            research_context=research_context
        )

        errors = []

        # ====================================================
        # 1. Try Groq
        # ====================================================

        try:

            print(
                f"[LLM] Trying Groq: {self.groq_model}"
            )

            result = self._generate_with_groq(
                prompt
            )

            result = self._validate_result(
                result
            )

            result["generated_by"] = "groq"
            result["model"] = self.groq_model

            print(
                "[LLM] Groq generation successful"
            )

            return result

        except Exception as e:

            error_message = (
                f"Groq failed: "
                f"{type(e).__name__}: {str(e)}"
            )

            print(
                f"[LLM] {error_message}"
            )

            errors.append(error_message)

        # ====================================================
        # 2. Fallback -> Gemma
        # ====================================================

        try:

            print(
                f"[LLM] Trying Gemma fallback: "
                f"{self.gemma_model}"
            )

            result = self._generate_with_gemma(
                prompt
            )

            result = self._validate_result(
                result
            )

            result["generated_by"] = "gemma"
            result["model"] = self.gemma_model

            print(
                "[LLM] Gemma generation successful"
            )

            return result

        except Exception as e:

            error_message = (
                f"Gemma failed: "
                f"{type(e).__name__}: {str(e)}"
            )

            print(
                f"[LLM] {error_message}"
            )

            errors.append(error_message)

        # ====================================================
        # Everything Failed
        # ====================================================

        raise RuntimeError(
            "All LLM providers failed.\n"
            + "\n".join(errors)
        )

    # ========================================================
    # Groq Generation
    # ========================================================

    def _generate_with_groq(
        self,
        prompt: str
    ):

        if self.groq_client is None:

            raise ValueError(
                "GROQ_API_KEY is not configured."
            )

        response = (
            self.groq_client
            .chat
            .completions
            .create(

                model=self.groq_model,

                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an expert educational "
                            "presentation designer and narrator. "
                            "Always return valid JSON only."
                        )
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],

                temperature=0.5,

                response_format={
                    "type": "json_object"
                }
            )
        )

        content = (
            response
            .choices[0]
            .message
            .content
        )

        if not content:

            raise ValueError(
                "Groq returned an empty response."
            )

        return self._parse_json(
            content
        )

    # ========================================================
    # Gemma Through Ollama
    # ========================================================

    def _generate_with_gemma(
        self,
        prompt: str
    ):

        url = (
            f"{self.ollama_url}/api/chat"
        )

        payload = {

            "model": self.gemma_model,

            "messages": [
                {
                    "role": "user",
                    "content": (
                        "You are an expert educational "
                        "presentation designer and narrator.\n\n"
                        "Return ONLY valid JSON.\n\n"
                        + prompt
                    )
                }
            ],

            "stream": False,

            "format": "json",

            "options": {
                "temperature": 0.5
            }
        }

        try:

            response = requests.post(
                url,
                json=payload,
                timeout=180
            )

        except requests.exceptions.ConnectionError:

            raise ConnectionError(
                "Cannot connect to Ollama. "
                "Make sure Ollama is running."
            )

        response.raise_for_status()

        data = response.json()

        if "message" not in data:

            raise ValueError(
                "Invalid response received from Ollama."
            )

        content = data["message"].get(
            "content",
            ""
        )

        if not content:

            raise ValueError(
                "Gemma returned an empty response."
            )

        return self._parse_json(
            content
        )

    # ========================================================
    # Build Prompt
    # ========================================================

    def _build_prompt(
        self,
        topic: str,
        slide_count: int,
        research_context: str
    ):

        # ----------------------------------------------------
        # Research Context
        # ----------------------------------------------------

        context_section = ""

        if research_context:

            context_section = f"""
RESEARCH CONTEXT:

Use the following information as factual grounding.

---------------- CONTEXT ----------------

{research_context}

-------------- END CONTEXT --------------

Do not invent facts that contradict the research context.
"""

        # ----------------------------------------------------
        # Main Prompt
        # ----------------------------------------------------

        prompt = f"""
Create a professional educational presentation about:

TOPIC:
{topic}

NUMBER OF SLIDES:
{slide_count}

{context_section}

You are generating content for an automated system that
will create:

1. Professional PowerPoint slides
2. Realistic images found through image search
3. Text-to-speech narration
4. An educational video


==================================================
IMPORTANT DIFFERENCE
==================================================

Every slide contains TWO different types of text.

A. SLIDE TEXT

This appears visually on the PowerPoint slide.

Slide text must:

- be short
- be concise
- avoid long paragraphs
- use important keywords
- use statistics when useful
- be easy to scan


B. NARRATION

This will NOT appear on the slide.

It will be converted to speech using text-to-speech.

Narration must:

- use complete natural sentences
- sound like a teacher presenting
- explain the slide clearly
- explain statistics instead of simply repeating them
- transition naturally between ideas
- avoid markdown
- avoid bullet symbols
- avoid saying things like "as you can see on this slide"
- be understandable without reading the slide


==================================================
NARRATION LENGTH
==================================================

Each slide narration should normally contain:

60-100 words.

This should create approximately 25-45 seconds of speech
depending on speaking speed.


==================================================
IMAGE SEARCH
==================================================

Each slide needs an image query.

The query will be sent to an external image search engine.

Good example:

"Bangladesh rice field farmer agriculture"

Bad example:

"image showing the importance of agriculture"

Image queries should:

- describe visible real-world subjects
- contain important location names when relevant
- prefer realistic photography
- be specific
- normally contain 4-10 words


==================================================
VISUAL DESIGN
==================================================

Choose a layout suitable for each slide.

Allowed layout values:

- title_hero
- image_left_content_right
- image_right_content_left
- dashboard
- statistics
- cards
- comparison
- timeline
- chart
- process
- conclusion

Do not use the same layout for every slide.


==================================================
CARDS
==================================================

Use cards only when useful.

Each card should contain:

- title
- body
- image_query

Keep card body text short.

Maximum recommended cards per slide:

4


==================================================
STATISTICS
==================================================

Statistics should contain:

- label
- value
- description

Never fabricate precise statistics.

If reliable numeric information is unavailable,
use an empty statistics array.


==================================================
CHART
==================================================

Use a chart only if numerical information genuinely
helps explain the topic.

Chart type can be:

- bar
- horizontal_bar
- pie
- donut
- line
- stacked_bar

If no chart is needed:

"chart": null


==================================================
SOURCES
==================================================

For every slide, include source_names.

If research context contains sources, use their names.

Otherwise include general source names only when you are
confident they support the information.

Never invent a URL.


==================================================
OUTPUT FORMAT
==================================================

Return ONLY valid JSON.

Do not return:

- Markdown
- explanations outside JSON
- ```json
- ```
- comments

The JSON must follow this structure:

{{
    "presentation_title": "Presentation title",

    "topic": "{topic}",

    "slides": [

        {{
            "slide_number": 1,

            "section": "Introduction",

            "title": "Slide title",

            "subtitle": "Short subtitle",

            "layout": "title_hero",

            "narration": "Natural 60-100 word narration for this slide.",

            "hero_image_query": "specific realistic image search query",

            "statistics": [],

            "cards": [],

            "chart": null,

            "key_takeaway": "One short key takeaway.",

            "source_names": []
        }}

    ]
}}


==================================================
SLIDE STRUCTURE RULES
==================================================

The presentation should have a logical educational flow.

For example:

Slide 1:
Introduction / title

Slide 2:
Basic concept / overview

Slide 3:
Important information / statistics

Slide 4:
Process / comparison / real-world application

Slide 5:
Summary / conclusion

Adapt the structure according to the topic.


==================================================
SLIDE NUMBER RULE
==================================================

Generate exactly {slide_count} slides.

Slide numbers must start at 1.

Slide numbers must be sequential:

1, 2, 3, ...

Do not generate extra slides.


==================================================
QUALITY RULES
==================================================

Make the presentation:

- educational
- accurate
- professional
- easy to understand
- visually interesting
- logically structured

Avoid:

- unnecessary repetition
- very long slide text
- fake statistics
- fake sources
- unsupported claims
- generic image queries
- excessive cards
- excessive statistics


==================================================
FINAL INSTRUCTION
==================================================

Return ONLY the JSON object.

No explanation.
No markdown.
No code fences.
"""

        return prompt

    # ========================================================
    # Parse JSON
    # ========================================================

    def _parse_json(
        self,
        content: str
    ):

        if not content:

            raise ValueError(
                "Empty LLM response."
            )

        content = content.strip()

        # ----------------------------------------------------
        # Remove Markdown Code Fence
        # ----------------------------------------------------

        content = re.sub(
            r"^```(?:json)?\s*",
            "",
            content,
            flags=re.IGNORECASE
        )

        content = re.sub(
            r"\s*```$",
            "",
            content
        )

        content = content.strip()

        # ----------------------------------------------------
        # First Attempt
        # ----------------------------------------------------

        try:

            return json.loads(
                content
            )

        except json.JSONDecodeError:
            pass

        # ----------------------------------------------------
        # Try Extracting JSON Object
        # ----------------------------------------------------

        start = content.find("{")
        end = content.rfind("}")

        if start == -1 or end == -1:

            raise ValueError(
                "No valid JSON object found in LLM response."
            )

        json_text = content[
            start:end + 1
        ]

        try:

            return json.loads(
                json_text
            )

        except json.JSONDecodeError as e:

            raise ValueError(
                f"Invalid JSON returned by LLM: {e}"
            )

    # ========================================================
    # Validate Result
    # ========================================================

    def _validate_result(
        self,
        result
    ):

        if not isinstance(result, dict):

            raise ValueError(
                "LLM result must be a JSON object."
            )

        # ----------------------------------------------------
        # Presentation Title
        # ----------------------------------------------------

        if not result.get(
            "presentation_title"
        ):

            result["presentation_title"] = (
                "Educational Presentation"
            )

        # ----------------------------------------------------
        # Topic
        # ----------------------------------------------------

        if not result.get(
            "topic"
        ):

            result["topic"] = ""

        # ----------------------------------------------------
        # Slides
        # ----------------------------------------------------

        slides = result.get(
            "slides"
        )

        if not isinstance(
            slides,
            list
        ):

            raise ValueError(
                "LLM result does not contain a valid slides list."
            )

        if not slides:

            raise ValueError(
                "LLM generated zero slides."
            )

        # ----------------------------------------------------
        # Validate Individual Slides
        # ----------------------------------------------------

        valid_slides = []

        allowed_layouts = {

            "title_hero",
            "image_left_content_right",
            "image_right_content_left",
            "dashboard",
            "statistics",
            "cards",
            "comparison",
            "timeline",
            "chart",
            "process",
            "conclusion"
        }

        for index, slide in enumerate(
            slides,
            start=1
        ):

            if not isinstance(
                slide,
                dict
            ):

                continue

            # ------------------------------------------------
            # Slide Number
            # ------------------------------------------------

            slide["slide_number"] = index

            # ------------------------------------------------
            # Basic Fields
            # ------------------------------------------------

            if not slide.get("section"):

                slide["section"] = (
                    f"Section {index}"
                )

            if not slide.get("title"):

                slide["title"] = (
                    f"Slide {index}"
                )

            if not slide.get("subtitle"):

                slide["subtitle"] = ""

            if not slide.get("narration"):

                slide["narration"] = (
                    slide["title"]
                )

            # ------------------------------------------------
            # Layout
            # ------------------------------------------------

            layout = slide.get(
                "layout",
                "image_left_content_right"
            )

            if layout not in allowed_layouts:

                layout = (
                    "image_left_content_right"
                )

            slide["layout"] = layout

            # ------------------------------------------------
            # Image Query
            # ------------------------------------------------

            if "hero_image_query" not in slide:

                slide["hero_image_query"] = ""

            if slide["hero_image_query"] is None:

                slide["hero_image_query"] = ""

            # ------------------------------------------------
            # Statistics
            # ------------------------------------------------

            if not isinstance(
                slide.get("statistics"),
                list
            ):

                slide["statistics"] = []

            # ------------------------------------------------
            # Cards
            # ------------------------------------------------

            if not isinstance(
                slide.get("cards"),
                list
            ):

                slide["cards"] = []

            # Limit cards
            slide["cards"] = slide[
                "cards"
            ][:4]

            # ------------------------------------------------
            # Chart
            # ------------------------------------------------

            if "chart" not in slide:

                slide["chart"] = None

            # ------------------------------------------------
            # Key Takeaway
            # ------------------------------------------------

            if not slide.get(
                "key_takeaway"
            ):

                slide["key_takeaway"] = ""

            # ------------------------------------------------
            # Sources
            # ------------------------------------------------

            if not isinstance(
                slide.get("source_names"),
                list
            ):

                slide["source_names"] = []

            valid_slides.append(
                slide
            )

        # ----------------------------------------------------
        # Replace With Valid Slides
        # ----------------------------------------------------

        result["slides"] = valid_slides

        if not result["slides"]:

            raise ValueError(
                "No valid slides were generated."
            )

        return result


# ============================================================
# Simple Test
# ============================================================

if __name__ == "__main__":

    print()
    print("=" * 60)
    print("LLM SERVICE TEST")
    print("=" * 60)

    service = LLMService()

    try:

        result = service.generate_slides(
            topic="How photosynthesis works",
            slide_count=5
        )

        print()
        print("Generation successful!")
        print()

        print(
            "Generated by:",
            result.get("generated_by")
        )

        print(
            "Model:",
            result.get("model")
        )

        print(
            "Presentation:",
            result.get("presentation_title")
        )

        print(
            "Slides:",
            len(result.get("slides", []))
        )

        print()
        print("Slide titles:")

        for slide in result["slides"]:

            print(
                f"{slide['slide_number']}. "
                f"{slide['title']}"
            )

        print()
        print("=" * 60)

    except Exception as e:

        print()
        print("LLM test failed:")
        print(str(e))
        print("=" * 60)