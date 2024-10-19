import telebot
import random
from telebot import types
from pymongo import MongoClient
from datetime import datetime
import os
from dotenv import load_dotenv, find_dotenv
import logging

load_dotenv(find_dotenv())
from question import question

bot = telebot.TeleBot(os.getenv('Token_tg'))
logging.basicConfig(level=logging.INFO)

class DataBase:
    def __init__(self):
        cluster = MongoClient(os.getenv('Token_MDB'))
        self.db = cluster["game_of_rapprochement"]
        self.users = self.db["Users"]

    def add_user(self, user_id, username):
        if not self.users.find_one({"_id": user_id}):
            user_data = {
                "_id": user_id,
                "username": username,
                "last_interaction": datetime.now()
            }
            self.users.insert_one(user_data)
        else:
            self.update_last_interaction(user_id)

    def update_last_interaction(self, user_id):
        self.users.update_one({"_id": user_id}, {"$set": {"last_interaction": datetime.now()}})

db = DataBase()

@bot.message_handler(commands=['start'])
def send_welcome(message):
    try:
        db.add_user(message.from_user.id, message.from_user.username)
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        item_question = types.KeyboardButton('Вопрос')
        item_rules = types.KeyboardButton('Правила')
        markup.add(item_question, item_rules)
        bot.send_message(
            message.chat.id,
            f'Привет {message.from_user.first_name}, готов начать игру? Выберите действие.',
            reply_markup=markup
        )
    except Exception as e:
        logging.error(f"Ошибка в send_welcome: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка, попробуйте позже.")

@bot.message_handler(content_types=['text'])
def bot_message(message):
    try:
        if message.chat.type == 'private':
            if message.text == 'Вопрос':
                answer_message = random.choice(question)
                bot.send_message(message.chat.id, answer_message)
                db.update_last_interaction(message.from_user.id)
            elif message.text == 'Правила':
                bot.send_message(
                    message.chat.id,
                    'Правила очень просты: каждый по очереди нажимает кнопку «Вопрос» и отвечает на выпавшее сообщение. Ответ - это ключ от двери в личную историю.'
                )
    except Exception as e:
        logging.error(f"Ошибка в bot_message: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка, попробуйте позже.")

bot.polling(none_stop=True)
