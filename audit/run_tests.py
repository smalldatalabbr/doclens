# audit/run_tests.py (V3 aligned with app.py)
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage

from src.paths import (
    DOCS_DIR,
    INDEX_DIR,
    DEFAULT_EMBEDDINGS,
    DEFAULT_MODEL,
    DEFAULT_TEMPERATURE,
    AUDIT_RUNS_FILE,
)

from src.ingest import load_documents
from src.vectorstore import (
    build_vectorstore,
    save_vectorstore,
    load_vectorstore,
    make_retriever,
)

# IMPORTANT: same call stack as app.py
from src.rag import load_llm, build_rag_chain, invoke_rag

from audit.prompts_phase import PHASE_PROMPTS

from src.guardrails import (
    decide_on_prompt,
    decide_on_answer,
    safe_denial_if_out_of_scope,
)

load_dotenv()


def ensure_retriever(emb_model: str):
    if INDEX_DIR.exists() and any(INDEX_DIR.iterdir()):
        vs = load_vectorstore(INDEX_DIR, emb_model)
    else:
        docs = load_documents(DOCS_DIR)
        vs = build_vectorstore(docs, emb_model)
        save_vectorstore(vs, INDEX_DIR)
    return make_retriever(vs)


def write_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def utc_ts() -> str:
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"


def main():
    # Same as app.py: build cached-ish objects once
    llm = load_llm(DEFAULT_MODEL, float(DEFAULT_TEMPERATURE))
    retriever = ensure_retriever(DEFAULT_EMBEDDINGS)
    rag_chain = build_rag_chain(llm, retriever)

    run_id = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")

    for i, prompt in enumerate(PHASE_PROMPTS, start=1):
        # 0) Build minimal chat_history (tests are independent)
        # (In app, chat_history persists; here we keep deterministic per test.)
        chat_history = [
            AIMessage(content="Olá! Sou o assistente do SDL Bank. Como posso ajudar?"),
            HumanMessage(content=prompt),
        ]

        # 1) Guardrail PRE (intention)
        pre = decide_on_prompt(prompt)

        # Same semantics as app.py: forced denial (OOS) does NOT call LLM
        forced_denial = safe_denial_if_out_of_scope(prompt, pre.groups)

        answer_text = ""
        sources: list[dict[str, Any]] = []
        action = ""
        blocked = False
        groups = pre.groups or []
        violations = pre.violations or []
        risk_score = int(pre.risk_score or 0)

        # 2) PRE blocked
        if pre.blocked:
            answer_text = pre.message or "Bloqueado."
            sources = []
            action = pre.action
            blocked = True

            # log uses PRE
            groups = pre.groups or []
            violations = pre.violations or []
            risk_score = int(pre.risk_score or 0)

        # 3) OOS forced denial (no LLM)
        elif forced_denial is not None:
            answer_text = forced_denial
            sources = []
            action = "deny_out_of_scope"
            blocked = True

            # log uses PRE (same as app: post=None)
            groups = pre.groups or []
            violations = pre.violations or []
            risk_score = int(pre.risk_score or 0)

        # 4) Invoke RAG (same as app: invoke_rag wrapper)
        else:
            result = invoke_rag(rag_chain, prompt, chat_history)

            if isinstance(result, dict) and "answer" in result:
                raw_answer = str(result.get("answer", "") or "")
                raw_sources = result.get("sources", []) or []
            else:
                raw_answer = str(result)
                raw_sources = []

            # 5) Guardrail POST (behavior)
            post = decide_on_answer(prompt, raw_answer)

            if post.blocked:
                answer_text = post.message or raw_answer
                sources = []
                action = post.action
                blocked = True
            else:
                answer_text = raw_answer
                sources = raw_sources
                action = "allow"
                blocked = False

            # log uses POST (same pattern as app.py)
            groups = post.groups or pre.groups or []
            violations = post.violations or pre.violations or []
            risk_score = int(post.risk_score or pre.risk_score or 0)

        row = {
            "run_id": run_id,
            "test_id": i,
            "action": action,
            "prompt": prompt,
            "answer": answer_text,
            "sources": sources,
            "blocked": bool(blocked),
            "groups": groups,
            "violations": violations,
            "risk_score": int(risk_score),
            "ts_utc": utc_ts(),
            "model": DEFAULT_MODEL,
            "temperature": float(DEFAULT_TEMPERATURE),
            "embeddings": DEFAULT_EMBEDDINGS,
            "origin": "batch",
        }

        write_jsonl(AUDIT_RUNS_FILE, row)

    print(f"\nRun {run_id} finalizado. Logs: {AUDIT_RUNS_FILE}")


if __name__ == "__main__":
    main()