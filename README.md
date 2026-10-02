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
├── main.py              # Bot do Telegram
├── server.py            # Servidor Flask
├── db_config.py         # Schema e dados de exemplo compartilhados
├── sql_generator.py     # DSPy, validação e carregamento do prompt
├── optimize_gepa.py     # Otimização offline com GEPA
├── data/gepa_train.json # Exemplos de treino
├── data/gepa_val.json   # Exemplos de validação
├── tests/               # Testes sem serviços externos
├── lojas.db
└── requirements.txt
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

- Python 3.10+ (para as dependências de áudio, prefira uma versão suportada pelo Whisper/PyTorch)
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
   pip install -r requirements.txt
   ```

3. Crie um arquivo `.env` na raiz do projeto com:
   ```env
   ApiTelegram=<token do seu bot no Telegram>
   IALOCAL=openai/<identificador do modelo servido localmente>
   apiKey=<api key exigida pelo servidor local do LLM, se houver>
   localhostServer=http://localhost:5001/
   ```

## Como executar

1. Suba o servidor Flask, que cria o banco `lojas.db` (se ainda não existir) e expõe o endpoint de execução de queries:
   ```bash
   python server.py
   ```
   O servidor sobe em `http://localhost:5001`.

2. Em outro terminal, inicie o bot do Telegram:
   ```bash
   python main.py
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


## Otimizar os prompts com GEPA

A integração usa [dspy.GEPA](https://github.com/stanfordnlp/dspy/tree/main/dspy/teleprompt/gepa)
para evoluir as instruções do `ChainOfThought(TextToSQL)`. O GEPA já é uma dependência
transitiva do DSPy 3.4+. A otimização é executada separadamente do bot.

1. Copie `.env.example` para `.env` e configure `IALOCAL`. O modelo de geração e o
   de reflexão usam `LM_API_BASE` (padrão `http://localhost:1337/v1`) e `apiKey`.
   Inicie o servidor do modelo antes de otimizar. Telegram, Whisper e Flask não
   precisam estar em execução durante a otimização.
2. Execute na raiz do projeto:
   ```bash
   python optimize_gepa.py --max-metric-calls 100
   ```
   Para usar outro modelo de reflexão disponível no mesmo endpoint, acrescente
   `--reflection-model openai/nome-do-modelo`. O orçamento limita avaliações da
   métrica, não tokens nem chamadas totais ao LLM.
3. O comando salva `artifacts/sql_gepa.json`. Acrescente ao `.env`:
   ```env
   GEPA_PROGRAM_PATH=artifacts/sql_gepa.json
   ```
4. Reinicie `python main.py`. O bot carrega o artefato uma vez ao iniciar e mantém
   a validação do SQL em cada pergunta. Sem `GEPA_PROGRAM_PATH`, usa o prompt
   original. Um caminho configurado inexistente causa erro na inicialização.

A métrica devolve uma nota (0 ou 1) e feedback textual com erros SQL ou diferenças
nos resultados. As consultas são executadas em SQLite temporário, com escrita
bloqueada e limite de instruções; `lojas.db` não é usado no treinamento. A comparação
preserva duplicatas e, quando `ordered` é verdadeiro, exige a ordem correta.

Os arquivos JSON contêm `question`, `sql_query` e `ordered` (opcional, padrão
`false`). `--train`, `--val` e `--output` permitem usar outros arquivos. Treino e
validação devem conter perguntas distintas. Os exemplos fornecidos são pequenos,
baseados nos três produtos de demonstração: igualdade de resultados nesse conjunto
não prova equivalência semântica em outros bancos. Amplie os exemplos e dados e
avalie em um conjunto de teste independente antes de concluir que houve melhoria.
Datas nos exemplos são explícitas para manter avaliações reproduzíveis.

Testes locais, sem tokens ou servidor LLM:

```bash
python -m unittest discover -s tests -v
```
