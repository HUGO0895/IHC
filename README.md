# IHC — Bot de Telegram para consultas em linguagem natural (Text-to-SQL)

Bot de Telegram que converte perguntas em **linguagem natural** (texto ou áudio) em consultas **SQL**, executa essas consultas contra um banco de dados SQLite e responde ao usuário com o resultado formatado em tabela. A geração do SQL é feita com **DSPy** usando um modelo de linguagem (LLM) local.

## Como funciona

1. O usuário envia uma mensagem (texto ou áudio) para o bot no Telegram.
2. Se for áudio, a mensagem é transcrita com **Whisper**.
3. O texto é enviado ao gerador de SQL (`ReliableSQLGenerator`, construído com **DSPy**), que usa um LLM local para transformar a pergunta em uma query SQL, com base no schema do banco.
4. Antes de ser aceita, a query passa por validação (`SqlValidator`):
   - é executada em um banco SQLite **em memória** (cópia do schema/dados) para garantir que é sintaticamente válida;
   - é checada por regex para garantir que é **somente leitura** (`SELECT`), bloqueando `INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, etc.
5. A query validada é enviada via HTTP para um servidor **Flask** local, que a executa no banco SQLite real (`lojas.db`) e devolve o resultado.
6. O bot formata o resultado como uma tabela em texto (via `Descritor`) e responde ao usuário no Telegram.

## Estrutura do projeto

```
.
├── ia/
│   ├── initBot.py        # Ponto de entrada do bot do Telegram
│   ├── bot.py             # Classe BotTelegram: recebe mensagens/áudio e responde
│   ├── sqlGnerator.py     # ReliableSQLGenerator (módulo DSPy que gera e valida o SQL)
│   ├── sqlValidator.py    # Validação de segurança e sintaxe do SQL gerado
│   └── txtTosql.py        # Signature DSPy (TextToSQL) que descreve o schema para o LLM
├── server/
│   ├── initServer.py      # Servidor Flask que executa as queries no banco
│   ├── dbClass.py          # Camada de acesso ao SQLite (cria o banco se não existir)
│   ├── descritor.py         # Formata o resultado da query como tabela em texto
│   ├── config.py             # Schema do banco, dados de seed e path do banco
│   └── lojas.db                # Banco SQLite (tabela "produtos")
├── requierements.txt
└── .gitignore
```

## Tecnologias

- **Python**
- **[DSPy](https://github.com/stanfordnlp/dspy)** — geração do SQL a partir de linguagem natural, usando um LLM local (compatível com API OpenAI, ex. LM Studio) em `http://localhost:1337/v1`
- **pyTelegramBotAPI (`telebot`)** — integração com o Telegram
- **OpenAI Whisper** — transcrição de mensagens de voz
- **Flask** — servidor HTTP que executa as queries no banco
- **SQLite** — banco de dados (tabela `produtos`: nome, departamento, data de vencimento, data de cadastro)
- **python-dotenv** — variáveis de ambiente

## Pré-requisitos

- Python 3.10+
- Um LLM local servido em uma API compatível com OpenAI (ex. [LM Studio](https://lmstudio.ai/)) rodando em `http://localhost:1337/v1`
- Um bot criado no [BotFather](https://t.me/BotFather) do Telegram (para obter o token)

## Instalação

1. Clone o repositório:
   ```bash
   git clone https://github.com/HUGO0895/IHC.git
   cd IHC
   ```

2. Instale as dependências:
   ```bash
   pip install -r requierements.txt
   ```

3. Crie um arquivo `.env` na raiz do projeto com:
   ```env
   ApiTelegram=<token do seu bot no Telegram>
   IALOCAL=<nome/identificador do modelo servido localmente>
   apiKey=<api key exigida pelo servidor local do LLM, se houver>
   localhostServer=http://localhost:5001/
   ```

## Como executar

1. Suba o servidor Flask, que cria o banco `lojas.db` (se ainda não existir) e expõe o endpoint de execução de queries:
   ```bash
   python -m server.initServer
   ```
   O servidor sobe em `http://localhost:5001`.

2. Em outro terminal, inicie o bot do Telegram:
   ```bash
   python -m ia.initBot
   ```

3. Envie uma mensagem de texto ou um áudio para o bot no Telegram perguntando algo sobre os produtos cadastrados (ex.: *"quais produtos são da categoria bebidas?"*). O bot irá gerar o SQL, validá-lo e responder com o resultado formatado em tabela.

## Banco de dados

Tabela `produtos`:

| Coluna            | Tipo |
|-------------------|------|
| id                | INTEGER (PK) |
| nome              | TEXT |
| departamento      | TEXT |
| data_vencimento   | TEXT |
| data_cadastro     | TEXT |

O banco já é populado com alguns produtos de exemplo na primeira execução.

## Segurança

Toda query gerada pelo LLM passa por validação antes de ser executada no banco real: é testada em um SQLite em memória e é bloqueada caso contenha qualquer comando além de `SELECT` (ex. `INSERT`, `UPDATE`, `DELETE`, `DROP`).

## Status

Projeto acadêmico (disciplina de IHC) explorando interação em linguagem natural com um banco de dados via bot de Telegram, DSPy e um LLM local.
