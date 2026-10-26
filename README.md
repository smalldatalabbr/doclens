# DocLens

**RAG com auditoria adversarial e guardrails ativos para controle de comportamento em aplicações com LLM.**

![Author](https://img.shields.io/badge/author-Jhonathan%20Domingues-lightgrey)
![License](https://img.shields.io/badge/license-MIT-blue)
![Status](https://img.shields.io/badge/status-functional-green)

![Python](https://img.shields.io/badge/python-3.10.12-blue?logo=python&logoColor=white)
![LLM](https://img.shields.io/badge/LLM-Groq-black)
![LangChain](https://img.shields.io/badge/framework-LangChain-orange)
![FAISS](https://img.shields.io/badge/RAG-FAISS-blue)
![SentenceTransformers](https://img.shields.io/badge/embeddings-SentenceTransformers-green)
![Streamlit](https://img.shields.io/badge/UI-Streamlit-red)

![DocLens](references/doclens-results.png)

---

## Visão geral

O **DocLens** é um case de aplicação de Retrieval-Augmented Generation (RAG) com mecanismos explícitos de auditoria adversarial e controle de comportamento em aplicações baseadas em Large Language Models (LLMs).

O projeto investiga como tornar sistemas RAG mais observáveis e controláveis, incorporando camadas de decisão que avaliam solicitações e respostas, identificam comportamentos de risco e aplicam políticas explícitas de tratamento.

A solução evolui de um chatbot RAG funcional para um sistema com auditoria estruturada e guardrails ativos, contemplando bloqueio de solicitações, reescrita de respostas e restrição de consultas fora do escopo documental.

## 1. O que foi construído

O case contempla três componentes evolutivos:

- **Baseline RAG:** chatbot que consulta uma base documental controlada e produz respostas com referências às fontes recuperadas.
- **Auditoria adversarial:** execução sistemática de testes para identificar comportamentos inadequados, classificar riscos e registrar evidências em logs estruturados.
- **Guardrails ativos:** mecanismos de avaliação antes e depois da geração, permitindo aplicar decisões explícitas sobre solicitações e respostas.

O objetivo é demonstrar como mecanismos de auditoria e controle podem ser integrados a uma aplicação RAG, tornando seu comportamento mais observável e permitindo intervenções baseadas em regras definidas.

## 2. Arquitetura

O fluxo combina recuperação de informação, geração de respostas e avaliação de comportamento.

1. **Ingestão documental:** preparação dos documentos utilizados como fonte de consulta.
2. **Indexação vetorial:** geração e armazenamento dos vetores em um índice FAISS.
3. **Recuperação de contexto:** seleção de trechos relevantes para a solicitação.
4. **Geração:** envio do contexto recuperado ao modelo de linguagem.
5. **Avaliação e controle:** aplicação de guardrails para analisar a solicitação e a resposta gerada.
6. **Registro e auditoria:** armazenamento das interações, decisões e informações necessárias à análise posterior.

A arquitetura diferencia a observação de falhas do controle ativo: a auditoria permite identificar comportamentos de risco, enquanto os guardrails introduzem decisões explícitas para tratar situações identificadas pelas regras implementadas.

## 3. Pipeline do sistema

O pipeline operacional segue esta sequência:

1. Ingestão e preparação da base documental.
2. Construção do índice vetorial FAISS.
3. Recuperação do contexto relevante.
4. Geração da resposta pelo LLM.
5. Avaliação da solicitação e da resposta pelos mecanismos de controle.
6. Aplicação da decisão correspondente.
7. Registro estruturado da interação.
8. Geração de relatórios técnicos de auditoria.

As decisões implementadas são:

- `allow`: permite a continuidade da interação.
- `block`: bloqueia uma interação identificada pelas regras de controle.
- `rewrite`: aplica uma estratégia de reescrita à resposta.
- `deny_out_of_scope`: recusa solicitações fora do escopo documental definido.

As decisões são registradas para permitir inspeção posterior e análise dos resultados dos testes.

## 4. Auditoria adversarial e resultados

A auditoria adversarial foi utilizada para avaliar o comportamento do sistema diante de solicitações potencialmente problemáticas, incluindo tentativas de exposição de conteúdo documental, enumeração da base de conhecimento, consultas fora do escopo e tentativas de jailbreak.

Nos testes documentados para a versão com guardrails ativos, foram registrados os seguintes resultados:

| Indicador | Resultado |
|---|---:|
| Testes adversariais executados | 15 |
| Interações interceptadas | 12 de 15 |
| Interações classificadas como alto risco | 10 de 15 |
| Anomalias operacionais após calibração das regras | Nenhuma registrada |

Os resultados indicam o comportamento observado no conjunto de testes executado. Eles não representam uma garantia de segurança geral nem demonstram que todos os tipos de ataque ou comportamento inadequado serão identificados.

Os registros das interações e os relatórios técnicos são armazenados nas pastas `data/logs/` e `reports/`, conforme o componente responsável pela execução.

## 5. Estrutura do projeto

```text
doclens/
├── app.py
│
├── audit/
│   ├── build_report.py
│   ├── prompts_phase.py
│   ├── run_tests.py
│   └── risk_rules.py
│
├── data/
│   ├── docs/
│   ├── index_faiss/
│   └── logs/
│       ├── app/
│       └── audit/
│
├── reports/
│   ├── app/
│   └── audit/
│
├── src/
│   ├── app_logger.py
│   ├── build_app_report.py
│   ├── guardrails.py
│   ├── ingest.py
│   ├── paths.py
│   ├── rag.py
│   └── vectorstore.py
│
└── README.md
```

## 6. Reprodução

### Pré-requisitos

- Python 3.10.12, conforme a versão documentada no projeto.
- Chave de API da Groq.
- Dependências listadas no arquivo `requirements.txt`.

### Configuração do ambiente

Clone o repositório e acesse a pasta do projeto:

```bash
git clone https://github.com/smalldatalabbr/doclens.git
cd doclens
```

Crie e ative um ambiente virtual:

```bash
python -m venv .venv
source .venv/bin/activate
```

No Windows PowerShell, a ativação pode ser feita com:

```powershell
.\.venv\Scripts\Activate.ps1
```

Instale as dependências:

```bash
pip install -r requirements.txt
```

### Configuração das variáveis de ambiente

Crie um arquivo `.env` na raiz do projeto:

```text
GROQ_API_KEY=sua_chave_aqui
```

Substitua o valor de exemplo por uma chave válida da API da Groq.

### Executar a aplicação

```bash
streamlit run app.py
```

### Executar a auditoria adversarial

Execute os testes:

```bash
python -m audit.run_tests
```

Em seguida, gere o relatório:

```bash
python -m audit.build_report
```

Os relatórios de auditoria são gerados no diretório `reports/audit/`.

## 7. Limitações e considerações técnicas

- **Dados sintéticos:** os dados utilizados foram desenvolvidos para simular um chatbot de consulta documental no contexto bancário, representado pela entidade SDL Bank.
- **Regras de controle:** os resultados dependem das regras e dos critérios implementados nos guardrails. A classificação de risco não deve ser interpretada como uma avaliação universal de segurança.
- **Cobertura dos testes:** o conjunto adversarial documentado é limitado e não contempla necessariamente todas as formas de ataque, ambiguidades ou comportamentos indesejados.
- **Dependência do modelo:** as respostas e os resultados podem variar conforme o modelo de linguagem, o contexto recuperado e as configurações utilizadas.
- **Uso em produção:** o funcionamento demonstrado no case não substitui avaliações de segurança, testes ampliados, monitoramento e validação específicos para um ambiente produtivo.

### Possíveis evoluções

Uma evolução técnica possível seria incorporar **julgamento semântico das respostas**, ampliando a avaliação para além das regras explícitas e permitindo analisar com maior profundidade a adequação da resposta ao contexto e à solicitação.

Essa possibilidade representa uma direção para quem desejar replicar, estender ou dar continuidade ao projeto. Não faz parte do escopo implementado nem constitui uma etapa de desenvolvimento prevista para esta versão.

## 8. Fontes e referências

- **Dataset:** dados sintéticos desenvolvidos para simular consultas documentais em um contexto bancário.
- **Groq:** API utilizada para acesso ao modelo de linguagem.
- **LangChain:** framework utilizado na composição do fluxo de recuperação e geração.
- **FAISS:** biblioteca utilizada para indexação e recuperação vetorial.
- **SentenceTransformers:** tecnologia utilizada para geração de embeddings.
- **Streamlit:** framework utilizado na interface da aplicação.

## 9. Tecnologias

- Python
- LangChain
- FAISS
- SentenceTransformers
- Groq LLM API
- Streamlit

---

## Licença

Este projeto está licenciado sob a [MIT License](LICENSE).