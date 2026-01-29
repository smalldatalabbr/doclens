import streamlit as st
from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage

from src.settings import DOCS_DIR, INDEX_DIR, DEFAULT_MODEL, DEFAULT_TEMPERATURE, DEFAULT_EMBEDDINGS
from src.ingest import load_documents
from src.vectorstore import build_vectorstore, save_vectorstore, load_vectorstore, make_retriever
from src.rag import load_llm, build_rag_chain

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

if "chat_history" not in st.session_state:
    st.session_state.chat_history = [
        AIMessage(content="Olá! Sou o assistente do SDL Bank. Como posso ajudar?")
    ]

for msg in st.session_state.chat_history:
    role = "assistant" if isinstance(msg, AIMessage) else "user"
    with st.chat_message(role):
        st.write(msg.content)

prompt = st.chat_input("Digite sua mensagem aqui...")

if prompt:
    st.session_state.chat_history.append(HumanMessage(content=prompt))
    with st.chat_message("user"):
        st.write(prompt)

    llm = get_llm_cached(model, temperature)
    retriever = get_retriever_cached(emb_model)
    rag_chain = build_rag_chain(llm, retriever)

    with st.chat_message("assistant"):
        answer = rag_chain.invoke({
            "question": prompt,
            "chat_history": st.session_state.chat_history
        })
        st.write(answer)

    st.session_state.chat_history.append(AIMessage(content=answer))

