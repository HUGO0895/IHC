import os
import re
import sqlite3
from urllib.parse import quote

import dspy
import requests
import telebot
import whisper

from dotenv import load_dotenv
from server import config


load_dotenv()


modelo = dspy.LM(
    os.getenv("IALOCAL"),
    api_base="http://localhost:1337/v1",
    api_key="local"
)

dspy.configure(lm=modelo)


class TextToSQL(dspy.Signature):
    """
    Gera uma consulta SQL a partir de uma pergunta em linguagem natural.
    """

    dbschema = dspy.InputField(
        desc="Database schema"
    )

    question = dspy.InputField(
        desc="Natural language question"
    )

    sql_query = dspy.OutputField(
        desc="Valid SQL query"
    )


class SqlValidator:
    def __init__(self, schema, data):
        self.schema = schema
        self.data = data

    def isSelectOnly(self, query):
        regex = (
            r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|TRUNCATE|"
            r"GRANT|REVOKE|CREATE|EXEC|MERGE)\b"
        )

        comando_perigoso = re.search(
            regex,
            query,
            re.IGNORECASE
        )

        if comando_perigoso:
            raise ValueError(
                "Essa query não possui somente SELECT"
            )

        return True

    def testeSql(self, query):
        conexao = None

        try:
            conexao = sqlite3.connect(":memory:")
            cursor = conexao.cursor()

            cursor.execute(self.schema)

            cursor.executemany(
                self.data[0],
                self.data[1]
            )

            cursor.execute(query)
            conexao.commit()

        except Exception as error:
            print(error)
            raise

        finally:
            if conexao:
                conexao.close()


class ReliableSQLGenerator(dspy.Module):
    def __init__(self, sql_validator):
        super().__init__()

        self.generate_sql = dspy.ChainOfThought(TextToSQL)
        self.sql_validator = sql_validator

    def forward(self, schema, question):
        resultado = self.generate_sql(
            dbschema=schema,
            question=question
        )

        self.sql_validator.testeSql(
            resultado.sql_query
        )

        self.sql_validator.isSelectOnly(
            resultado.sql_query
        )

        print(resultado)

        return resultado


class BotTelegram:
    def __init__(self, api_token, schema):
        self.api_token = api_token
        self.schema = schema
        self.bot = telebot.TeleBot(self.api_token)

        self.bot.message_handler(
            content_types=["voice"]
        )(self.transcribe_voice_message)

        self.bot.message_handler(
            func=lambda message: True
        )(self.reply_hi)

    def generate(self, question):
        try:
            validator = SqlValidator(
                config["schema"],
                config["query"]
            )

            generator = ReliableSQLGenerator(
                validator
            )

            resultado_sql = generator(
                schema=self.schema,
                question=question
            )

            query = quote(
                resultado_sql.sql_query,
                safe=""
            )

            endereco = os.getenv(
                "localhostServer",
                "http://127.0.0.1:5001/"
            )

            resposta = requests.get(
                endereco + query
            )

            resposta.raise_for_status()

            return resposta.text

        except Exception as error:
            print(error)

            return (
                "Não foi possível gerar/executar a query"
            )

    def reply_hi(self, message):
        resultado = self.generate(message.text)

        self.bot.send_message(
            chat_id=message.chat.id,
            text=f"<pre>{resultado}</pre>",
            parse_mode="HTML"
        )

    def transcribe_voice_message(self, message):
        file_id = message.voice.file_id

        file_path = self.bot.get_file_url(file_id)

        texto = self.whisper_transcribe(
            file_path
        )

        resultado = self.generate(texto)

        self.bot.reply_to(
            message,
            resultado
        )

    def whisper_transcribe(
        self,
        filepath,
        model="tiny"
    ):
        modelo_whisper = whisper.load_model(model)

        resultado = modelo_whisper.transcribe(
            filepath
        )

        return resultado["text"]

    def polling(self):
        self.bot.polling()


if __name__ == "__main__":
    token = os.getenv("ApiTelegram")

    if not token:
        raise ValueError(
            "A variável ApiTelegram não foi configurada no .env"
        )

    bot = BotTelegram(
        token,
        config["schema"]
    )

    bot.polling()
