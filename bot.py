import telebot
import sqlite3
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup

# коннект с базой
conn = sqlite3.connect('channels.db')
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS channels 
                (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                name TEXT, 
                description TEXT, 
                category TEXT)''')
conn.commit()

# ботконнект
bot = telebot.TeleBot("5841252911:AAHF2doAJsRw6ucdmng8Yzq7tJnXkfihJCI")

user_passwords = {}

@bot.message_handler(commands=['start'])
def handle_start(message):
    chat_id = message.chat.id
    # Создаем кнопки
    keyboard = [[InlineKeyboardButton("Добавить канал", callback_data='add_channel')]]
    # Создаем объект разметки
    reply_markup = InlineKeyboardMarkup(keyboard)
    # ответка на кнопку старт
    bot.send_message(chat_id, 'Привет! Я могу предложить тебе каналы на основе твоих интересов. Просто пиши их мне по одному и я что-нибудь подберу.')

# Обработчик нажатия на кнопку
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == "add_channel":
        # Запускаем код для добавления канала
        add_channel(call.message)

# Обработчик команды /cancel
@bot.message_handler(commands=['cancel'])
def handle_cancel(message):
    chat_id = message.chat.id
    # Ответ на команду /cancel
    bot.send_message(chat_id, 'Выход из режима добавления канала')
    
    # Удаляем текущее состояние пользователя из базы данных
    conn = sqlite3.connect('channels.db')
    cursor = conn.cursor()
    cursor.execute

@bot.message_handler(commands=['usercount'])
def handle_usercount(message):
    user_count = bot.get_chat_members_count(message.chat.id).wait()
    bot.send_message(message.chat.id, f"Количество пользователей: {user_count}")

@bot.message_handler(func=lambda message: True)
def handle_user_input(message):
    chat_id = message.chat.id
    if message.content_type == 'text':
        lower_message_text = message.text.lower()

        if lower_message_text.startswith('/add_channel'):
            add_channel(message)
        else:
            interests = lower_message_text.split(',')
            # ищем каналы в базе данных
            channels = find_channels_by_interests(interests)
            if channels:
                # формируем сообщение со списком каналов
                message_text = 'Каналы по вашим интересам:\n\n'
                for channel in channels:
                    message_text += f"{channel[0]} - {channel[1]}\n"
                bot.send_message(chat_id, message_text)
            else:
                bot.send_message(chat_id, 'К сожалению, по вашим интересам ничего не найдено, но если у вас есть подходящие каналы вы можете их добавить командой /add_channel.')

def find_channels_by_interests(interests):
    conn = sqlite3.connect('channels.db')
    cursor = conn.cursor()
    # формируем запрос на поиск каналов по интересам
    query = "SELECT name, description FROM channels WHERE category IN ({seq})".format(seq=','.join(['?']*len(interests)))
    cursor.execute(query, interests)
    channels = cursor.fetchall()
    return channels

@bot.message_handler(commands=['add_channel'])
def add_channel(message):
    # Отправляем пользователю сообщение с инструкцией по добавлению канала
    bot.send_message(message.chat.id, "Введите название канала с @. Пример: @crypton_off. Либо отмените команду прописав /cancel")
    
    # Устанавливаем состояние "ожидание названия канала"
    def ask_channel_name(message):
        # Приводим название канала к нижнему регистру
        name = message.text.lower()
        # Проверяем, что название канала начинается с символа @
        if message.text.startswith('@'):
            # Сохраняем название канала, введённое пользователем
            name = message.text
            # Спрашиваем у пользователя описание канала
            bot.send_message(message.chat.id, "Введите описание канала:")
            # Устанавливаем состояние "ожидание описания канала"
            bot.register_next_step_handler(message, ask_channel_description, name)
        else:
            # Отправляем сообщение об ошибке, если название канала не начинается с символа @
            bot.send_message(message.chat.id, "Название канала должно начинаться со знака @. Попробуйте еще раз.")
            # Устанавливаем состояние "ожидание названия канала"
            bot.register_next_step_handler(message, ask_channel_name)
    
    # Устанавливаем состояние "ожидание названия канала"
    bot.register_next_step_handler(message, ask_channel_name)

def ask_channel_description(message, name):
    # Сохраняем описание канала, введённое пользователем
    description = message.text
    # Спрашиваем у пользователя категорию канала
    bot.send_message(message.chat.id, "Введите категорию канала:")
    # Устанавливаем состояние "ожидание категории канала"
    bot.register_next_step_handler(message, save_channel, name, description)

def save_channel(message, name, description):
    # Сохраняем категорию канала, введённую пользователем
    category = message.text
    # Приводим категорию к нижнему регистру перед сохранением в базу данных
    category_lower = category.lower()
    # Проверяем, существует ли канал с таким же названием в базе данных
    conn = sqlite3.connect('channels.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM channels WHERE name=?", (name,))
    result = cursor.fetchone()

    # Если канал с таким же названием уже существует, сообщаем пользователю об этом
    if result:
        bot.send_message(message.chat.id, f"Канал с названием '{name}' уже существует в базе данных!")
    else:
        # Проверяем, существует ли канал с таким же описанием в базе данных
        cursor.execute("SELECT * FROM channels WHERE description=?", (description,))
        result = cursor.fetchone()
        if result:
            bot.send_message(message.chat.id, f"Канал с таким же описанием уже существует в базе данных!")
        else:
            # Добавляем данные о новом канале в базу данных
            cursor.execute("INSERT INTO channels (name, description, category) VALUES (?, ?, ?)", (name, description, category_lower))
            conn.commit()
            # Отправляем сообщение пользователю об успешном добавлении канала
            bot.send_message(message.chat.id, "Канал успешно добавлен в базу данных!")

bot.polling()