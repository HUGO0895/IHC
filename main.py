import html
import os
import shutil
import tempfile
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
        self.modelo_whisper = None
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
        try:
            # Baixa o áudio (.ogg) do Telegram para um arquivo temporário
            info = self.bot.get_file(message.voice.file_id)
            audio = self.bot.download_file(info.file_path)

            with tempfile.NamedTemporaryFile(
                suffix=".ogg", delete=False
            ) as arquivo:
                arquivo.write(audio)
                caminho = arquivo.name

            try:
                texto = self.whisper_transcribe(caminho)
            finally:
                os.remove(caminho)

        except Exception as error:
            print(f"Erro ao transcrever áudio: {error!r}")
            self.bot.reply_to(
                message,
                "Não foi possível transcrever o áudio."
            )
            return

        if not texto:
            self.bot.reply_to(
                message,
                "Não entendi o áudio, tente falar de novo."
            )
            return

        print(f"Transcrição: {texto}")
        resultado = self.generate(texto)

        self.bot.reply_to(
            message,
            f"Você disse: {html.escape(texto)}\n\n<pre>{html.escape(resultado)}</pre>",
            parse_mode="HTML"
        )

    def whisper_transcribe(self, filepath):
        # Carrega o modelo uma única vez (na primeira mensagem de voz)
        if self.modelo_whisper is None:
            self.modelo_whisper = whisper.load_model(
                os.getenv("WHISPER_MODEL", "base")
            )

        resultado = self.modelo_whisper.transcribe(
            filepath,
            language="pt",
            fp16=False
        )

        return resultado["text"].strip()

    def polling(self):
        self.bot.polling()


if __name__ == "__main__":
    if shutil.which("ffmpeg") is None:
        raise RuntimeError(
            "ffmpeg não encontrado. O Whisper precisa dele para ler áudio. "
            "Windows: winget install Gyan.FFmpeg | Linux/WSL: sudo apt install ffmpeg"
        )

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
