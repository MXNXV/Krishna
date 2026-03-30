# Bhagavad Gita RAG Assistant

A verse-grounded Retrieval-Augmented Generation (RAG) app for the Bhagavad Gita with:

- semantic retrieval (`ChromaDB` + sentence embeddings)
- chapter-safe context expansion
- LLM answer generation with verse citations
- Streamlit UI (`app.py`)

## Project Structure

```
Krishna/
├── src/                      # Core RAG modules
│   ├── config.py            # Central constants and paths
│   ├── process_data.py      # CSV cleaning + metadata extraction
│   ├── generate_embeddings.py  # Embedding generation
│   ├── build_index.py       # Build/rebuild Chroma vector index
│   ├── retrieve.py          # Semantic retrieval from Chroma
│   ├── expand_context.py    # Context windows around retrieved verses
│   └── answer.py            # End-to-end RAG orchestration
├── scripts/                 # CLI scripts
│   ├── build_index.py       # Index building script
│   ├── generate_embeddings.py  # Embedding generation script
│   └── test_retrieve.py     # Test retrieval script
├── tests/                   # Test files
│   └── test_all_queries.py  # Test 10 RAG queries
├── data/                    # Source data
│   └── Bhagwad_Gita.csv
├── chroma_db/              # ChromaDB index (gitignored)
├── app.py                  # Streamlit entry point
├── requirements.txt
└── runtime.txt
```

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
python scripts/build_index.py
```

This creates the local Chroma database under `chroma_db/`.

## Run Streamlit App

```bash
streamlit run app.py
```

## Run Tests

```bash
python tests/test_all_queries.py
```

## Required Secret

- `OPENAI_API_KEY` (required)

If deploying on Streamlit Cloud, set this in app Secrets rather than committing it to files.

## Notes for Deployment

- Local `chroma_db/` is committed to git for Streamlit Cloud deployment

