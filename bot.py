import dspy
from dbClass import dbCreator
import telebot
import whisper
import json
from sqlGnerator import ReliableSQLGenerator
from dotenv import load_dotenv
import os
load_dotenv()
lm = dspy.LM('openai/gemma-4-E2B-it-Q4_K_S', api_base='http://localhost:1337/v1', api_key='not-needed')
dspy.configure(lm=lm)
class BotTelegram():
    def __init__(self,api_token,schema):
        self.apiToken=api_token
        self.schema=schema
        self.bot=telebot.TeleBot(self.apiToken)
        self.bot.message_handler(func=lambda message: True)(self.reply_hi)
        self.bot.message_handler(content_types=['voice'])(self.transcribe_voice_message)
    def generate(self,question):
        schema =self.schema
        generator = ReliableSQLGenerator()
        sql = generator.forward(schema, question)
        print(sql)
        print(sql.sql_query)
        results = dbCreator.cursor_executeSelect(sql.sql_query)
        return results

    
    def reply_hi(self,message):
        result = self.generate(message.text)
        self.bot.reply_to(message, json.dumps(result))

    def transcribe_voice_message(self,message):
        file_id = message.voice.file_id
        # Get url to audio file.
        file_path = self.bot.get_file_url(file_id)

        # Transcribe the audio using Whisper AI
        text = self.whisper_transcribe(file_path)

        result = self.generate(text)
        self.bot.reply_to(message, json.dumps(result))

    def whisper_transcribe(self,filepath: str, model="tiny") -> str:
        """
        Function to perform ASR on a .mp3 file
        :param filepath: Path to the .mp3 audiofile.
        :param model: Set the model type for whisper
        ["tiny", "base", "small", "medium", "large"].
        Larger model means more parameters, higher memory requirements and
        slower speed.
        :return: transcribed audio.
        """
        # Choose tiny model for faster output.
        model = whisper.load_model(model)
        result = model.transcribe(filepath)

        return result["text"]

    def begin_to_pulling(self):
        self.bot.polling()


myBot=BotTelegram(os.getenv('ApiTelegram'),dbCreator.schema)

myBot.begin_to_pulling()