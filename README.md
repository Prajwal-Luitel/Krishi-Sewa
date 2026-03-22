# Krishi Sewa - RAG Setup

This project now uses a standard service-layer RAG pipeline for disease-based product recommendation:

- `home/services/rag/chroma_store.py` for vector retrieval (ChromaDB)
- `home/services/rag/ollama_client.py` for LLM JSON generation
- `home/services/rag/pipeline.py` for orchestration
- `home/views.py` calls the pipeline from `detect`

## 1) Python dependency

Install ChromaDB (already done in this environment):

```powershell
pip install chromadb
```

## 2) Ollama models

Pull and serve required models:

```powershell
ollama pull llama3.1:8b
ollama pull nomic-embed-text
ollama serve
```

## 3) Environment configuration

Create `.env` from `.env.example` and keep/update these values:

```env
OLLAMA_MODEL=llama3.1:8b
OLLAMA_URL=http://localhost:11434/api/generate
OLLAMA_BASE_URL=http://localhost:11434
CHROMA_PERSIST_DIR=.chroma
CHROMA_COLLECTION=product_catalog
CHROMA_EMBED_MODEL=nomic-embed-text
```

Current code has safe defaults, so it can run even without `.env`. The file helps make configuration explicit.

## 4) Run Django

```powershell
python manage.py runserver
```

Open `/detect/`, upload a leaf image, and click Detect.

## 5) Notes

- If Chroma/Ollama embedding is unavailable, retrieval gracefully falls back to database ordering.
- If LLM generation is unavailable, summary falls back to `"Couldn't connect to AI..."` guidance.
