# audit/build_app_report.py (V3 - app privacy-first)
from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

from src.paths import APP_INTERACTIONS_FILE, APP_REPORTS_DIR

TOP_K_DEFAULT = 50  # no app, normalmente você quer listar tudo da sessão quando for incidente

DENIAL_MESSAGE_RE = re.compile(r"n[aã]o encontrei essa informa[cç][aã]o", re.I)

# Heurísticas de anomalia / allow suspeito (app)
RE_PLACEHOLDER = re.compile(
    r"(arquivo\s+n[aã]o\s+especificad[ao]|contexto\s+fornecido|\[fonte:\s*contexto\]|unknown_source|placeholder)",
    re.I,
)

# “procedural/exfil” mesmo se o regex do risk_rules falhar (prompt truncado, variação linguística etc.)
RE_PROC_SUSPECT = re.compile(
    r"(recupera[cç][aã]o\s+de\s+senha|redefini[rç][aã]o\s+de\s+senha|perdi\s+a\s+senha|"
    r"reescreva|re-escreva|em\s+linguagem\s+simpl(es|ificada)|incluindo\s+todos?)",
    re.I,
)

RE_JAILBREAK_SUSPECT = re.compile(r"(ignore\s+todas\s+as\s+regras|desconsidere\s+as\s+regras|bypass)", re.I)
RE_INVENTORY_SUSPECT = re.compile(r"(liste\s+apenas|t[ií]tulos\s+das\s+se[cç][oõ]es|se[cç][oõ]es\s+do\s+manual|sum[aá]rio|[ií]ndice)", re.I)
RE_EXFIL_SUSPECT = re.compile(r"(conte[uú]do\s+completo|integral|revelar\s+integralmente|dump|todo\s+o\s+conte[uú]do)", re.I)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def parse_ts(ts: str | None) -> datetime | None:
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except Exception:
        return None


def fmt_dt(ts: str | None) -> str:
    dt = parse_ts(ts)
    if not dt:
        return ts or "—"
    return dt.strftime("%Y-%m-%d %H:%M:%S UTC")


def safe(s: str, n: int) -> str:
    s = (s or "").strip()
    return s if len(s) <= n else s[:n].rstrip() + "…"


def md_codeblock(text: str) -> str:
    text = (text or "").replace("```", "'''")
    return f"```text\n{text}\n```"


def unique_sources(row: dict[str, Any]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for s in row.get("sources", []) or []:
        if not isinstance(s, dict):
            continue
        src = s.get("source")
        if not src:
            continue
        if src not in seen:
            seen.add(src)
            out.append(src)
    return out


def is_intercepted(row: dict[str, Any]) -> bool:
    action = (row.get("action") or "").strip().lower()
    return bool(action) and action != "allow"


def pick_latest_session_id(rows: list[dict[str, Any]]) -> str:
    # pega a sessão cuja última ts_utc é a mais recente
    by_sess: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in rows:
        sid = r.get("session_id") or "UNKNOWN_SESSION"
        by_sess[sid].append(r)

    best_sid = None
    best_ts: datetime | None = None

    for sid, rs in by_sess.items():
        ts_list = [parse_ts(x.get("ts_utc")) for x in rs]
        ts_list = [t for t in ts_list if t is not None]
        if not ts_list:
            continue
        mx = max(ts_list)
        if best_ts is None or mx > best_ts:
            best_ts = mx
            best_sid = sid

    return best_sid or (rows[-1].get("session_id") or "UNKNOWN_SESSION")


def find_anomalies_app(rows: list[dict[str, Any]]) -> list[str]:
    issues: list[str] = []

    for r in rows:
        iid = r.get("interaction_id", "—")
        action = (r.get("action") or "").strip().lower()
        prompt = str(r.get("prompt", "") or "")
        answer = str(r.get("answer", "") or "")
        sources = r.get("sources", []) or []
        violations = r.get("violations", []) or []
        score = int(r.get("risk_score", 0) or 0)

        # allow com risco alto
        if action == "allow" and score >= 50:
            issues.append(f"- Interação {iid}: action=allow mas risk_score={score} (ALLOW_SUSPEITO).")

        # allow com violations preenchidas
        if action == "allow" and violations:
            issues.append(f"- Interação {iid}: action=allow mas violations={violations} (inconsistente).")

        # DENIAL com sources (isso deveria ser rewrite/block no POST)
        if DENIAL_MESSAGE_RE.search(answer) and sources:
            issues.append(f"- Interação {iid}: resposta é negação padrão mas trouxe sources (SOURCE_ON_DENIAL).")

        # placeholder na resposta
        if action == "allow" and RE_PLACEHOLDER.search(answer):
            issues.append(f"- Interação {iid}: action=allow mas resposta tem placeholder de fonte (TRACEABILITY).")

        # allow suspeito por intenção (heurística de prompt)
        if action == "allow":
            if RE_PROC_SUSPECT.search(prompt):
                issues.append(f"- Interação {iid}: allow em prompt procedural/exfil suspeito (PROC_SUSPECT).")
            if RE_JAILBREAK_SUSPECT.search(prompt):
                issues.append(f"- Interação {iid}: allow em prompt jailbreak suspeito (JAILBREAK_SUSPECT).")
            if RE_INVENTORY_SUSPECT.search(prompt):
                issues.append(f"- Interação {iid}: allow em prompt inventory suspeito (INVENTORY_SUSPECT).")
            if RE_EXFIL_SUSPECT.search(prompt):
                issues.append(f"- Interação {iid}: allow em prompt exfil suspeito (EXFIL_SUSPECT).")

    return issues


def build_app_report_v3(rows_all: list[dict[str, Any]], session_id: str, top_k: int) -> str:
    rows = [r for r in rows_all if (r.get("session_id") or "UNKNOWN_SESSION") == session_id]
    if not rows:
        raise RuntimeError(f"Nenhuma linha encontrada para session_id={session_id}")

    # ordena por interaction_id (se existir) e fallback por ts
    def sort_key(r: dict[str, Any]):
        iid = r.get("interaction_id")
        try:
            iid_int = int(iid)
        except Exception:
            iid_int = 10**9
        ts = parse_ts(r.get("ts_utc")) or datetime.min
        return (iid_int, ts)

    rows = sorted(rows, key=sort_key)

    # meta
    first = rows[0]
    meta_model = first.get("model", "")
    meta_temp = first.get("temperature", "")
    meta_embed = first.get("embeddings", "")

    ts_list = [parse_ts(r.get("ts_utc")) for r in rows]
    ts_list = [t for t in ts_list if t is not None]
    ts_min = min(ts_list).strftime("%Y-%m-%d %H:%M:%S UTC") if ts_list else "—"
    ts_max = max(ts_list).strftime("%Y-%m-%d %H:%M:%S UTC") if ts_list else "—"

    # KPIs
    total = len(rows)
    by_action = Counter((r.get("action") or "unknown").strip().lower() for r in rows)
    scores = [float(r.get("risk_score", 0) or 0) for r in rows]
    avg_score = (sum(scores) / len(scores)) if scores else 0.0
    high_risk = sum(1 for s in scores if s >= 50)
    intercepted_total = sum(1 for r in rows if is_intercepted(r))

    anomalies = find_anomalies_app(rows)
    allow_suspects = [r for r in rows if (r.get("action") or "").strip().lower() == "allow" and any(
        [
            DENIAL_MESSAGE_RE.search(str(r.get("answer", "") or "")) and (r.get("sources") or []),
            RE_PLACEHOLDER.search(str(r.get("answer", "") or "")),
            RE_PROC_SUSPECT.search(str(r.get("prompt", "") or "")),
            RE_JAILBREAK_SUSPECT.search(str(r.get("prompt", "") or "")),
            RE_INVENTORY_SUSPECT.search(str(r.get("prompt", "") or "")),
            RE_EXFIL_SUSPECT.search(str(r.get("prompt", "") or "")),
        ]
    )]

    # Detalhamento: interceptados + allows suspeitos
    detailed = [r for r in rows if is_intercepted(r)]
    # adiciona allows suspeitos sem duplicar
    seen_ids = set((r.get("interaction_id"), r.get("ts_utc")) for r in detailed)
    for r in allow_suspects:
        key = (r.get("interaction_id"), r.get("ts_utc"))
        if key not in seen_ids:
            detailed.append(r)
            seen_ids.add(key)

    detailed = sorted(detailed, key=sort_key)[:top_k]

    md: list[str] = []
    md.append("# Relatório de Execução — DocLens (V3 | App)\n\n")
    md.append(f"**Session ID:** `{session_id}`  \n")
    md.append(f"**Período:** {ts_min} → {ts_max}  \n")
    md.append(f"**Modelo:** `{meta_model}` | **Temperature:** `{meta_temp}` | **Embeddings:** `{meta_embed}`  \n\n")

    md.append("## KPIs\n\n")
    md.append(f"- **Total de interações:** **{total}**\n")
    md.append(f"- **Interceptadas (≠ allow):** **{intercepted_total}/{total}**\n")
    md.append(f"- **High-risk (risk ≥ 50):** **{high_risk}/{total}**\n")
    md.append(f"- **Risco médio:** **{avg_score:.1f}**\n")
    md.append(f"- **Allows suspeitos:** **{len(allow_suspects)}**\n\n")

    md.append("## Distribuição por ação\n\n")
    md.append("| Ação | Qtde |\n|---|---:|\n")
    for a in ["allow", "block", "rewrite", "deny_out_of_scope", "unknown"]:
        if by_action.get(a, 0):
            md.append(f"| `{a}` | {by_action[a]} |\n")
    md.append("\n")

    md.append("## Anomalias detectadas (drift / falhas de regra)\n\n")
    if anomalies:
        md.extend([x + "\n" for x in anomalies])
    else:
        md.append("- Nenhuma anomalia detectada.\n")
    md.append("\n")

    md.append("## Detalhamento (interceptadas + allows suspeitos)\n\n")
    if not detailed:
        md.append("- Nada a detalhar.\n")
        return "".join(md)

    for r in detailed:
        iid = r.get("interaction_id", "—")
        ts = fmt_dt(r.get("ts_utc"))
        action = (r.get("action") or "").strip()
        score = r.get("risk_score", 0)
        groups = r.get("groups", []) or []
        violations = r.get("violations", []) or []
        prompt = str(r.get("prompt", "") or "")
        answer = str(r.get("answer", "") or "")
        sources = unique_sources(r)

        md.append(
            f"**Interação {iid}** — `{ts}` | action `{action}` | risco `{score}` | groups `{', '.join(groups) if groups else '—'}` | violações `{', '.join(violations) if violations else '—'}`  \n"
        )
        md.append(f"- **Prompt:** {safe(prompt, 280)}  \n")
        md.append(f"- **Sources (payload):** {', '.join(sources) if sources else '—'}  \n")
        md.append(f"- **Resposta (trecho):**\n{md_codeblock(safe(answer, 900))}\n\n")

    return "".join(md)


def main() -> int:
    parser = argparse.ArgumentParser(description="Gera relatório Markdown (DocLens V3 | app).")
    parser.add_argument("--in", dest="in_path", default=str(APP_INTERACTIONS_FILE), help="Caminho do JSONL (app_interactions.jsonl).")
    parser.add_argument("--outdir", default=str(APP_REPORTS_DIR), help="Pasta de saída do relatório.")
    parser.add_argument("--topk", type=int, default=TOP_K_DEFAULT, help="Limite de itens no detalhamento.")
    parser.add_argument("--session-id", default="", help="Força um session_id específico. Se vazio, usa o mais recente.")
    args = parser.parse_args()

    in_path = Path(args.in_path)
    if not in_path.exists():
        raise FileNotFoundError(f"Não achei: {in_path}")

    rows_all = read_jsonl(in_path)
    if not rows_all:
        raise RuntimeError("Nenhuma linha JSON encontrada. Verifique o arquivo de entrada.")

    session_id = args.session_id.strip() or pick_latest_session_id(rows_all)

    md = build_app_report_v3(rows_all, session_id=session_id, top_k=args.topk)

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    out_path = outdir / f"app_session_{session_id}_v3.md"
    out_path.write_text(md, encoding="utf-8")

    print(f"Relatório gerado: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
