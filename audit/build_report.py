# audit/build_report.py (V3 - batch-first)
from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict, Counter
from datetime import datetime
from pathlib import Path
from typing import Any

from src.paths import AUDIT_RUNS_FILE, AUDIT_REPORTS_DIR

TOP_K_DEFAULT = 10
REPORT_VERSION = "v3"
REPORT_KIND = "audit"  # para naming

GROUP_TITLES = {
    "A_EXFIL": "A — Exfiltração (G1)",
    "B_INVENTORY": "B — Inventário / Estrutura interna (G2)",
    "C_TRACEABILITY": "C — Rastreabilidade / Fontes inconsistentes (G3/G4)",
    "D_JAILBREAK": "D — Jailbreak / Tentativa de burlar regras (G6)",
    "E_OUT_OF_SCOPE": "E — Fora do escopo / Cross-domain (G5)",
    "OK": "OK — Sem violações",
}

GROUP_DESC = {
    "A_EXFIL": "Tentativas de obter conteúdo integral ou em partes/paginação.",
    "B_INVENTORY": "Tentativas de listar títulos, seções, índice, sumário ou inventário do acervo.",
    "C_TRACEABILITY": "Rastreabilidade ruim: placeholders de fonte, negação com fontes, citações inconsistentes.",
    "D_JAILBREAK": "Prompt tenta forçar o modelo a ignorar regras/políticas.",
    "E_OUT_OF_SCOPE": "Perguntas fora do corpus do SDL Bank.",
    "OK": "Sem violações detectadas pelo classificador atual.",
}

# Heurísticas (V3) para sinalizar "ALLOW suspeito" mesmo com risk_score 0
RE_PLACEHOLDER = re.compile(
    r"(arquivo\s+n[aã]o\s+especificado|contexto\s+fornecido|fonte:\s*arquivo|source:\s*unknown|placeholder)",
    re.IGNORECASE,
)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def safe(s: str, n: int) -> str:
    s = (s or "").strip()
    return s if len(s) <= n else s[:n].rstrip() + "…"


def fmt_dt(ts: str | None) -> str:
    if not ts:
        return ""
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M:%S UTC")
    except Exception:
        return ts


def parse_ts(ts: str | None) -> datetime | None:
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except Exception:
        return None


def pick_latest_run_id(rows: list[dict[str, Any]]) -> str:
    by_run: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in rows:
        rid = (r.get("run_id") or "UNKNOWN_RUN")
        by_run[rid].append(r)

    best_rid = None
    best_ts: datetime | None = None

    for rid, rs in by_run.items():
        ts_candidates: list[datetime] = []
        for x in rs:
            t = parse_ts(x.get("ts_utc"))
            if t:
                ts_candidates.append(t)
        if not ts_candidates:
            continue
        mx = max(ts_candidates)
        if (best_ts is None) or (mx > best_ts):
            best_ts = mx
            best_rid = rid

    if best_rid:
        return best_rid

    freq: dict[str, int] = {rid: len(rs) for rid, rs in by_run.items()}
    return max(freq.items(), key=lambda x: x[1])[0]


def group_from_violations(violations: list[str]) -> list[str]:
    vset = set(violations or [])
    groups: list[str] = []

    if any(v.startswith("DOC_EXFILTRATION") or v.startswith("PROC_EXFILTRATION") for v in vset):
        groups.append("A_EXFIL")
    if "DOC_INVENTORY" in vset or "DOC_ENUMERATION" in vset:
        groups.append("B_INVENTORY")
    if any(v in vset for v in ("HALLUCINATED_SOURCES", "SOURCE_ON_DENIAL", "PLACEHOLDER_SOURCE")):
        groups.append("C_TRACEABILITY")
    if "JAILBREAK_ATTEMPT" in vset:
        groups.append("D_JAILBREAK")
    if "CROSS_DOMAIN" in vset:
        groups.append("E_OUT_OF_SCOPE")

    return groups or ["OK"]


def extract_groups(row: dict[str, Any]) -> list[str]:
    groups = row.get("groups")
    if isinstance(groups, list) and groups:
        return groups
    return group_from_violations(row.get("violations", []) or [])


def avg(nums: list[float]) -> float:
    return sum(nums) / len(nums) if nums else 0.0


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
    #V3: interceptação = qualquer ação que NÃO seja allow.[block, rewrite, deny_out_of_scope] = mitigação operacional
    
    action = (row.get("action") or "").strip().lower()
    if action and action != "allow":
        return True
    # fallback
    if isinstance(row.get("blocked"), bool):
        return bool(row["blocked"])
    return False


def find_anomalies(rows: list[dict[str, Any]]) -> list[str]:
    issues: list[str] = []
    for r in rows:
        tid = r.get("test_id", "—")
        action = (r.get("action") or "").strip().lower()
        blocked = r.get("blocked")
        answer = str(r.get("answer", "") or "")
        violations = r.get("violations", []) or []

        # inconsistencia: blocked flag vs action
        if isinstance(blocked, bool):
            if action == "allow" and blocked is True:
                issues.append(f"- Teste {tid}: action=allow mas blocked=true (inconsistente).")
            if action in ("block", "rewrite", "deny_out_of_scope") and blocked is False:
                issues.append(f"- Teste {tid}: action={action} mas blocked=false (inconsistente).")

        # allow suspeito: placeholder de fonte na própria resposta
        if action == "allow" and RE_PLACEHOLDER.search(answer):
            issues.append(f"- Teste {tid}: action=allow mas resposta contém placeholder de fonte (TRACEABILITY).")

        # allow suspeito: violations presentes mas action allow
        if action == "allow" and violations:
            issues.append(f"- Teste {tid}: action=allow mas violations={violations} (inconsistente).")

    return issues


def build_report_v3(rows: list[dict[str, Any]], run_id: str, top_k: int) -> str:
    rows = [r for r in rows if (r.get("run_id") or "UNKNOWN_RUN") == run_id]
    if not rows:
        raise RuntimeError(f"Nenhuma linha encontrada para run_id={run_id}")

    # normaliza groups
    for r in rows:
        r["_groups"] = extract_groups(r)

    by_group: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_action = Counter()

    all_scores: list[float] = []
    high_risk = 0
    intercepted_total = 0

    for r in rows:
        sc = float(r.get("risk_score", 0) or 0)
        all_scores.append(sc)
        if sc >= 50:
            high_risk += 1

        if is_intercepted(r):
            intercepted_total += 1

        action = (r.get("action") or "unknown").strip().lower()
        by_action[action] += 1

        for g in r["_groups"]:
            by_group[g].append(r)

    order = ["A_EXFIL", "B_INVENTORY", "C_TRACEABILITY", "D_JAILBREAK", "E_OUT_OF_SCOPE", "OK"]
    groups_present = [g for g in order if g in by_group]

    meta_model = rows[0].get("model", "")
    meta_temp = rows[0].get("temperature", "")
    meta_embed = rows[0].get("embeddings", "")
    meta_ts = fmt_dt(rows[0].get("ts_utc"))

    total = len(rows)
    avg_score = avg(all_scores)

    anomalies = find_anomalies(rows)

    md: list[str] = []
    md.append("# Relatório de Auditoria (Test Run) — DocLens (V3)\n\n")
    md.append(f"**Run ID:** `{run_id}`  \n")
    md.append(f"**Data:** {meta_ts or '—'}  \n")
    md.append(f"**Modelo:** `{meta_model}` | **Temperature:** `{meta_temp}` | **Embeddings:** `{meta_embed}`  \n\n")

    md.append("## KPIs\n\n")
    md.append(f"- **Total de testes:** **{total}**\n")
    md.append(f"- **Ações de mitigação (≠ allow):** **{intercepted_total}/{total}**\n")
    md.append(f"- **High-risk (risk ≥ 50):** **{high_risk}/{total}**\n")
    md.append(f"- **Risco médio:** **{avg_score:.1f}**\n\n")

    md.append("## Distribuição por ação\n\n")
    md.append("| Ação | Qtde |\n|---|---:|\n")
    for a in ["allow", "block", "rewrite", "deny_out_of_scope", "unknown"]:
        if by_action.get(a, 0):
            md.append(f"| `{a}` | {by_action[a]} |\n")
    md.append("\n")

    md.append("## Resumo de classificação\n\n")
    md.append("| Grupo | Qtde | Interceptados | Test IDs | Risco médio |\n|---|---:|---:|---|---:|\n")
    for g in groups_present:
        rs = by_group[g]
        ids = [str(r.get("test_id") or "—") for r in rs]
        scores = [float(r.get("risk_score", 0) or 0) for r in rs]
        icount = sum(1 for r in rs if is_intercepted(r))
        md.append(
            f"| {GROUP_TITLES.get(g, g)} | {len(rs)} | {icount} | {', '.join(ids)} | {avg(scores):.1f} |\n"
        )
    md.append("\n")

    md.append("## Anomalias detectadas (drift / falhas de regra)\n\n")
    if anomalies:
        md.extend([x + "\n" for x in anomalies])
    else:
        md.append("- Nenhuma anomalia detectada.\n")
    md.append("\n")

    md.append("## Detalhamento por grupo\n")
    for g in groups_present:
        rs = by_group[g]
        md.append(f"\n### {GROUP_TITLES.get(g, g)}\n")
        md.append(f"{GROUP_DESC.get(g, '')}\n\n")

        def sort_key(r: dict[str, Any]):
            intercepted = 1 if is_intercepted(r) else 0
            score = float(r.get("risk_score", 0) or 0)
            tid = int(r.get("test_id", 0) or 0)
            return (-intercepted, -score, tid)

        examples = sorted(rs, key=sort_key)[:top_k]

        for r in examples:
            tid = r.get("test_id", "—")
            prompt = r.get("prompt", "")
            answer = r.get("answer", "")
            violations = r.get("violations", []) or []
            score = r.get("risk_score", 0)
            action = (r.get("action") or "").strip()
            intercepted_flag = is_intercepted(r)
            sources = unique_sources(r)

            md.append(
                f"**Teste {tid}** — action `{action}` | interceptado `{intercepted_flag}` | risco `{score}` | violações: `{', '.join(violations) if violations else '—'}`  \n"
            )
            md.append(f"- **Prompt:** {safe(prompt, 260)}  \n")
            md.append(f"- **Sources (payload):** {', '.join(sources) if sources else '—'}  \n")
            md.append(f"- **Resposta (trecho):**\n{md_codeblock(safe(answer, 900))}\n\n")

    return "".join(md)


def default_out_path(run_id: str) -> Path:
   
    filename = f"{REPORT_KIND}_run_{run_id}_{REPORT_VERSION}.md"
    return AUDIT_REPORTS_DIR / filename


def main() -> int:
    parser = argparse.ArgumentParser(description="Gera relatório Markdown (DocLens V3 | audit batch).")
    parser.add_argument(
        "--in",
        dest="in_path",
        default=str(AUDIT_RUNS_FILE),
        help="Caminho do JSONL de auditoria (audit_runs.jsonl).",
    )
    parser.add_argument(
        "--out",
        dest="out_path",
        default="",
        help="Override do caminho de saída do relatório (.md). Se vazio, usa reports/audit.",
    )
    parser.add_argument("--topk", type=int, default=TOP_K_DEFAULT, help="Itens por grupo (TOP K).")
    parser.add_argument("--run-id", default="", help="Força um run_id específico. Se vazio, usa o mais recente.")
    args = parser.parse_args()

    in_path = Path(args.in_path)
    if not in_path.exists():
        raise FileNotFoundError(f"Não achei: {in_path}")

    rows = read_jsonl(in_path)
    if not rows:
        raise RuntimeError("Nenhuma linha JSON encontrada. Verifique o arquivo de entrada.")

    run_id = args.run_id.strip() or pick_latest_run_id(rows)
    md = build_report_v3(rows, run_id=run_id, top_k=args.topk)

    out_path = Path(args.out_path) if args.out_path.strip() else default_out_path(run_id)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(md, encoding="utf-8")

    print(f"Relatório gerado: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())