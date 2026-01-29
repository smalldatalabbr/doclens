from pathlib import Path
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS


def build_vectorstore(documents: list[Document], embedding_model: str) -> FAISS:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=150
    )

    split_docs: list[Document] = []

    for doc in documents:
        chunks = splitter.split_text(doc.page_content)
        for chunk in chunks:
            split_docs.append(
                Document(
                    page_content=chunk,
                    metadata=doc.metadata
                )
            )

    embeddings = HuggingFaceEmbeddings(model_name=embedding_model)
    return FAISS.from_documents(split_docs, embedding=embeddings)


def save_vectorstore(vs: FAISS, index_dir: Path) -> None:
    index_dir.mkdir(parents=True, exist_ok=True)
    vs.save_local(str(index_dir))


def load_vectorstore(index_dir: Path, embedding_model: str) -> FAISS:
    embeddings = HuggingFaceEmbeddings(model_name=embedding_model)
    return FAISS.load_local(
        str(index_dir),
        embeddings,
        allow_dangerous_deserialization=True
    )


def make_retriever(vs: FAISS):
    return vs.as_retriever(
        search_type="mmr",
        search_kwargs={"k": 4, "fetch_k": 6}
    )