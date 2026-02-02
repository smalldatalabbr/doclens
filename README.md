# DocLens

**Chatbot RAG baseado em documentos, com auditoria adversarial e classificação de riscos**

![DocLens – Chatbot RAG](imagens/thumbnail.png)

---

## Visão Geral

A **DocLens** é uma **Proof of Concept (POC)** que demonstra a construção, avaliação e controle de um **chatbot baseado em Retrieval-Augmented Generation (RAG)** para consulta de documentos, com foco em:

* **controle explícito de escopo**
* **rastreabilidade das respostas**
* **identificação e mitigação ativa de riscos**
* **comportamento previsível em ambientes sensíveis**

O projeto evolui de um **baseline funcional (V1)** para uma **camada formal de auditoria adversarial (V2)** e culmina na **V3**, onde **guardrails ativos passam a interferir diretamente no fluxo de decisão do chatbot**, bloqueando, reescrevendo ou negando respostas inadequadas.

---

## Problema

Chatbots RAG são amplamente utilizados para consulta de políticas internas, manuais operacionais e bases corporativas. Mesmo quando corretamente ancorados em documentos, esses sistemas frequentemente apresentam falhas como:

* exposição indevida de conteúdo documental
* enumeração de seções ou inventário da base
* respostas fora de escopo
* uso inconsistente ou inexistente de fontes
* tentativas de jailbreak parcialmente bem-sucedidas

Esses comportamentos reduzem a confiabilidade do sistema e representam riscos reais em ambientes corporativos.

Antes de aplicar bloqueios cegos, é fundamental **entender empiricamente como e onde o sistema falha** — e, a partir disso, **implementar mecanismos de controle explícitos**.

---

## Evolução da POC

### V1 — Baseline funcional

* Chatbot RAG operando sobre uma base documental controlada
* Respostas com citação de fontes
* Sem mecanismos formais de controle ou auditoria

### V2 — Auditoria adversarial (diagnóstico)

* Execução sistemática de **testes adversariais**
* Classificação automática de riscos
* Logs estruturados em JSON
* Geração de **relatórios técnicos de auditoria**
* **Sem bloqueios ativos** (sistema observável)

### V3 — Guardrails ativos e mitigação (atual)

Na V3, a DocLens deixa de ser apenas observável e passa a ser **controlável**.

O sistema implementa:

* **Guardrail pré-RAG** (análise de intenção do prompt)
* **Guardrail pós-RAG** (avaliação da resposta gerada)
* Decisão explícita por interação:

  * `allow`
  * `block`
  * `rewrite`
  * `deny_out_of_scope`
* Registro estruturado de decisões, riscos e violações
* Auditoria separada entre **execução real (app)** e **testes adversariais (batch)**

O objetivo não é censurar respostas arbitrariamente, mas **garantir previsibilidade, rastreabilidade e alinhamento ao escopo documental**.

---

## O que esta V3 entrega

* Chatbot RAG com **controle ativo de comportamento**
* Bloqueio explícito de tentativas de:

  * exfiltração de documentos
  * inventário da base
  * jailbreak
* Reescrita controlada de respostas sensíveis
* Negação formal de perguntas fora do domínio
* Logs estruturados para:

  * auditoria técnica
  * análise de falhas
  * evolução de regras
* Relatórios automáticos em Markdown:

  * **auditoria batch**
  * **execução do aplicativo**

---

## Evidência Operacional — Auditoria V3 (resumo)

A auditoria batch executada na V3 produziu, por exemplo:

* **15 testes adversariais**
* **12/15 interações interceptadas**
* **10/15 classificadas como alto risco (risk ≥ 50)**
* Nenhuma anomalia operacional após calibração das regras

Os resultados completos (prompts, decisões, riscos, fontes e respostas) são consolidados automaticamente em um **relatório técnico de auditoria**.

📄 **Relatórios gerados** ficam disponíveis na pasta [`reports/`](reports/).

---

## Estrutura do Projeto

```text
├─ app.py
│  └─ Aplicação Streamlit do chatbot RAG com guardrails ativos
│
├─ audit/
│  ├─ build_report.py        # gera relatório técnico da auditoria adversarial (batch)
│  ├─ prompts_phase.py       # conjunto de prompts adversariais para testes
│  ├─ run_tests.py           # executa testes adversariais contra o chatbot
│  └─ risk_rules.py          # definição das regras e categorias de risco (nível auditoria)
│
├─ data/
│  ├─ docs/                 # base documental sintética (Markdown – SDL Bank)
│  ├─ index_faiss/          # índice vetorial gerado automaticamente
│  └─ logs/
│     ├─ app/               # logs das interações reais do chatbot
│     └─ audit/             # logs dos testes adversariais (batch)
│
├─ imagens/
│  └─ thumbnail.png         # imagem de capa / visual do projeto
│
├─ reports/
│  ├─ app/                  # relatórios gerados a partir da execução do app
│  └─ audit/                # relatórios da auditoria adversarial (batch)
│
├─ src/
│  ├─ app_logger.py         # logging estruturado das interações do app
│  ├─ build_app_report.py   # gera relatório consolidado da execução do chatbot
│  ├─ guardrails.py         # lógica central de decisão (allow, block, rewrite, deny)
│  ├─ ingest.py             # carregamento e preparação dos documentos
│  ├─ paths.py              # centralização de caminhos e constantes do projeto
│  ├─ rag.py                # pipeline RAG (LLM + Retriever + Chain)
│  └─ vectorstore.py        # criação e carregamento do índice vetorial
│
└─ README.md

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

### Execução do chatbot (app)

```bash
streamlit run app.py
```

Ao final da sessão, os logs da execução são gravados automaticamente e podem ser convertidos em um [**relatório do app**](reports/app/),

### Execução da auditoria adversarial (V3)

```bash
python3 -m audit.run_tests
python3 -m audit.build_report
```

Ao final, um **relatório técnico em Markdown** é gerado automaticamente na pasta [`reports/audit/`](reports/audit/).

---

## Status da POC

* **V1 — Baseline funcional:** concluída
* **V2 — Auditoria adversarial:** concluída
* **V3 — Guardrails ativos e mitigação:** concluída
* **V3.1 — Julgamento semântico / prompt-as-judge:** em planejamento

---

## Licença

Este projeto está licenciado sob os termos da **MIT License**.
Consulte o arquivo `LICENSE` para mais detalhes.

---

## Disclaimer

Este projeto é uma **Proof of Concept (POC)** desenvolvida com fins demonstrativos, voltada à avaliação de arquiteturas de chatbots baseados em IA e práticas de uso responsável.

A entidade **“SDL Bank” é fictícia**.
Todos os dados utilizados são sintéticos e não representam informações reais.

Este projeto **não deve ser utilizado em ambientes produtivos**.

---

## Contato

**Jhonathan Domingues**

🌐 [Portfólio](https://jhonathan.me) | 💼 [LinkedIn](https://www.linkedin.com/in/jhonathandomingues)