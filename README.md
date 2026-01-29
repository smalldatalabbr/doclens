# DocLens

**Chatbot RAG baseado em documentos, com controle de escopo, rastreabilidade e mitigação de riscos**

![DocLens – Chatbot RAG](imagens/thumbnail.png)
---

## Visão Geral

A **DocLens** é uma Proof of Concept (POC) que demonstra a construção de um **chatbot baseado em Retrieval-Augmented Generation (RAG)** para consulta de documentos, com foco em **confiabilidade da resposta, rastreabilidade das fontes e controle explícito de escopo**.

Este repositório representa a **V1 da POC**, cujo objetivo é estabelecer um **baseline funcional**: um chatbot capaz de responder perguntas exclusivamente com base em uma base documental, citando fontes e recusando perguntas fora do escopo disponível.

A partir desse baseline, versões posteriores da POC evoluem para **auditoria adversarial e implementação de mecanismos de controle (guardrails)**, culminando em um sistema conversacional blindado e previsível.

---

## Problema

Chatbots baseados em IA vêm sendo amplamente utilizados para consulta de documentos, políticas internas e bases de conhecimento. Apesar disso, é comum que esses sistemas apresentem falhas como respostas fora de escopo, extrapolação do conteúdo disponível ou uso indevido de fontes.

Antes de implementar mecanismos de controle, é fundamental estabelecer um **baseline funcional e rastreável**, que permita observar o comportamento do sistema e identificar seus limites reais.

Esta V1 da DocLens atende exatamente a esse propósito.

---

## O que esta V1 entrega

* Chatbot RAG funcional com histórico de conversa
* Recuperação semântica de documentos utilizando FAISS
* Respostas ancoradas exclusivamente na base documental
* Exibição explícita das fontes utilizadas em cada resposta
* Recusa clara para perguntas fora do escopo da base de conhecimento

---

## Abordagem

Nesta fase inicial, o foco está em **funcionamento e rastreabilidade**, e não em blindagem ou mitigação de falhas.

A POC utiliza documentação sintética de um banco fictício (“SDL Bank”) como base de conhecimento, permitindo simular um cenário real de consulta documental sem o uso de dados sensíveis.

Essa abordagem cria as condições necessárias para que versões futuras da POC possam:

* submeter o sistema a testes adversariais,
* identificar falhas recorrentes,
* e implementar mecanismos explícitos de controle e mitigação de riscos.

---

## Estrutura do Projeto

```
├─ app.py
├─ src/
│ ├─ settings.py
│ ├─ ingest.py
│ ├─ vectorstore.py
│ └─ rag.py
├─ imagens/
│ └─ thumbnail.png
└─ data/
   ├─ docs/          # base de conhecimento (documentação sintética em Markdown)
   └─ index_faiss/   # índice FAISS gerado automaticamente
```

---

## Como executar

### Ambiente virtual

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Variáveis de ambiente

Crie um arquivo `.env`:

```env
GROQ_API_KEY=sua_chave_aqui
```

### Execução

```bash
streamlit run app.py
```

Na primeira execução, o índice vetorial é criado automaticamente a partir dos documentos disponíveis.

---

## Status da POC

* **V1 - Baseline funcional:** concluída
* **V2 - Auditoria e identificação de falhas:** em desenvolvimento
* **V3 - Implementação de guardrails e consolidação:** planejada

---

## Licença

Este projeto está licenciado sob os termos da **MIT License**.
Consulte o arquivo `LICENSE` para mais detalhes.

---

## Disclaimer

Este projeto é uma **Proof of Concept (POC)** desenvolvida com fins demonstrativos, voltada à avaliação de arquiteturas de chatbots baseados em IA e práticas de uso responsável.

A entidade “SDL Bank” é inteiramente fictícia.
Todos os dados utilizados são sintéticos, não representam pessoas reais e não contêm informações sensíveis.

Este projeto **não deve ser utilizado em ambientes produtivos ou com dados reais**.

---

## Contato

**Jhonathan Domingues**

🌐 [Portifólio](https://jhonathan.me) | 💼 [Linkedin](https://www.linkedin.com/in/jhonathandomingues)

