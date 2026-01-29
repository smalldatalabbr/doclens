from pathlib import Path
from langchain_core.documents import Document

def list_markdowns(docs_dir: Path) -> list[Path]:
    return sorted(docs_dir.glob("*.md"))

def load_documents(docs_dir: Path) -> list[Document]:
    files = list_markdowns(docs_dir)

    if not files:
        raise FileNotFoundError(f"Nenhum arquivo .md encontrado em: {docs_dir}")

    documents = []

    for f in files:
        text = f.read_text(encoding="utf-8")
        documents.append(
            Document(
                page_content=text,
                metadata={"source": f.name}
            )
        )

    return documents
