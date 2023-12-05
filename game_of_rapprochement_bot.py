import telebot
import random
from telebot import types
from pymongo import MongoClient
from datetime import datetime
import os
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())
from question import question
bot = telebot.TeleBot(os.getenv('Token_tg'))


class DataBase:
    def __init__(self):
        cluster = MongoClient(os.getenv('Token_MDB'))
        self.db = cluster["game_of_rapprochement"]
        self.users = self.db["Users"]

    def add_user(self, user_id, username):
        user_data = {
            "_id": user_id,
            "username": username,
            "last_interaction": datetime.now()
        }
        self.users.update_one({"_id": user_id}, {"$set": user_data}, upsert=True)

    def update_last_interaction(self, user_id):
        self.users.update_one({"_id": user_id}, {"$set": {"last_interaction": datetime.now()}})


db = DataBase()

@bot.message_handler(commands=['start', 'Вопрос'])
def send_welcome(message):
    db.add_user(message.from_user.id, message.from_user.username)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item = types.KeyboardButton('Вопрос')
    markup.add(item)
    bot.send_message(message.chat.id, 'Привет {0.first_name}, наверняка вы не раз испытывали это ощущение: вроде, болтаешь о чём-то с новым знакомым, но разговор не клеится и кажется пустым. \n     Эти вопросы придуманы для тех, кто хочет наполнить беседы смыслом. После нескольких ответов, любой незнакомец станет будто старый приятель, которого знаешь сто лет. \n     Играть можно как вдвоём, так и компанией. правила очень просты: каждый по очереди нажимает кнопку «Вопрос» и отвечает на выпавшее сообщение. Ответ - это ключ от двери в личную историю. Время игры неограниченно: вы можете остановиться на одном вопросе и обсуждать его весь вечер или быстро перейти к следующим. Начнём?'.format(message.from_user), reply_markup=markup)

@bot.message_handler(content_types=['text'])
def bot_message(message):
    if message.chat.type == 'private':
        if message.text == 'Вопрос':
            answer_message = random.choice(question)
            bot.send_message(message.chat.id, answer_message)
            db.update_last_interaction(message.from_user.id)


bot.polling()
