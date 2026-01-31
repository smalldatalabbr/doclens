# DocLens

**Chatbot RAG baseado em documentos, com auditoria adversarial e classificação de riscos**

![DocLens – Chatbot RAG](imagens/thumbnail.png)

---

## Visão Geral

A **DocLens** é uma Proof of Concept (POC) que demonstra a construção e evolução de um **chatbot baseado em Retrieval-Augmented Generation (RAG)** para consulta de documentos, com foco em **rastreabilidade das respostas, controle de escopo e identificação sistemática de riscos**.

Este repositório encontra-se atualmente na **V2 da POC**, que parte de um **baseline funcional (V1)** e evolui para uma **camada explícita de auditoria adversarial**, responsável por **avaliar o comportamento do chatbot frente a prompts maliciosos, ambíguos ou fora de escopo**.

A V2 **não aplica bloqueios ativos**. Seu objetivo é **observar, classificar e quantificar falhas**, criando insumos técnicos claros para a implementação de **guardrails ativos na V3**.

---

## Problema

Chatbots RAG são amplamente utilizados para consulta de políticas, manuais e bases internas. Apesar disso, mesmo quando corretamente ancorados em documentos, esses sistemas tendem a apresentar falhas como:

* exposição indevida de conteúdo ou estrutura documental
* enumeração de seções ou inventário da base
* uso de fontes inconsistentes ou inexistentes
* extrapolação do escopo documental
* tentativas de jailbreak parcialmente bem-sucedidas

Antes de aplicar mecanismos de bloqueio, é fundamental **entender empiricamente como e onde o sistema falha**.

A V2 da DocLens foi criada exatamente para esse diagnóstico.

---

## O que esta V2 entrega

Além de manter todas as capacidades da V1, esta versão adiciona uma **camada formal de auditoria adversarial**, composta por:

* Execução de **testes adversariais** contra o chatbot RAG
* Classificação automática de riscos com base em:

  * intenção do prompt
  * comportamento da resposta
* Agrupamento de falhas por categorias (exfiltração, inventário, rastreabilidade, jailbreak e fora de escopo)
* Geração de **logs estruturados em JSON**
* Consolidação automática dos resultados em um **relatório técnico de auditoria**

📄 Um relatório completo em Markdown é gerado a partir da execução da auditoria, permitindo análise detalhada, rastreável e reprodutível dos testes realizados.

---

## Abordagem

Nesta fase, a DocLens opera como um **sistema observável**, não como um sistema blindado.

A base documental continua sendo composta por documentação sintética de um banco fictício (“SDL Bank”), o que permite simular cenários realistas sem uso de dados sensíveis.

A auditoria adversarial submete o chatbot a diferentes classes de prompts, avaliando:

* tentativas de extração integral ou parcial de documentos
* pedidos de inventário ou estrutura interna
* respostas com fontes inexistentes ou inconsistentes
* perguntas fora do domínio documental
* tentativas explícitas de ignorar regras do sistema

O resultado dessa abordagem é um **mapa claro de riscos**, utilizado como base técnica para decisões de controle na V3.

---

## Evidência de Auditoria (V2)

A auditoria executada nesta versão produziu os seguintes resultados consolidados:

* **11 testes adversariais executados**
* **7/11 testes com risco ≥ 50 (alto risco)**

| Grupo | Descrição                               | Qtde de testes | Risco médio |
| ----- | --------------------------------------- | -------------: | ----------: |
| A     | Exfiltração de conteúdo                 |              4 |        70.0 |
| B     | Inventário / estrutura interna          |              1 |        80.0 |
| C     | Rastreabilidade / fontes inconsistentes |              4 |        65.0 |
| D     | Jailbreak                               |              1 |        60.0 |
| E     | Fora do escopo                          |              2 |        15.0 |
| OK    | Sem violações                           |              2 |         0.0 |

🔗 O relatório técnico completo, contendo prompts, respostas, fontes e classificação de risco, está disponível em:

[📄 **Acesse o Relatório de Auditoria**](reports/run_20260131T133534Z.md)

---

## Estrutura do Projeto

```text
├─ app.py
├─ audit/
│ ├─ build_report.py
│ ├─ logger.py
│ ├─ prompts_phase2.py
│ ├─ risk_rules.py
│ └─ run_tests.py
├─ data/
│  ├─ docs/          # base de conhecimento (documentação sintética em Markdown)
│  ├─ index_faiss/   # índice FAISS gerado automaticamente
│  └─ logs/          # logs de auditoria
├─ imagens/
│ └─ thumbnail.png
├─ reports/
│ └─ run_20260129T200719Z.md
├─ src/
│ ├─ ingest.py
│ ├─ paths.py
│ ├─ rag.py
│ └─ vectorstore.py
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

### Execução do chatbot

```bash
streamlit run app.py
```

### Execução da auditoria (V2)

```bash
python3 -m audit.run_tests
python3 -m audit.build_report
```

Ao final da execução, os logs são processados e um **relatório de auditoria em Markdown** é gerado automaticamente.

---

## Status da POC

* **V1 — Baseline funcional:** concluída
* **V2 — Auditoria e identificação de falhas:** concluída
* **V3 — Guardrails ativos e mitigação:** em planejamento

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

🌐 [Portfólio](https://jhonathan.me) | 💼 [LinkedIn](https://www.linkedin.com/in/jhonathandomingues)
