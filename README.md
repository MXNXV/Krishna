# Bhagavad Gita RAG Assistant

A verse-grounded Retrieval-Augmented Generation (RAG) app for the Bhagavad Gita with:

- semantic retrieval (`ChromaDB` + sentence embeddings)
- chapter-safe context expansion
- LLM answer generation with verse citations
- Streamlit UI (`app.py`)

## Project Structure

- `app.py` - Streamlit entry point
- `answer.py` - end-to-end RAG orchestration (retrieve -> expand -> answer)
- `retrieve.py` - semantic retrieval from Chroma
- `expand_context.py` - context windows around retrieved verses
- `build_index.py` - build/rebuild Chroma vector index
- `generate_embeddings.py` - embedding generation
- `process_data.py` - CSV cleaning + metadata extraction
- `config.py` - central constants and paths

## Local Setup

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Set required environment variable:

```bash
# Windows PowerShell
$env:OPENAI_API_KEY="your_key_here"
```

## Build Index (one-time or when data changes)

```bash
python build_index.py
```

This creates the local Chroma database under `chroma_db/`.

## Run Streamlit App

```bash
streamlit run app.py
```

## Required Secret

- `OPENAI_API_KEY` (required)

If deploying on Streamlit Cloud, set this in app Secrets rather than committing it to files.

## Notes for Deployment

- Local `chroma_db/` is ignored by git.
- Build index in the deploy environment (or switch to a hosted vector DB for production persistence).
- Never commit `.env` or `.streamlit/secrets.toml`.
