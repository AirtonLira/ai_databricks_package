# 📚 DatabricksAI Core Library - Pacote Databricks para RAG

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Databricks](https://img.shields.io/badge/Databricks-Compatible-orange.svg)](https://databricks.com/)

## 🎯 Visão Geral

O **databricksAI Core Library** é um pacote Python robusto desenvolvido para facilitar a implementação de fluxos de **Retrieval-Augmented Generation (RAG)** utilizando a plataforma Databricks. Este projeto oferece uma solução completa para processamento de documentos, busca vetorial e geração de respostas contextualizadas usando LLMs.

### 🚀 Principais Funcionalidades

- **🔍 Busca Vetorial Otimizada**: Integração nativa com Databricks Vector Search
- **🤖 Suporte a Múltiplos LLMs**: Interface unificada para diversos modelos de linguagem
- **📄 Processamento de Documentos**: Suporte para múltiplos formatos (PDF, Markdown, JSON, etc.)
- **☁️ Integração AWS**: Suporte completo para S3 e Secrets Manager
- **🔧 Arquitetura Modular**: Instale apenas os componentes que você precisa
- **🛡️ AI Guardrails**: Configuração e gerenciamento de guardrails para endpoints

## 📦 Instalação

### Instalação Básica

```bash
pip install databricksai-core-lib
```

### Instalação Modular

O pacote foi projetado para permitir instalação modular de dependências:

```bash
# Funcionalidades AWS (S3, Secrets Manager)
pip install databricksai-core-lib[aws]

# Processamento de texto e markdown
pip install databricksai-core-lib[text-processing]

# Integração com Databricks
pip install databricksai-core-lib[databricks]

# Processamento de PDFs
pip install databricksai-core-lib[pdf]

# Integração com Confluence
pip install databricksai-core-lib[confluence]

# Machine Learning e embeddings
pip install databricksai-core-lib[ml]

# Instalação completa
pip install databricksai-core-lib[all]
```

## 🏗️ Arquitetura

### Estrutura do Projeto

```
databricksai-core-lib/
├── src/
│   └── databricksai_core_lib/
│       ├── ai_rag_chat_model.py      # Modelo principal de chat RAG
│       ├── ai_vector_search.py       # Interface para busca vetorial
│       ├── ai_embedding.py           # Geração de embeddings
│       ├── ai_llm_client.py          # Cliente para LLMs
│       ├── ai_storage.py             # Gerenciamento de armazenamento
│       ├── ai_confluence.py          # Integração com Confluence
│       ├── ai_github.py              # Integração com GitHub
│       └── splitters/                # Divisores de texto especializados
│           ├── ai_text_splitter.py
│           ├── ai_markdown_splitter.py
│           ├── ai_json_splitter.py
│           └── ai_open_api_splitter.py
└── v1/
    └── databricksai_core_lib/
        ├── databricks.py             # Configurações Databricks
        └── utils/                    # Utilitários diversos
```

### Componentes Principais

#### 1. **AiRagChatModel**
Classe principal que orquestra o fluxo RAG completo:
- Gerencia embeddings e busca vetorial
- Integra com LLMs para geração de respostas
- Suporta múltiplos modelos (Llama, GPT, etc.)

#### 2. **AiVectorSearch**
Interface para o Databricks Vector Search:
- Criação e gerenciamento de índices
- Busca por similaridade
- Suporte a diferentes dimensões de embedding

#### 3. **AiEmbedding**
Geração de embeddings para documentos:
- Suporte a múltiplos modelos de embedding
- Otimização para diferentes tipos de conteúdo
- Cache inteligente de embeddings

#### 4. **Splitters Especializados**
Divisores de texto otimizados para diferentes formatos:
- **TextSplitter**: Divisão inteligente de texto
- **MarkdownSplitter**: Preserva estrutura de markdown
- **JSONSplitter**: Mantém estrutura JSON válida
- **OpenAPISplitter**: Especializado em especificações OpenAPI

## 💻 Uso Básico

### Exemplo de Fluxo RAG Completo

```python
from databricksai_core_lib import AiRagChatModel

# Inicializar o modelo RAG
rag_model = AiRagChatModel(
    vector_search_endpoint_name="seu-endpoint",
    source_table_name="sua-tabela",
    llm_model_name="databricks-meta-llama-3-1-8b-instruct",
    max_tokens=8000,
    temperature=0.1,
    embedding_dimension=384
)

# Processar uma pergunta
pergunta = "Como configurar o Databricks Vector Search?"
resposta = rag_model.process_query(pergunta)
print(resposta)
```

### Processamento de Documentos

```python
from databricksai_core_lib import AiLayerProcessor
from databricksai_core_lib.splitters import AiMarkdownSplitter

# Configurar processador
processor = AiLayerProcessor()
splitter = AiMarkdownSplitter(chunk_size=1000, chunk_overlap=200)

# Processar documento
with open("documento.md", "r") as f:
    conteudo = f.read()

chunks = splitter.split_text(conteudo)
embeddings = processor.generate_embeddings(chunks)
```

### Busca Vetorial

```python
from databricksai_core_lib import AiVectorSearch

# Configurar busca vetorial
vector_search = AiVectorSearch(
    vector_search_endpoint_name="meu-endpoint",
    source_table_name="minha-tabela",
    embedding_dimension=384
)

# Realizar busca
query = "databricks vector search configuração"
resultados = vector_search.search(query, k=5)
```

## 🔧 Configuração

### Variáveis de Ambiente

```bash
# Databricks
export DATABRICKS_HOST="https://seu-workspace.cloud.databricks.com"
export DATABRICKS_TOKEN="seu-token"

# AWS (opcional)
export AWS_ACCESS_KEY_ID="sua-chave"
export AWS_SECRET_ACCESS_KEY="seu-secret"
export AWS_DEFAULT_REGION="us-east-1"
```

### Configuração de AI Guardrails

```python
from databricksai_core_lib.v1 import Databricks

# Configurar guardrails
db = Databricks(
    host=os.getenv("DATABRICKS_HOST"),
    token=os.getenv("DATABRICKS_TOKEN"),
    endpoint_name="meu-endpoint"
)

# Atualizar configurações
db.update_ai_guardrails(
    invalid_keywords=["palavra-proibida"],
    pii_behavior="BLOCK"
)
```

## 📊 Casos de Uso

### 1. **Chatbot Corporativo**
- Indexação de documentação interna
- Respostas contextualizadas baseadas em conhecimento empresarial
- Suporte multilíngue

### 2. **Assistente de Documentação Técnica**
- Processamento de documentação de APIs
- Geração de exemplos de código
- Respostas técnicas precisas

### 3. **Sistema de FAQ Inteligente**
- Indexação automática de perguntas frequentes
- Respostas dinâmicas baseadas em contexto
- Aprendizado contínuo

## 🛠️ Desenvolvimento

### Requisitos de Desenvolvimento

```bash
pip install -r requirements-dev.txt
```

### Executar Testes

```bash
pytest tests/
```

### Contribuindo

1. Fork o projeto
2. Crie sua feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📝 Licença

Este projeto está licenciado sob a Licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

## 👥 Autores

- **Airton Lira Junior** - *Trabalho Inicial* - [airtonlirajr@gmail.com](mailto:airtonlirajr@gmail.com)

## 🙏 Agradecimentos

- Time Databricks pela excelente plataforma
- Comunidade open-source pelos modelos e ferramentas
- Todos os contribuidores do projeto

## 📞 Suporte

Para suporte, envie um email para airtonlirajr@gmail.com ou abra uma issue no GitHub.

---

**⭐ Se este projeto foi útil, considere dar uma estrela no GitHub!**
