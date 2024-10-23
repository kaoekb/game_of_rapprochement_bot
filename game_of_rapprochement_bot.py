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


db= os.getenv('DB')


mongodb+srv://{db}@cluster0.w6k4v.mongodb.net/?retryWrites=true&w=majority

# Подключаемся к MongoDB


bot = telebot.TeleBot(os.getenv('Token_tg_1'))

# Проверка на существование директории для логов
log_dir = "logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# Настройка логирования в файл
log_file_path = os.path.join(log_dir, "bot.log")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file_path),  # Логи будут записываться в logs/bot.log
        logging.StreamHandler()  # Дополнительно вывод в консоль
    ]
)

admin_user_id = int(os.getenv('Your_user_ID'))

class DataBase:
    def __init__(self):
        cluster = MongoClient(mongo_uri)
        self.db = cluster["game_of_rapprochement"]
        self.users = self.db["Users"]
        self.projects = self.db["Projects"]
        self.ads = self.db["Ads"]
        self.stats = self.db["Stats"]
        self.questions_accessed = self.get_question_access_count()

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

    def get_user_count(self):
        return self.users.count_documents({})

    def increment_question_access(self):
        self.questions_accessed += 1
        self.stats.update_one({}, {"$set": {"questions_accessed": self.questions_accessed}}, upsert=True)

    def get_question_access_count(self):
        stat = self.stats.find_one()
        if stat and "questions_accessed" in stat:
            return stat["questions_accessed"]
        else:
            return 0

    # Работа с проектами
    def add_project(self, link, description):
        project_data = { 
            "link": link,
            "description": description
        }
        self.projects.insert_one(project_data)
        logging.info(f"Добавлен проект: {link}, описание: {description}")  # Логирование добавления проекта

    def get_projects(self):
        projects = list(self.projects.find())  # Преобразуем курсор в список
        logging.info(f"Загруженные проекты: {projects}")  # Логирование списка проектов
        return projects

    # Работа с рекламой
    def add_ad(self, link, description):
        ad_data = {
            "link": link,
            "description": description
        }
        self.ads.insert_one(ad_data)

    def remove_ad(self, link):
        self.ads.delete_one({"link": link})

    def get_ads(self):
        return list(self.ads.find())  # Преобразуем курсор в список

db = DataBase()

# Обработка команды /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    try:
        db.add_user(message.from_user.id, message.from_user.username)
        
        # Создаем клавиатуру
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        
        # Кнопка "Вопрос" на всю ширину
        item_question = types.KeyboardButton('Вопрос')
        
        # Маленькие кнопки "Правила" и "Проекты"
        item_rules = types.KeyboardButton('Правила')
        item_project = types.KeyboardButton('Проекты')
        
        # Добавляем кнопку "Вопрос" в отдельную строку
        markup.add(item_question)
        
        # Добавляем кнопки "Правила" и "Проекты" на одну строку
        markup.add(item_rules, item_project)
        
        # Отправляем сообщение с кастомной клавиатурой
        bot.send_message(
            message.chat.id,
            f'Привет {message.from_user.first_name}, готов начать игру? Выберите действие.',
            reply_markup=markup
        )
    except Exception as e:
        logging.error(f"Ошибка в send_welcome: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка, попробуйте позже.")


# Обработка команды /project
@bot.message_handler(commands=['project'])
def send_projects(message):
    try:
        projects = db.get_projects()
        if not projects:  # Если список проектов пуст
            bot.send_message(message.chat.id, "На данный момент нет проектов.")
        else:
            response = "Список проектов:\n"
            for project in projects:
                response += f"- [{project['link']}]({project['link']}): {project['description']}\n"
            bot.send_message(message.chat.id, response, parse_mode="Markdown")
    except Exception as e:
        logging.error(f"Ошибка в send_projects: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка, попробуйте позже.")

# Обработка команды /admin
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id == admin_user_id:
        markup = types.InlineKeyboardMarkup()
        status_button = types.InlineKeyboardButton("Статус", callback_data="status")
        ad_button = types.InlineKeyboardButton("Реклама", callback_data="ad_menu")
        logs_button = types.InlineKeyboardButton("Логи", callback_data="logs")  # Новая кнопка для логов
        markup.add(status_button, ad_button, logs_button)
        bot.send_message(message.chat.id, "Добро пожаловать в админку!", reply_markup=markup)
    else:
        bot.send_message(message.chat.id, "У вас нет прав для доступа к этой команде.")

# Обработка инлайн кнопок
@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    try:
        if call.data == "status":
            user_count = db.get_user_count()
            questions_accessed = db.get_question_access_count()
            bot.send_message(call.message.chat.id, f"Пользователей: {user_count}\nЗапросов вопросов: {questions_accessed}")
        elif call.data == "ad_menu":
            ad_markup = types.InlineKeyboardMarkup()
            add_button = types.InlineKeyboardButton("Добавить", callback_data="add_ad")
            remove_button = types.InlineKeyboardButton("Удалить", callback_data="remove_ad")
            show_ads_button = types.InlineKeyboardButton("Показать рекламу", callback_data="show_ads")
            ad_markup.add(add_button, remove_button, show_ads_button)
            bot.send_message(call.message.chat.id, "Меню рекламы", reply_markup=ad_markup)
        elif call.data == "logs":  # Обработка нажатия кнопки Логи
            send_logs(call.message)
        elif call.data == "add_ad":
            bot.send_message(call.message.chat.id, "Отправьте ссылку на канал:")
            bot.register_next_step_handler(call.message, add_ad_step_1)
        elif call.data == "remove_ad":
            bot.send_message(call.message.chat.id, "Отправьте ссылку на канал для удаления:")
            bot.register_next_step_handler(call.message, remove_ad_step_1)
        elif call.data == "show_ads":
            show_ads(call.message)
    except Exception as e:
        logging.error(f"Ошибка в callback_inline: {e}")
        bot.send_message(call.message.chat.id, "Произошла ошибка, попробуйте позже.")

# Логи
def send_logs(message):
    log_file_path = "logs/bot.log"  # Убедитесь, что путь к логам правильный
    try:
        if os.path.exists(log_file_path):
            with open(log_file_path, 'rb') as log_file:
                bot.send_document(message.chat.id, log_file)
        else:
            bot.send_message(message.chat.id, "Файл логов не найден.")
    except Exception as e:
        logging.error(f"Ошибка при отправке логов: {e}")
        bot.send_message(message.chat.id, "Не удалось отправить файл логов.")

# Вывод рекламы
def show_ads(message):
    ads = db.get_ads()  # Получаем все рекламные записи
    if len(ads) == 0:
        bot.send_message(message.chat.id, "На данный момент нет активной рекламы.")
    else:
        response = "Другие проекты:\n"
        for ad in ads:
            response += f"- [{ad['link']}]({ad['link']}): {ad['description']}\n"
        bot.send_message(message.chat.id, response, parse_mode="Markdown")

# Добавление рекламы
def add_ad_step_1(message):
    link = message.text
    bot.send_message(message.chat.id, "Отправьте описание канала:")
    bot.register_next_step_handler(message, add_ad_step_2, link)

def add_ad_step_2(message, link):
    description = message.text
    db.add_ad(link, description)
    bot.send_message(message.chat.id, "Реклама успешно добавлена!")

# Удаление рекламы
def remove_ad_step_1(message):
    link = message.text
    db.remove_ad(link)
    bot.send_message(message.chat.id, "Реклама успешно удалена!")

# Обработка текстовых сообщений
@bot.message_handler(content_types=['text'])
def bot_message(message):
    try:
        if message.chat.type == 'private':
            if message.text == 'Вопрос':
                answer_message = random.choice(question)
                bot.send_message(message.chat.id, answer_message)
                db.update_last_interaction(message.from_user.id)
                db.increment_question_access()
            elif message.text == 'Правила':
                bot.send_message(
                    message.chat.id,
                    'Правила очень просты: каждый по очереди нажимает кнопку «Вопрос» и отвечает на выпавшее сообщение. Ответ - это ключ от двери в личную историю.'
                )
            elif message.text == 'Проекты':
                show_ads(message)
    except Exception as e:
        logging.error(f"Ошибка в bot_message: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка, попробуйте позже.")

bot.polling(none_stop=True)
