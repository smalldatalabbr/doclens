from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]

DATA_DIR = BASE_DIR / "data"
DOCS_DIR = DATA_DIR / "docs"
INDEX_DIR = DATA_DIR / "index_faiss"

# Garante que os diretórios existam
DATA_DIR.mkdir(exist_ok=True)
DOCS_DIR.mkdir(exist_ok=True)
INDEX_DIR.mkdir(exist_ok=True)

# Modelos padrão
DEFAULT_MODEL = "llama-3.3-70b-versatile"   # depois podemos trocar para 8B se precisar
DEFAULT_TEMPERATURE = 0.7
DEFAULT_EMBEDDINGS = "BAAI/bge-m3"
