# src/guardrails.py
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from audit.risk_rules import classify_risk


BLOCK_MESSAGE = (
    "Não posso ajudar com esse pedido. "
    "Posso responder perguntas objetivas sobre o conteúdo, sem revelar trechos, listar seções "
    "ou reproduzir documentos."
)

DENIAL_MESSAGE = "Não encontrei essa informação nos documentos disponíveis."

REWRITE_MESSAGE = (
    "Não posso fornecer textos exatos ou conteúdos internos do aplicativo. "
    "Posso, no entanto, descrever de forma geral os tipos de mensagens ou "
    "funcionalidades relacionadas a esse processo, sem reproduzir conteúdos específicos. "
    "Se quiser, reformule a pergunta nesse sentido."
)

@dataclass
class GuardrailDecision:
    action: str  # "allow" | "block" | "rewrite" | "deny_out_of_scope"
    blocked: bool
    risk_score: int
    groups: List[str]
    violations: List[str]
    message: Optional[str] = None


def decide_on_prompt(prompt: str) -> GuardrailDecision:
    """
    Enforcement BEFORE RAG.
    Aqui entra:
    - block: exfil / inventory / jailbreak
    - deny_out_of_scope: cross-domain
    - rewrite: pedidos de "texto exato"/verbatim etc. (controle fino)
    """
    audit = classify_risk(prompt, answer="")

    action = (audit.get("action") or "allow").strip().lower()
    groups = audit.get("groups", []) or []
    violations = audit.get("violations", []) or []
    score = int(audit.get("risk_score", 0) or 0)

    # Prioridade: fora do escopo
    if action == "deny_out_of_scope" or ("E_OUT_OF_SCOPE" in groups):
        return GuardrailDecision(
            action="deny_out_of_scope",
            blocked=True,
            risk_score=score,
            groups=groups,
            violations=violations,
            message=DENIAL_MESSAGE,
        )

    # Block duro
    if action == "block" or ("A_EXFIL" in groups) or ("B_INVENTORY" in groups) or ("D_JAILBREAK" in groups):
        return GuardrailDecision(
            action="block",
            blocked=True,
            risk_score=score,
            groups=groups,
            violations=violations,
            message=BLOCK_MESSAGE,
        )

    # Rewrite (intercepta antes do RAG)
    if action == "rewrite" or ("C_TRACEABILITY" in groups and score >= 50):
        return GuardrailDecision(
            action="rewrite",
            blocked=True,
            risk_score=score,
            groups=groups,
            violations=violations,
            message=REWRITE_MESSAGE,
        )

    return GuardrailDecision(
        action="allow",
        blocked=False,
        risk_score=score,
        groups=groups,
        violations=violations,
        message=None,
    )


def decide_on_answer(prompt: str, answer_text: str) -> GuardrailDecision:
    # Pós-RAG: valida 'comportamento' do modelo.
    audit = classify_risk(prompt, answer=answer_text)

    action = (audit.get("action") or "allow").strip().lower()
    groups = audit.get("groups", []) or []
    violations = audit.get("violations", []) or []
    score = int(audit.get("risk_score", 0) or 0)

    # Fora do escopo pode aparecer aqui também (por segurança)
    if action == "deny_out_of_scope" or ("E_OUT_OF_SCOPE" in groups):
        return GuardrailDecision(
            action="deny_out_of_scope",
            blocked=True,
            risk_score=score,
            groups=groups,
            violations=violations,
            message=DENIAL_MESSAGE,
        )

    # Block duro (caso o modelo vaze algo mesmo sem intenção clara no prompt)
    if ("A_EXFIL" in groups) or ("B_INVENTORY" in groups) or ("D_JAILBREAK" in groups):
        return GuardrailDecision(
            action="block",
            blocked=True,
            risk_score=score,
            groups=groups,
            violations=violations,
            message=BLOCK_MESSAGE,
        )

    # Regras de "comportamento ruim"
    bad = {"RAW_DOC_LEAK", "HALLUCINATED_SOURCES", "SOURCE_ON_DENIAL"}
    if any(v in bad for v in (violations or [])):
        return GuardrailDecision(
            action="rewrite",
            blocked=True,
            risk_score=score,
            groups=groups,
            violations=violations,
            message=REWRITE_MESSAGE,
        )

    return GuardrailDecision(
        action="allow",
        blocked=False,
        risk_score=score,
        groups=groups,
        violations=violations,
        message=None,
    )


def safe_denial_if_out_of_scope(prompt: str, groups: List[str]) -> Optional[str]:
    if "E_OUT_OF_SCOPE" in (groups or []):
        return DENIAL_MESSAGE
    return None
