import os
from urllib.parse import quote

import dspy
import requests
import telebot
import whisper

from dotenv import load_dotenv
from db_config import config
from sql_generator import build_generator, configure_lm


load_dotenv()


class BotTelegram:
    def __init__(self, api_token, schema):
        self.api_token = api_token
        self.schema = schema
        self.generator = build_generator(
            schema, config["query"], os.getenv("GEPA_PROGRAM_PATH")
        )
        self.bot = telebot.TeleBot(self.api_token)

        self.bot.message_handler(
            content_types=["voice"]
        )(self.transcribe_voice_message)

        self.bot.message_handler(
            func=lambda message: True
        )(self.reply_hi)

    def generate(self, question):
        try:
            resultado_sql = self.generator(
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
    dspy.configure(lm=configure_lm())
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
