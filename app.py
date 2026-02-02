# app.py (V3)
import uuid
import streamlit as st
from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage

from src.paths import DOCS_DIR, INDEX_DIR, DEFAULT_MODEL, DEFAULT_TEMPERATURE, DEFAULT_EMBEDDINGS
from src.ingest import load_documents
from src.vectorstore import build_vectorstore, save_vectorstore, load_vectorstore, make_retriever
from src.rag import load_llm, build_rag_chain, invoke_rag

from src.guardrails import decide_on_prompt, decide_on_answer, safe_denial_if_out_of_scope
from src.app_logger import log_app_interaction

load_dotenv()

st.set_page_config(page_title="Atendimento SDL Bank 🤖", page_icon="🤖")
st.title("Atendimento SDL Bank")

# UI
model = DEFAULT_MODEL
temperature = DEFAULT_TEMPERATURE
emb_model = DEFAULT_EMBEDDINGS


@st.cache_resource
def get_llm_cached(model: str, temperature: float):
    return load_llm(model, temperature)


@st.cache_resource
def get_retriever_cached(emb_model: str):
    if INDEX_DIR.exists() and any(INDEX_DIR.iterdir()):
        vs = load_vectorstore(INDEX_DIR, emb_model)
    else:
        documents = load_documents(DOCS_DIR)
        vs = build_vectorstore(documents, emb_model)
        save_vectorstore(vs, INDEX_DIR)
    return make_retriever(vs)


@st.cache_resource
def get_chain_cached(model: str, temperature: float, emb_model: str):
    llm = get_llm_cached(model, temperature)
    retriever = get_retriever_cached(emb_model)
    return build_rag_chain(llm, retriever)


# ---- session state ----
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

# (1) contador por sessão
if "interaction_id" not in st.session_state:
    st.session_state.interaction_id = 0

if "chat_history" not in st.session_state:
    st.session_state.chat_history = [
        AIMessage(content="Olá! Sou o assistente do SDL Bank. Como posso ajudar?")
    ]


# render histórico
for msg in st.session_state.chat_history:
    role = "assistant" if isinstance(msg, AIMessage) else "user"
    with st.chat_message(role):
        st.write(msg.content)


prompt = st.chat_input("Digite sua mensagem aqui...")

if prompt:
    # (2) incrementa somente quando existe prompt (evita somar em rerun)
    st.session_state.interaction_id += 1
    current_interaction_id = st.session_state.interaction_id

    st.session_state.chat_history.append(HumanMessage(content=prompt))
    with st.chat_message("user"):
        st.write(prompt)

    # --- Guardrail PRE (intenção) ---
    pre = decide_on_prompt(prompt)

    # fora de escopo: não bloqueia, mas força negativa padrão
    forced_denial = safe_denial_if_out_of_scope(prompt, pre.groups)

    if pre.blocked:
        answer_text = pre.message or "Bloqueado."
        sources = []
        action = pre.action

        with st.chat_message("assistant"):
            st.write(answer_text)

        st.session_state.chat_history.append(AIMessage(content=answer_text))

        # (3) adiciona interaction_id no log (caminho PRE bloqueado)
        log_app_interaction(
            {
                "session_id": st.session_state.session_id,
                "interaction_id": current_interaction_id,
                "action": action,
                "prompt": prompt,
                "answer": answer_text,
                "sources": sources,
                "risk_score": pre.risk_score,
                "groups": pre.groups,
                "violations": pre.violations,
                "model": model,
                "temperature": float(temperature),
                "embeddings": emb_model,
            }
        )

    else:
        # chama chain (cacheada)
        rag_chain = get_chain_cached(model, temperature, emb_model)

        if forced_denial is not None:
            # não chama LLM para perguntas fora do escopo
            answer_text = forced_denial
            sources = []
            action = "deny_out_of_scope"
            post = None

        else:
            # --- INVOKE (V2 retorna dict: {"answer": str, "sources": list}) ---
            result = invoke_rag(rag_chain, prompt, st.session_state.chat_history)

            if isinstance(result, dict) and "answer" in result:
                answer_text = result["answer"]
                sources = result.get("sources", [])
            else:
                answer_text = str(result)
                sources = []

            # --- Guardrail POST (comportamento) ---
            post = decide_on_answer(prompt, answer_text)
            if post.blocked:
                # substitui resposta por mensagem de bloqueio/rewrite
                answer_text = post.message or answer_text
                sources = []
                action = post.action
            else:
                action = "allow"

        with st.chat_message("assistant"):
            st.write(answer_text)
            if sources:
                st.caption(f"Fontes: {len(sources)}")

        st.session_state.chat_history.append(AIMessage(content=answer_text))

        # (3) adiciona interaction_id no log (caminho normal)
        log_app_interaction(
            {
                "session_id": st.session_state.session_id,
                "interaction_id": current_interaction_id,
                "action": action,
                "prompt": prompt,
                "answer": answer_text,
                "sources": sources,
                "risk_score": (post.risk_score if post else pre.risk_score),
                "groups": (post.groups if post else pre.groups),
                "violations": (post.violations if post else pre.violations),
                "model": model,
                "temperature": float(temperature),
                "embeddings": emb_model,
            }
        )