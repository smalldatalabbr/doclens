# audit/run_tests.py
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage

from src.paths import DOCS_DIR, INDEX_DIR, DEFAULT_EMBEDDINGS, DEFAULT_MODEL, DEFAULT_TEMPERATURE, TESTS_FILE
from src.ingest import load_documents
from src.vectorstore import build_vectorstore, save_vectorstore, load_vectorstore, make_retriever
from src.rag import load_llm, build_rag_chain, invoke_rag

from audit.prompts_phase2 import PHASE2_PROMPTS

from dotenv import load_dotenv

from audit.logger import log_interaction
from audit.risk_rules import classify_risk



load_dotenv()

OUT_FILE = TESTS_FILE


def ensure_retriever(emb_model: str):
    if INDEX_DIR.exists() and any(INDEX_DIR.iterdir()):
        vs = load_vectorstore(INDEX_DIR, emb_model)
    else:
        docs = load_documents(DOCS_DIR)  # retorna list[dict] no seu novo ingest
        vs = build_vectorstore(docs, emb_model)
        save_vectorstore(vs, INDEX_DIR)
    return make_retriever(vs)


def write_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def main():
    llm = load_llm(DEFAULT_MODEL, float(DEFAULT_TEMPERATURE))
    retriever = ensure_retriever(DEFAULT_EMBEDDINGS)
    rag_chain = build_rag_chain(llm, retriever)

    run_id = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")

    for i, prompt in enumerate(PHASE2_PROMPTS, start=1):
        chat_history = [AIMessage(content="Olá, sou o assistente do SDL Bank. Como posso ajudar?")]
        chat_history.append(HumanMessage(content=prompt))

        result = rag_chain.invoke({"question": prompt, "chat_history": chat_history})


        audit = classify_risk(prompt, result["answer"])

        row = {
            "run_id": run_id,
            "test_id": i,
            "prompt": prompt,
            "answer": result["answer"],
            "sources": result["sources"],
            "violations": audit["violations"],
            "risk_score": audit["risk_score"],
            "ts_utc": datetime.utcnow().isoformat(timespec="seconds") + "Z",
            "model": DEFAULT_MODEL,
            "temperature": float(DEFAULT_TEMPERATURE),
            "embeddings": DEFAULT_EMBEDDINGS,
        }

        write_jsonl(OUT_FILE, row)
        log_interaction(row)

    print(f"\nRun {run_id} finalizado. Logs: {OUT_FILE}")


if __name__ == "__main__":
    main()
