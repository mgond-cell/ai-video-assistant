# 🎥 AI Video Assistant

An AI-powered application that transforms YouTube videos and local audio/video files into useful summaries, action items, key decisions, open questions, and an interactive chat experience.

## ✨ Features

- **YouTube Audio Extraction** — Extract audio from YouTube videos.
- **Local File Support** — Process supported local media files.
- **AI Transcription** — Convert speech into text using OpenAI Whisper.
- **English & Hinglish Modes** — Choose the transcription workflow based on your needs.
- **AI-Powered Summarization** — Generate clear, structured summaries using Groq.
- **Action Item Extraction** — Identify tasks and follow-up actions.
- **Key Decisions & Open Questions** — Extract important decisions and unresolved topics.
- **RAG-Based Chat** — Ask questions about the processed transcript.
- **Vector Search** — Store and retrieve relevant transcript chunks using ChromaDB and Hugging Face embeddings.
- **Streamlit UI** — Interact with the application through a user-friendly web interface.

## 🛠️ Tech Stack

| Component | Technology |
|---|---|
| Frontend | Streamlit |
| Programming Language | Python |
| Speech-to-Text | OpenAI Whisper |
| LLM | Groq API with LangChain |
| Vector Database | ChromaDB |
| Embeddings | Hugging Face Sentence Transformers |
| YouTube Audio | yt-dlp |
| Audio Processing | FFmpeg, pydub |
| Environment Configuration | python-dotenv |

## 📁 Project Structure

```text
video_assistant/
├── app.py
├── main.py
├── requirements.txt
├── .gitignore
├── core/
│   ├── extractor.py
│   ├── rag_engine.py
│   ├── sammarize.py
│   ├── transcriber.py
│   └── vector_store.py
├── utils/
│   └── audio_processor.py
├── download/       # Generated locally; not committed
├── models/         # Downloaded models; not committed
└── vector_db/      # Generated locally; not committed
```

## 🚀 Run Locally

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git
cd YOUR_REPOSITORY
```

Replace the repository URL with your actual GitHub repository URL.

### 2. Install dependencies

Install Python and the FFmpeg executable first. Ensure FFmpeg is available to your application.

Create a virtual environment if needed:

```bash
python -m venv .venv
```

Activate it on Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Install project dependencies:

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

Create a `.env` file in the project root and add the API keys required by your configuration:

```env
GROQ_API_KEY=your_groq_api_key
SARVAM_API_KEY=your_sarvam_api_key
```

Only configure the keys used by your selected features. Never commit your `.env` file or expose API keys publicly.

### 4. Launch the Streamlit app

```bash
streamlit run app.py
```

Open the local URL displayed in your terminal.

## ☁️ Deployment

This application can be deployed on Streamlit Community Cloud.

1. Push the project to a GitHub repository.
2. Open [Streamlit Community Cloud](https://share.streamlit.io/).
3. Connect your GitHub account and select the repository.
4. Select `app.py` as the application entry point.
5. Configure the required API keys under the app's **Secrets** settings.
6. Deploy and review the logs if any dependency or runtime issue occurs.

**Deployment note:** Whisper and embedding models may require downloads and CPU memory. Streamlit Cloud has resource limits, and local FFmpeg paths must not be hard-coded for deployment. Verify audio processing, model loading, and temporary-file handling in the cloud environment before sharing the app.

## 🔐 Security

- Keep API keys in environment variables or Streamlit Secrets.
- Do not commit `.env`, virtual environments, downloaded media, model weights, or local vector databases.
- Avoid logging API keys or other secrets.
- Review uploaded media and temporary-file handling before deploying publicly.

## 🔮 Future Improvements

- Export summaries and action items as downloadable files.
- Improve transcription quality and language support.
- Add transcript timestamps and source-grounded chat responses.
- Optimize model loading and processing for cloud deployment.
- Improve error handling for unsupported files and unavailable video sources.

## 👨‍💻 Author

**Mithilesh Gond**

- GitHub: [mgond-cell](https://github.com/mgond-cell)
- LinkedIn: [Mithilesh Gond](https://www.linkedin.com/in/mithilesh-gond-5b543022a/)
