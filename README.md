# 🎓 AI-Powered Educational Video Generation System

An AI-powered educational content generation platform that transforms a user's topic or prompt into a complete educational video automatically.

The system uses **Large Language Models (LLMs)** to generate structured lesson content, creates presentation slides with relevant images, generates voice narration, combines the slides and narration into a video, and produces supplementary quiz questions and PDF notes.

---

## 📌 Project Overview

Creating educational videos manually requires significant time for:

* Researching a topic
* Writing lesson content
* Preparing presentation slides
* Finding suitable images
* Recording narration
* Editing video
* Creating quizzes
* Preparing study notes

This project automates these tasks using Artificial Intelligence.

### Basic Workflow

```text
User Prompt
     │
     ▼
┌──────────────────────┐
│   LLM Content        │
│   Generation         │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ Structured Lesson    │
│ Content Generation   │
└──────────┬───────────┘
           │
           ├─────────────────┐
           ▼                 ▼
┌──────────────────┐  ┌──────────────────┐
│ Slide Generation │  │ Quiz Generation  │
└────────┬─────────┘  └──────────────────┘
         │
         ▼
┌──────────────────┐
│ Image Search /   │
│ Slide Visuals    │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Voice Narration  │
│ Generation       │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Video Generation │
│ + Audio + Slides │
└────────┬─────────┘
         │
         ▼
┌────────────────────────────┐
│ Educational Video + Quiz   │
│ + PDF Study Notes          │
└────────────────────────────┘
```

---

# ✨ Key Features

## 🤖 AI Lesson Generation

The user provides a topic or educational prompt.

Example:

```text
Explain Convolutional Neural Networks for beginners.
```

The LLM generates structured educational content including:

* Title
* Introduction
* Learning objectives
* Main concepts
* Explanations
* Examples
* Summary
* Quiz questions

---

## 🖼️ Automatic Slide Generation

The generated lesson is automatically converted into presentation slides.

Each slide can contain:

* Slide title
* Key points
* Explanations
* Relevant images
* Educational visual content

Slides are generated programmatically using Python.

---

## 🔎 Image Search

The system can search for relevant images based on the generated lesson content.

The images are then used as visual elements in the generated educational slides.

---

## 🗣️ AI Voice Narration

The generated lesson content is converted into speech automatically.

The system generates audio narration for the educational content and associates the narration with the corresponding slides.

---

## 🎬 Automatic Video Generation

The generated slides and voice narration are combined to create an educational video.

The video generation pipeline handles:

* Slide rendering
* Audio generation
* Audio/video synchronization
* Slide timing
* Video encoding

---

# 🏗️ System Architecture

```text
                    ┌─────────────────┐
                    │      User       │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │   React Frontend│
                    └────────┬────────┘
                             │
                             │ HTTP/API
                             ▼
                    ┌─────────────────┐
                    │    FastAPI      │
                    │     Backend     │
                    └────────┬────────┘
                             │
             ┌───────────────┼────────────────┐
             │               │                │
             ▼               ▼                ▼
      ┌─────────────┐ ┌──────────────┐ ┌──────────────┐
      │ LLM Service │ │ Image Search │ │ Quiz/Notes   │
      └──────┬──────┘ └──────┬───────┘ └──────┬───────┘
             │               │                │
             ▼               ▼                ▼
      ┌─────────────┐ ┌──────────────┐ ┌──────────────┐
      │   Lesson    │ │    Images    │ │ Quiz + PDF   │
      │   Content   │ │              │ │    Output    │
      └──────┬──────┘ └──────┬───────┘ └──────────────┘
             │               │
             └───────┬───────┘
                     ▼
             ┌─────────────────┐
             │ Slide Generator │
             └────────┬────────┘
                      │
                      ▼
             ┌─────────────────┐
             │ Voice Generator │
             └────────┬────────┘
                      │
                      ▼
             ┌─────────────────┐
             │ Video Generator │
             └────────┬────────┘
                      │
                      ▼
             ┌─────────────────┐
             │ Educational     │
             │ Video           │
             └─────────────────┘
```

---

# 🛠️ Technology Stack

## Frontend

* React
* Vite
* Tailwind CSS
* JavaScript
* HTML5
* CSS3

## Backend

* Python
* FastAPI
* Pydantic

## Artificial Intelligence

* Large Language Models (LLMs)
* Google Gemini API
* Groq API
* Ollama
* Local LLM models

## Slide Generation

* Python
* `python-pptx`

## Image Processing

* Image Search API
* Python
* Pillow

## Text-to-Speech

* Edge TTS

## Video Generation

* FFmpeg
* Python


---

# 📂 Project Structure

```text
AI-Educational-Video-Generator/
│
├── Backend/
│   │
│   ├── main.py
│   │
│   ├── services/
│   │   ├── llm_service.py
│   │   ├── image_search.py
│   │   ├── slide_generator.py
│   │   ├── voice_generate.py
│   │   ├── video_generator.py
│   │   └── quiz_generator.py
│   │
│   ├── generated/
│   │   ├── slides/
│   │   ├── audio/
│   │   ├── videos/
│   │   ├── images/
│   │   └── pdf/
│   │
│   ├── requirements.txt
│   ├── .env
│   └── .gitignore
│
├── Frontend/
│   │
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   ├── App.jsx
│   │   └── main.jsx
│   │
│   ├── public/
│   ├── package.json
│   └── vite.config.js
│
└── README.md
```

> The exact folder structure may vary depending on the current implementation.

---

# 🔄 Complete Processing Pipeline

## Step 1 — User Provides a Prompt

The user enters an educational topic.

Example:

```text
Explain Machine Learning to a beginner.
```

---

## Step 2 — LLM Generates the Lesson

The backend sends the prompt to the selected LLM.

The LLM generates structured educational content.

```text
User Prompt
     ↓
LLM
     ↓
Structured Lesson
```

---

## Step 3 — Generate Slides

The lesson content is divided into multiple slides.

For example:

```text
Slide 1 → Introduction
Slide 2 → What is Machine Learning?
Slide 3 → Types of Machine Learning
Slide 4 → Training Process
Slide 5 → Real-World Applications
Slide 6 → Summary
```

---

## Step 4 — Find Relevant Images

The system generates image-search queries based on the slide content.

For example:

```text
Machine learning workflow
```

The resulting image can then be placed into the corresponding slide.

---

## Step 5 — Generate Voice

The slide narration is converted into speech.

```text
Slide Text
    ↓
Text-to-Speech
    ↓
Audio File
```

Example output:

```text
audio/
├── slide_1.mp3
├── slide_2.mp3
├── slide_3.mp3
└── slide_4.mp3
```

---

## Step 6 — Generate Video

The slides and generated audio are combined.

```text
Slides
  +
Voice Narration
  +
Timing
  ↓
FFmpeg
  ↓
Educational Video
```

Example:

```text
generated/videos/
└── educational_video.mp4
```

---

# 📦 Example Output

The system can produce:

```text
outputs/
│
├── lesson.json
│
├── slides/
│   ├── slide_1.pptx
│   ├── slide_2.pptx
│   ├── slide_3.pptx
│   └── slide_4.pptx
│
├── images/
│   ├── image_1.jpg
│   ├── image_2.jpg
│   └── image_3.jpg
│
├── audio/
│   ├── slide_1.mp3
│   ├── slide_2.mp3
│   └── slide_3.mp3
│
├── video/
│   └── cnn_tutorial.mp4

```

---

# 🧠 LLM Architecture

The application can support multiple LLM providers.

```text
                 ┌───────────────┐
                 │ User Prompt   │
                 └───────┬───────┘
                         │
                         ▼
                 ┌───────────────┐
                 │ LLM Service   │
                 └───────┬───────┘
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
     ┌─────────┐    ┌─────────┐   ┌─────────┐
     │ Gemini  │    │  Groq   │   │ Ollama  │
     └─────────┘    └─────────┘   └─────────┘
```

This allows the application to switch between cloud-based and locally hosted models.

---

# 💡 Why This Project?

The project demonstrates how multiple AI technologies can be combined into a single practical educational application.

It integrates:

```text
LLM
 │
 ├── Content Generation
 │
 ├── Slide Generation
 │
 ├── Image Search
 │
 ├── Voice Generation
 │
 └── PDF Generation
          │
          ▼
    Video Generation
```

---

# 📚 Technologies Used

| Technology   | Purpose                |
| ------------ | ---------------------- |
| Python       | Backend development    |
| FastAPI      | REST API               |
| React        | Frontend               |
| Vite         | Frontend development   |
| Tailwind CSS | UI styling             |
| Gemini       | LLM content generation |
| Groq         | Fast LLM inference     |
| Ollama       | Local LLM inference    |
| python-pptx  | PowerPoint generation  |
| Edge TTS     | Voice generation       |
| FFmpeg       | Video processing       |
| ReportLab    | PDF generation         |
| Pillow       | Image processing       |

---

# 👨‍💻 Author

**Shorifuzzaman Shuvo**

Software Engineering Student
Interested in:

* Artificial Intelligence
* Machine Learning
* Deep Learning
* Computer Vision
* Image Processing
* Generative AI
* Backend Development

