# Multi‑modal Gen‑AI Farmer Assistant  
### A Unified AI Agent for Crop Disease Diagnosis & Localized Agricultural Support

An AI-driven assistant that bridges complex agricultural science and practical farmer guidance. It supports **multi-lingual voice and text interactions**, performs **real-time crop disease diagnosis**, and provides **localized, actionable advice** in the user’s native language.

---

## Key Features

- **Multi‑modal Interaction**
  - Accepts **Voice input** (`.mp3`) and **Typed Text**
  - Works across multiple languages (Hindi, Telugu, English, etc.)

- **Vision AI Disease Diagnosis**
  - Fine‑tuned **MobileNetV2** model
  - Detects **19 crop disease classes**
  - Crops supported: **Apple, Corn, Potato, Tomato, Pepper, Strawberry**

- **Explainable AI (XAI)**
  - Generates **Grad‑CAM heatmaps** to show which leaf regions influenced the prediction

- **Farmer‑Friendly Advice Layer**
  - Converts technical class labels into **simple, actionable guidance**

- **Real‑time Weather Integration**
  - Uses **OpenWeatherMap API** for context-aware alerts (rain, heat, humidity, etc.)

- **Automated Voice Output**
  - Responds using **TTS** in the farmer’s language

---

## Tech Stack

| Category | Tools |
|---|---|
| Deep Learning | TensorFlow / Keras (CNN) |
| Speech | OpenAI Whisper (Transcription + Language Detection) |
| NLP | Transformers (Zero‑Shot Intent Classification), LangDetect |
| Translation + TTS | deep‑translator (GoogleTranslator), gTTS |
| Weather | OpenWeatherMap API |
| Computer Vision | OpenCV (Blur Detection + Grad‑CAM) |

---

## Project Outputs

- **`heatmap_output.jpg`**  
  Saved after diagnosis to provide visual evidence of detected symptoms.

- **`response_###.mp3`** (or `response.mp3`)  
  Spoken assistant response (saved to disk; playback depends on environment).

---

## Installation & Setup

### 1) Prerequisites
- **Python 3.10+**
- **FFmpeg** (required for Whisper audio loading)

**Windows**
```bash
winget install ffmpeg
```

**Linux**
```bash
sudo apt install ffmpeg
```

---

### 2) Clone the Repository
```bash
git clone https://github.com/YourUsername/Crop-Disease-Agent.git
cd Crop-Disease-Agent
```

---

### 3) Install Dependencies
```bash
pip install -r requirements.txt
```

> Tip: Use a virtual environment to avoid package conflicts.

---

### 4) Configuration (Weather API)
Create a `.env` file in the project root:

```text
OPENWEATHER_API_KEY=your_actual_api_key_here
```

---

## Usage

### Initialize the Agent
```python
from farmer_agent import IntegratedFarmerAgent

agent = IntegratedFarmerAgent("model/crop_disease_master_model.keras")
```

### Example 1: Voice Input + Image Diagnosis
```python
agent.process_full_request(
    image_path="test_samples/leaf.jpg",
    audio_path="test_samples/request.mp3"
)
```

### Example 2: Native Text Input
```python
agent.process_text_input("मेरे पौधों के लिए आज का मौसम कैसा है?")
```

---

## Visual Evidence (Grad‑CAM)

When a diagnosis is made, the system saves **`heatmap_output.jpg`**.  
This image highlights **hot zones** (often red) where the model detected visual symptoms, helping validate predictions and build user trust.

---

## Notes / Common Issues

- If audio is not “playing” in terminal runs, it is usually because `IPython.display.Audio(...)` only autoplays inside notebooks. In scripts, prefer saving MP3 and opening it via the OS default player.
- If TensorFlow fails to install on the latest Python versions, use a stable supported version (commonly Python 3.12).

---