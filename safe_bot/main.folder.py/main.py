#импорт необходимых функций
import os
import sqlite3
import datetime
import telebot
from telebot import types

#хранение данных
user_data = {}
registrated_users = {}
incident_data = {}
broadcast_data = {}

REG_NAME = 1
RENAME_FULL = 2

# токен бота(ключ), ID админа
ADMIN_ID = id
BOT_TOKEN = 'token'
bot = telebot.TeleBot(BOT_TOKEN)


# ------------------------ ИНИЦИАЛИЗАЦИЯ БАЗЫ ДАННЫХ -------------------------

def init_database():
#база данных для хранения регистрационных данных пользователей
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            full_name TEXT NOT NULL,
            registration_date TEXT
        )
    ''')
    conn.commit()
    conn.close()

# Функция для получения ФИО пользователя из базы данных
def get_user_full_name(user_id):
    try:
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute("SELECT full_name FROM users WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return result[0]
        else:
            return "Пользователь не найден в базе"
    except Exception as e:
        print(f"Ошибка при получении ФИО: {e}")
        return "Ошибка получения данных"

# Функция для сохранения регистрационных данных
def save_user_registration(user_id, full_name):
    try:
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        registration_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute(
            "INSERT OR REPLACE INTO users (user_id, full_name, registration_date) VALUES (?, ?, ?)",
            (user_id, full_name, registration_date)
        )
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Ошибка при сохранении пользователя: {e}")
        return False

# Инициализируем базу данных при запуске
init_database()

# клавиатуры
def get_main_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item1 = types.KeyboardButton("Контакты и поддержка 📞")
    item2 = types.KeyboardButton("Мой профиль 👤")
    item3 = types.KeyboardButton("Документы и правила 📖")
    item4 = types.KeyboardButton("Сообщить об инциденте ⚠️")
    item5 = types.KeyboardButton("О чат-боте 👾")
    markup.add(item1)
    markup.add(item2) 
    markup.add(item3)
    markup.add(item4)
    markup.add(item5)
    return markup

def get_profile_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    it1 = types.KeyboardButton('✏️Переименовать профиль')
    it2 = types.KeyboardButton('🗑️Удалить профиль')
    it3 = types.KeyboardButton('🔙Вернуться в меню')
    markup.add(it1)
    markup.add(it2)
    markup.add(it3)
    return markup

def delete_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    i1 = types.KeyboardButton('✅ Да, удалить')
    i2 = types.KeyboardButton('❌ Нет, отмена')
    markup.add(i1)
    markup.add(i2)
    return markup

# -------------------ОБРАБОТЧИК КОМАНДЫ /START -------------------------------
@bot.message_handler(commands=['start'])
def main(message):
    bot.send_message(message.chat.id, f'Привет, {message.from_user.first_name}! Рад приветствовать тебя в нашей команде!!! Этот бот - ваш быстрый доступ к правилам и инструментам для безопасной работы.')
    user_id = message.from_user.id
    if user_id in registrated_users:
        welcome_text = f'С возвращением, {registrated_users[user_id]["name"]}!'
        bot.send_message(message.chat.id, 
                         welcome_text, 
                         reply_markup=get_main_keyboard())
    else:
        bot.send_message(
            message.chat.id,
            f'Здравствуйте, {message.from_user.first_name}! Давайте познакомимся.\n\nВведите свою фамилию, имя и отчество. (например: Иванов Иван Иванович):'
        )
        user_data[user_id] = {'state': REG_NAME}

# ---------------------- ОБРАБОТЧИКИ РЕГИСТРАЦИИ -----------------------------
@bot.message_handler(func=lambda message: message.from_user.id in user_data and user_data[message.from_user.id].get('state') == REG_NAME)
def handle_registration(message):
    user_id = message.from_user.id
    user_name = message.text
    registrated_users[user_id] = {
        'name': user_name,
        'user_id': user_id,
        'username': message.from_user.username,
        'first_name': message.from_user.first_name
    }
# Сохраняем в базу данных
    save_user_registration(user_id, user_name)
    
    bot.send_message(
        message.chat.id,
        f'Регистрация завершена!\n\n'
        f'Ваши данные:\n'
        f'ФИО: {user_name}\n\n'
        f'Теперь вам доступны функции бота!', 
        reply_markup=get_main_keyboard()
    )
    del user_data[user_id]

@bot.message_handler(func=lambda message: message.from_user.id in user_data and user_data[message.from_user.id].get('state') == RENAME_FULL)
def handle_rename(message):
    user_id = message.from_user.id
    new_nik = message.text.strip()
    if not new_nik:
        bot.send_message(message.chat.id, "Данные не могут быть пустыми. Попробуйте снова.")
        return
    registrated_users[user_id]['name'] = new_nik

 # Обновляем в базе данных
    save_user_registration(user_id, new_nik)
    
    bot.send_message(
        message.chat.id,
        f"Данные обновлены!\n\n"
        f"Новые данные: {new_nik}"
    )
    del user_data[user_id]

# ------------------------ ОБРАБОТЧИКИ ДЛЯ ИНЦИДЕНТОВ ----------------------------
@bot.message_handler(func=lambda message: message.from_user.id in incident_data and incident_data[message.from_user.id]['stage'] == 'waiting_for_text')
def handle_incident_text(message):
    user_id = message.from_user.id
    print(f"Обработка текста инцидента от пользователя {user_id}")  # Отладка
    
# Сохраняем текст инцидента
    incident_data[user_id]['text'] = message.text
    incident_data[user_id]['stage'] = 'waiting_for_media'
    incident_data[user_id]['message_id'] = message.message_id
    
# Определяем, является ли пользователь администратором
    if user_id == ADMIN_ID:
        # Для администратора - сразу отправляем всем
        markup = types.InlineKeyboardMarkup(row_width=2)
        send_button = types.InlineKeyboardButton("📤 Отправить всем", callback_data="send_incident_to_all")
        cancel_button = types.InlineKeyboardButton("❌ Отмена", callback_data="cancel_incident")
        markup.add(send_button, cancel_button)
        
        bot.send_message(
            message.chat.id,
            "📢 *Вы администратор*\n\n"
            "Вы можете отправить это сообщение как рассылку ВСЕМ пользователям.\n\n"
            "Текст сообщения:\n"
            f"_{message.text}_\n\n"
            "При необходимости прикрепите фото или видео, затем нажмите 'Отправить всем'.",
            parse_mode="Markdown",
            reply_markup=markup
        )
    else:
        # Для обычного пользователя - спрашиваем про медиа
        markup = types.InlineKeyboardMarkup(row_width=2)
        skip_button = types.InlineKeyboardButton("⏭ Пропустить", callback_data="skip_media")
        send_button = types.InlineKeyboardButton("📤 Отправить", callback_data="send_incident")
        markup.add(skip_button)
        markup.add(send_button)
        
        bot.send_message(
            message.chat.id,
            "📸 *Прикрепите медиафайлы*\n\n"
            "Теперь вы можете прикрепить фото или видео (до 10 файлов).\n"
            "После завершения нажмите кнопку 'Отправить'.",
            parse_mode="Markdown",
            reply_markup=markup
        )

@bot.message_handler(content_types=['photo'], func=lambda message: message.from_user.id in incident_data and incident_data[message.from_user.id]['stage'] == 'waiting_for_media')
def handle_incident_photo(message):
    user_id = message.from_user.id
    print(f"Обработка фото от пользователя {user_id}")  # Отладка
    
# Инициализируем список медиа, если его нет
    if 'media' not in incident_data[user_id]:
        incident_data[user_id]['media'] = []
    
# Получаем file_id самого большого фото
    file_id = message.photo[-1].file_id
    incident_data[user_id]['media'].append({
        'type': 'photo',
        'file_id': file_id
    })
    
# Подтверждаем получение
    bot.reply_to(
        message,
        f"✅ Фото получено (всего: {len(incident_data[user_id]['media'])}). "
        "Вы можете добавить еще или нажать 'Отправить'."
    )

@bot.message_handler(content_types=['video'], func=lambda message: message.from_user.id in incident_data and incident_data[message.from_user.id]['stage'] == 'waiting_for_media')
def handle_incident_video(message):
    user_id = message.from_user.id
    print(f"Обработка видео от пользователя {user_id}")  # Отладка
    
# Инициализируем список медиа, если его нет
    if 'media' not in incident_data[user_id]:
        incident_data[user_id]['media'] = []
    
# Сохраняем информацию о видео
    incident_data[user_id]['media'].append({
        'type': 'video',
        'file_id': message.video.file_id
    })
    
# Подтверждаем получение
    bot.reply_to(
        message,
        f"✅ Видео получено (всего: {len(incident_data[user_id]['media'])}). "
        "Вы можете добавить еще или нажать 'Отправить'."
    )

# -------------------------- ОСНОВНОЙ ОБРАБОТЧИК МЕНЮ ------------------------------
@bot.message_handler(func=lambda message: True)
def handle_main_menu(message):
    user_id = message.from_user.id
    print(f"Обработка меню от пользователя {user_id}: {message.text}")  # Отладка

# Контакты и поддержка
    if message.text == 'Контакты и поддержка 📞':
        contacts_text = "Выберите нужный раздел:"
        markup = types.InlineKeyboardMarkup(row_width=1)
        btn_1 = types.InlineKeyboardButton("👥 Контакты сотрудников", callback_data="contacts_employees")
        btn_2 = types.InlineKeyboardButton("🤖 Поддержка бота", callback_data="contacts_support")
        markup.add(btn_1)
        markup.add(btn_2)

        bot.send_message(message.chat.id, 
                         contacts_text, 
                         parse_mode="Markdown", 
                         reply_markup=markup)
        return

# Мой профиль
    if message.text == 'Мой профиль 👤':
        if user_id in registrated_users:
            user = registrated_users[user_id]
            profile_text = f"""
___Мой профиль___ 
ID: {message.from_user.id}
Имя пользователя: @{message.from_user.username}
ФИО: {user['name']}
            """
            bot.send_message(message.chat.id, 
                             profile_text, 
                             parse_mode="Markdown")
            bot.send_message(message.chat.id, 
                             "Действия с профилем:", 
                             reply_markup=get_profile_keyboard())
        else:
            bot.send_message(message.chat.id, "Профиль не найден. Пожалуйста, выполните /start.")
        return

# Вернуться в меню
    if message.text == '🔙Вернуться в меню':
        bot.send_message(message.chat.id, "Вы вернулись в главное меню", reply_markup=get_main_keyboard())
        return

# Переименовать профиль
    if message.text == "✏️Переименовать профиль":
        if user_id in registrated_users:
            bot.send_message(
                message.chat.id,
                f"Переименовать профиль\n\n"
                f"Текущие данные: {registrated_users[user_id]['name']}\n\n"
                f"Введите новые данные:",
                parse_mode='Markdown'
            )
            user_data[user_id] = {'state': RENAME_FULL}
        else:
            bot.send_message(message.chat.id, "Профиль не найден. Выполните /start.")
        return

# Удалить профиль
    if message.text == "🗑️Удалить профиль":
        if user_id in registrated_users:
            confirm_text = f"""
Вы уверены что хотите удалить свой профиль?
ID: {message.from_user.id}
Имя пользователя: @{message.from_user.username}"""
            bot.send_message(message.chat.id, 
                             confirm_text, 
                             parse_mode='Markdown', 
                             reply_markup=delete_keyboard())
        else:
            bot.send_message(message.chat.id, "Профиль не найден. Выполните /start.")
        return

# Подтверждение удаления
    if message.text == "✅ Да, удалить":
        deleted_user = registrated_users.pop(user_id, None)
        if deleted_user:
            bot.send_message(
                message.chat.id,
                f"✅ Профиль успешно удален!\n\n"
                f"Данные пользователя {deleted_user['name']} удалены.\n\n"
                f"Чтобы начать заново, напишите /start",
                parse_mode='Markdown',
                reply_markup=types.ReplyKeyboardRemove()
            )
        else:
            bot.send_message(message.chat.id, "❌ Ошибка при удалении профиля.", reply_markup=get_main_keyboard())
        return

# Отмена удаления
    if message.text == "❌ Нет, отмена":
        bot.send_message(message.chat.id, "✅ Удаление отменено.", reply_markup=get_main_keyboard())
        return

# Документы и правила
    if message.text == 'Документы и правила 📖':
        document_text = "Выберите нужный раздел:"
        markup = types.InlineKeyboardMarkup(row_width=1)
        btn_1 = types.InlineKeyboardButton("📄 Шаблоны", callback_data="documents_templates")
        btn_2 = types.InlineKeyboardButton("📁 Официальные", callback_data="documents_official")
        markup.add(btn_1, btn_2)
        bot.send_message(message.chat.id, 
                         document_text, 
                         parse_mode="Markdown", 
                         reply_markup=markup)
        return

# Сообщить об инциденте
    if message.text == "Сообщить об инциденте ⚠️":
# Проверяем, зарегистрирован ли пользователь
        if user_id not in registrated_users:
            bot.send_message(
                message.chat.id,
                "❌ Для отправки сообщения об инциденте необходимо зарегистрироваться.\n\n"
                "Нажмите /start для регистрации."
            )
            return
        
# Запрашиваем описание инцидента
        markup = types.InlineKeyboardMarkup()
        cancel_button = types.InlineKeyboardButton("❌ Отмена", callback_data="cancel_incident")
        markup.add(cancel_button)
        
        bot.send_message(
            message.chat.id,
            "🚨 *Сообщение об инциденте*\n\n"
            "Пожалуйста, опишите проблему подробно. "
            "Если есть возможность, прикрепите фото или видео.\n\n"
            "📝 *Напишите ваше сообщение:*",
            parse_mode="Markdown",
            reply_markup=markup
        )
        
# Устанавливаем состояние ожидания сообщения об инциденте
        incident_data[user_id] = {'stage': 'waiting_for_text'}
        print(f"Инцидент инициирован для пользователя {user_id}")  # Отладка
        return

# О чат-боте
    if message.text == "О чат-боте 👾":
        bot.send_message(
            message.chat.id, 
            "Этот бот помогает с управлением профилем, доступом к документам и правилам, "
            "а также позволяет отправлять сообщения об инцидентах администратору."
        )
        return

# -------------------------- ОБРАБОТЧИК КОЛБЭКОВ ------------------------------
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    user_id = call.from_user.id
    print(f"Callback от пользователя {user_id}: {call.data}")  # Отладка

    # Сначала проверяем, относится ли callback к рассылке
    if call.data.startswith('broadcast_'):
        handle_broadcast_callbacks(call)
        return

# Контакты и поддержка
    if call.data == "contacts_employees":
        employees_text = """
👥 КОНТАКТЫ СОТРУДНИКОВ КОМПАНИИ

👷 Диспетчерская/ЦИТС: +7 (999) 999-99-99
☎️ Горячая линия безопасности: +7 (999) 999-99-99
🧑‍💻 Help Desk (ИТ-поддержка): +7 (999) 999-99-99
📑 HR-служба/Отдел кадров: +7 (999) 999-99-99
💵 Бухгалтерия: +7(999) 999-99-99
☎️ Горячая линия компании: +7 (999) 999-99-99

━━━━━━━━━━━━━━━━━━━━━
По рабочим вопросам обращайтесь к соответствующим сотрудникам.
        """
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              text=employees_text, parse_mode="Markdown")
        navigation_markup = types.InlineKeyboardMarkup(row_width=2)
        back_button = types.InlineKeyboardButton("🔙 Назад к выбору", callback_data="back_to_contacts")
        navigation_markup.add(back_button)
        bot.send_message(call.message.chat.id, 
                         "Выберите дальнейшее действие:", 
                         reply_markup=navigation_markup)

    elif call.data == "contacts_support":
        support_text = """
🤖 ПОДДЕРЖКА БОТА

Выберите способ связи с поддержкой:
        """
        support_markup = types.InlineKeyboardMarkup(row_width=1)
        admin_button = types.InlineKeyboardButton("👨‍💼 Написать администратору", url="https://t.me/bot_admin_username")
        email_button = types.InlineKeyboardButton("📧 Отправить email", url="mailto:support@botcompany.com")
        phone_button = types.InlineKeyboardButton("📱 Позвонить", url="tel:+7(999)999-99-99")
        back_button = types.InlineKeyboardButton("🔙 Назад к выбору", callback_data="back_to_contacts")
        support_markup.add(admin_button)
        support_markup.add(email_button)
        support_markup.add(phone_button)
        support_markup.add(back_button)
        bot.edit_message_text(chat_id=call.message.chat.id, 
                              message_id=call.message.message_id,
                              text=support_text, 
                              parse_mode="Markdown", 
                              reply_markup=support_markup)

    elif call.data == "back_to_contacts":
        choice_text = "📞 КОНТАКТЫ И ПОДДЕРЖКА:"
        markup = types.InlineKeyboardMarkup(row_width=1)
        btn_employees = types.InlineKeyboardButton("👥 Контакты сотрудников", callback_data="contacts_employees")
        btn_support = types.InlineKeyboardButton("🤖 Поддержка бота", callback_data="contacts_support")
        markup.add(btn_employees)
        markup.add(btn_support)
        bot.edit_message_text(chat_id=call.message.chat.id,
                            message_id=call.message.message_id,
                            text=choice_text, 
                            parse_mode="Markdown", 
                            reply_markup=markup)

    elif call.data == "main_menu":
        bot.edit_message_reply_markup(chat_id=call.message.chat.id, 
                                      message_id=call.message.message_id, 
                                      reply_markup=None)
        bot.send_message(call.message.chat.id, 
                         "Вы вернулись в главное меню.", 
                         reply_markup=get_main_keyboard())
        bot.answer_callback_query(call.id)

# Документы и правила
    elif call.data == "documents_templates":
        templates_text = "Выберите нужный шаблон для скачивания:"
        all_templates_markup = types.InlineKeyboardMarkup(row_width=1)
        one_button = types.InlineKeyboardButton("🏖️Шаблон заявления на отпуск", callback_data="template_vacation")
        two_button = types.InlineKeyboardButton("📑Шаблон договора", callback_data="template_contract")
        thr_button = types.InlineKeyboardButton("✅Шаблон акта выполненных работ", callback_data="template_act")
        fou_button = types.InlineKeyboardButton("📃Шаблон служебной записки", callback_data="template_memo")
        back_button = types.InlineKeyboardButton("🔙 Назад", callback_data="back_to_documents")
        all_templates_markup.add(one_button)
        all_templates_markup.add(two_button)
        all_templates_markup.add(thr_button)
        all_templates_markup.add(fou_button)
        all_templates_markup.add(back_button)
        bot.edit_message_text(chat_id=call.message.chat.id, 
                              message_id=call.message.message_id,
                              text=templates_text, 
                              parse_mode="Markdown", 
                              reply_markup=all_templates_markup)

    elif call.data == "template_vacation":
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(BASE_DIR, 'templates', 'vacation.docx')
        try:
            with open(path, 'rb') as file:
                bot.send_document(chat_id=call.message.chat.id, document=file,
                                  caption="🏖️ Шаблон заявления на отпуск\n\nСкачайте файл и заполните его.")
        except FileNotFoundError:
            bot.answer_callback_query(call.id, "Файл временно недоступен. Попробуйте позже.", show_alert=True)


    elif call.data == "template_contract":
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(BASE_DIR, 'templates', 'contract_template.docx')
        try:
            with open(path, 'rb') as file:
                bot.send_document(chat_id=call.message.chat.id, document=file,
                                  caption="📑 Шаблон договора\n\nСкачайте файл и заполните его.")
        except FileNotFoundError:
            bot.answer_callback_query(call.id, "Файл временно недоступен. Попробуйте позже.", show_alert=True)


    elif call.data == "template_act":
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(BASE_DIR, 'templates', 'act_template.docx')
        try:
            with open(path, 'rb') as file:
                bot.send_document(chat_id=call.message.chat.id, document=file,
                                  caption="✅ Шаблон акта выполненных работ\n\nСкачайте файл и заполните его.")
        except FileNotFoundError:
            bot.answer_callback_query(call.id, "Файл временно недоступен. Попробуйте позже.", show_alert=True)


    elif call.data == "template_memo":
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(BASE_DIR, 'templates', 'memo_template.docx')
        try:
            with open(path, 'rb') as file:
                bot.send_document(chat_id=call.message.chat.id, 
                                  document=file,
                                  caption="📃 Шаблон служебной записки\n\nСкачайте файл и заполните его.")
        except FileNotFoundError:
            bot.answer_callback_query(call.id, "Файл временно недоступен. Попробуйте позже.", show_alert=True)


    elif call.data == "back_to_documents":
        document_text = "Выберите нужный раздел:"
        markup = types.InlineKeyboardMarkup(row_width=1)
        btn_1 = types.InlineKeyboardButton("📄 Шаблоны", callback_data="documents_templates")
        btn_2 = types.InlineKeyboardButton("📁 Официальные", callback_data="documents_official")
        markup.add(btn_1)
        markup.add(btn_2)
        bot.edit_message_text(chat_id=call.message.chat.id, 
                              message_id=call.message.message_id,
                              text=document_text, 
                              parse_mode="Markdown", 
                              reply_markup=markup)

    elif call.data == "documents_official":
        bot.answer_callback_query(call.id, "Раздел в разработке", show_alert=True)

# Инциденты
    elif call.data == "cancel_incident":
        if user_id in incident_data:
            del incident_data[user_id]
        bot.edit_message_text(chat_id=call.message.chat.id, 
                              message_id=call.message.message_id,
                              text="❌ Отправка сообщения об инциденте отменена.", 
                              parse_mode="Markdown")
        bot.send_message(call.message.chat.id, 
                         "Вы можете продолжить работу с ботом.", 
                         reply_markup=get_main_keyboard())

    elif call.data == "skip_media":
        if user_id in incident_data:
            send_incident_report(call.message, user_id)

    elif call.data == "send_incident":
        if user_id in incident_data:
            send_incident_report(call.message, user_id)
            
    elif call.data == "send_incident_to_all":
        if user_id in incident_data and user_id == ADMIN_ID:
            send_admin_incident_to_all(call.message, user_id)

# ------------------------ ФУНКЦИЯ ОТПРАВКИ ИНЦИДЕНТА (для обычных пользователей) ---------------------------------
def send_incident_report(message, user_id):
    """Функция для отправки сообщения об инциденте администратору"""
    
# Получаем данные пользователя
    user_data = incident_data.get(user_id)
    if not user_data:
        bot.send_message(message.chat.id, "❌ Ошибка: данные не найдены")
        return
    
# Получаем ФИО пользователя из registrated_users
    if user_id in registrated_users:
        full_name = registrated_users[user_id]['name']
    else:
        full_name = "Пользователь не найден в системе"
    
# Получаем username если есть
    username = message.from_user.username if message.from_user.username else "нет username"
    
# Формируем текст сообщения для администратора
    report_text = f"""
🚨 *НОВЫЙ ИНЦИДЕНТ*

👤 *Отправитель:* {full_name}
🆔 *ID:* `{user_id}`
👤 *Username:* @{username}
📅 *Дата и время:* {datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")}

📝 *Описание инцидента:*
{user_data['text']}

---
*Сообщение отправлено из бота*
"""
    
    print(f"Отправка инцидента от {full_name} администратору")  # Отладка
    
# Отправляем сообщение администратору
    try:
# Если есть медиафайлы
        if 'media' in user_data and user_data['media']:
            if len(user_data['media']) == 1:
                media = user_data['media'][0]
                if media['type'] == 'photo':
                    bot.send_photo(ADMIN_ID, photo=media['file_id'], caption=report_text, parse_mode="Markdown")
                elif media['type'] == 'video':
                    bot.send_video(ADMIN_ID, video=media['file_id'], caption=report_text, parse_mode="Markdown")
            else:
                media_group = []
                for i, media in enumerate(user_data['media']):
                    if i == 0:
                        if media['type'] == 'photo':
                            media_group.append(types.InputMediaPhoto(media=media['file_id'], caption=report_text, parse_mode="Markdown"))
                        elif media['type'] == 'video':
                            media_group.append(types.InputMediaVideo(media=media['file_id'], caption=report_text, parse_mode="Markdown"))
                    else:
                        if media['type'] == 'photo':
                            media_group.append(types.InputMediaPhoto(media=media['file_id']))
                        elif media['type'] == 'video':
                            media_group.append(types.InputMediaVideo(media=media['file_id']))
                bot.send_media_group(ADMIN_ID, media_group)
        else:
            bot.send_message(ADMIN_ID, report_text, parse_mode="Markdown")
        
# Подтверждаем пользователю
        bot.send_message(
            message.chat.id,
            "✅ *Сообщение об инциденте отправлено администратору!*\n\n"
            "Спасибо за бдительность. Мы рассмотрим ваше сообщение в ближайшее время.",
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )
        
# Очищаем временные данные
        del incident_data[user_id]
        print(f"Инцидент от пользователя {user_id} успешно отправлен")  # Отладка
        
    except Exception as e:
        print(f"Ошибка при отправке инцидента: {e}")
        bot.send_message(
            message.chat.id,
            "❌ Произошла ошибка при отправке сообщения. Попробуйте позже.",
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )

# ------------------------ ФУНКЦИЯ ОТПРАВКИ ИНЦИДЕНТА ОТ АДМИНИСТРАТОРА (ВСЕМ ПОЛЬЗОВАТЕЛЯМ) ---------------------------------
def send_admin_incident_to_all(message, admin_id):
    """Функция для отправки сообщения об инциденте от администратора всем пользователям"""
    
# Получаем данные инцидента
    admin_data = incident_data.get(admin_id)
    if not admin_data:
        bot.send_message(message.chat.id, "❌ Ошибка: данные не найдены")
        return
    
# Получаем ФИО администратора
    if admin_id in registrated_users:
        admin_name = registrated_users[admin_id]['name']
    else:
        admin_name = "Администратор"
    
# Формируем текст сообщения для пользователей
    broadcast_text = f"""
📢 *ОБЪЯВЛЕНИЕ АДМИНИСТРАТОРА*

{admin_data['text']}

---
*Сообщение отправлено администратором*
📅 {datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")}
"""
    
    print(f"Отправка объявления от администратора {admin_name} всем пользователям")  # Отладка
    
    # Получаем всех пользователей из базы данных
    try:
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM users WHERE user_id != ?", (admin_id,))  # Не отправляем самому админу
        users = cursor.fetchall()
        conn.close()
    except Exception as e:
        bot.send_message(admin_id, f"❌ Ошибка при получении списка пользователей: {e}")
        return
    
    if not users:
        bot.send_message(admin_id, "❌ В базе данных нет других зарегистрированных пользователей.")
        # Очищаем данные
        del incident_data[admin_id]
        return
    
    # Статистика отправки
    success_count = 0
    fail_count = 0
    fail_list = []
    
    # Отправляем сообщение каждому пользователю
    bot.send_message(admin_id, f"📤 Начинаю рассылку объявления...\nВсего получателей: {len(users)}")
    
    # Если есть медиафайлы
    if 'media' in admin_data and admin_data['media']:
        for user in users:
            user_id = user[0]
            try:
                if len(admin_data['media']) == 1:
                    media = admin_data['media'][0]
                    if media['type'] == 'photo':
                        bot.send_photo(user_id, photo=media['file_id'], caption=broadcast_text, parse_mode="Markdown")
                    elif media['type'] == 'video':
                        bot.send_video(user_id, video=media['file_id'], caption=broadcast_text, parse_mode="Markdown")
                else:
                    # Для нескольких медиа отправляем группой
                    media_group = []
                    for i, media in enumerate(admin_data['media']):
                        if i == 0:
                            if media['type'] == 'photo':
                                media_group.append(types.InputMediaPhoto(media=media['file_id'], caption=broadcast_text, parse_mode="Markdown"))
                            elif media['type'] == 'video':
                                media_group.append(types.InputMediaVideo(media=media['file_id'], caption=broadcast_text, parse_mode="Markdown"))
                        else:
                            if media['type'] == 'photo':
                                media_group.append(types.InputMediaPhoto(media=media['file_id']))
                            elif media['type'] == 'video':
                                media_group.append(types.InputMediaVideo(media=media['file_id']))
                    bot.send_media_group(user_id, media_group)
                success_count += 1
            except Exception as e:
                fail_count += 1
                fail_list.append(f"{user_id}: {str(e)[:50]}")
    else:
        # Отправляем только текст
        for user in users:
            user_id = user[0]
            try:
                bot.send_message(user_id, broadcast_text, parse_mode="Markdown")
                success_count += 1
            except Exception as e:
                fail_count += 1
                fail_list.append(f"{user_id}: {str(e)[:50]}")
    
    # Отправляем отчет администратору
    report = f"""
📊 *Отчет о рассылке объявления*

✅ Успешно отправлено: {success_count}
❌ Не удалось отправить: {fail_count}
👥 Всего получателей: {len(users)}
    """
    
    if fail_list and len(fail_list) <= 10:
        report += "\n\n❌ *Ошибки:*\n" + "\n".join(fail_list[:10])
    elif fail_list:
        report += f"\n\n❌ *Первые 10 ошибок из {len(fail_list)}:*\n" + "\n".join(fail_list[:10])
    
    bot.send_message(admin_id, report, parse_mode="Markdown")
    
    # Подтверждаем администратору
    bot.send_message(
        admin_id,
        "✅ *Объявление успешно разослано всем пользователям!*",
        parse_mode="Markdown",
        reply_markup=get_main_keyboard()
    )
    
    # Очищаем временные данные
    del incident_data[admin_id]

# ------------------------ РАССЫЛКА СООБЩЕНИЙ (ДЛЯ АДМИНИСТРАТОРА) -------------------------

# Команда для запуска рассылки (доступна только администратору)
@bot.message_handler(commands=['broadcast'])
def start_broadcast(message):
    user_id = message.from_user.id
    
    # Проверяем, является ли пользователь администратором
    if user_id != ADMIN_ID:
        bot.reply_to(message, "❌ У вас нет прав на выполнение этой команды.")
        return
    
    # Запрашиваем текст для рассылки
    markup = types.InlineKeyboardMarkup()
    cancel_button = types.InlineKeyboardButton("❌ Отмена", callback_data="broadcast_cancel")
    markup.add(cancel_button)
    
    msg = bot.send_message(
        message.chat.id,
        "📢 *Режим рассылки*\n\n"
        "Отправьте мне текст, который вы хотите разослать всем зарегистрированным пользователям.\n"
        "Вы можете использовать форматирование Markdown.\n\n"
        "✍️ *Введите текст сообщения:*",
        parse_mode="Markdown",
        reply_markup=markup
    )
    
    # Устанавливаем состояние ожидания текста для рассылки
    broadcast_data[user_id] = {'stage': 'waiting_for_broadcast_text', 'message_id': msg.message_id}

# Обработчик текста для рассылки
@bot.message_handler(func=lambda message: message.from_user.id in broadcast_data and broadcast_data[message.from_user.id].get('stage') == 'waiting_for_broadcast_text')
def handle_broadcast_text(message):
    user_id = message.from_user.id
    
    # Сохраняем текст рассылки
    broadcast_text = message.text
    
    # Создаем клавиатуру с опциями
    markup = types.InlineKeyboardMarkup(row_width=2)
    confirm_button = types.InlineKeyboardButton("✅ Отправить всем", callback_data="broadcast_confirm")
    edit_button = types.InlineKeyboardButton("✏️ Редактировать", callback_data="broadcast_edit")
    cancel_button = types.InlineKeyboardButton("❌ Отмена", callback_data="broadcast_cancel")
    markup.add(confirm_button, edit_button, cancel_button)
    
    # Показываем превью и запрашиваем подтверждение
    bot.send_message(
        user_id,
        f"📋 *Превью рассылки:*\n\n{broadcast_text}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"❗️ Подтвердите отправку этого сообщения ВСЕМ зарегистрированным пользователям.",
        parse_mode="Markdown",
        reply_markup=markup
    )
    
    # Сохраняем текст и переходим к подтверждению
    broadcast_data[user_id]['text'] = broadcast_text
    broadcast_data[user_id]['stage'] = 'waiting_for_broadcast_confirm'

# Обработчик добавления медиа к рассылке (опционально)
@bot.message_handler(content_types=['photo', 'video', 'document'], func=lambda message: message.from_user.id in broadcast_data and broadcast_data[message.from_user.id].get('stage') == 'waiting_for_broadcast_text')
def handle_broadcast_media(message):
    user_id = message.from_user.id
    
    # Определяем тип медиа и сохраняем file_id
    if message.content_type == 'photo':
        file_id = message.photo[-1].file_id
        media_type = 'photo'
    elif message.content_type == 'video':
        file_id = message.video.file_id
        media_type = 'video'
    elif message.content_type == 'document':
        file_id = message.document.file_id
        media_type = 'document'
        file_name = message.document.file_name
    else:
        bot.reply_to(message, "Неподдерживаемый тип файла.")
        return
    
    # Сохраняем медиа
    broadcast_data[user_id]['media'] = {
        'type': media_type,
        'file_id': file_id,
        'file_name': file_name if message.content_type == 'document' else None
    }
    
    # Подтверждаем получение
    bot.reply_to(
        message,
        f"✅ Медиафайл получен. Теперь отправьте текст сообщения или нажмите /broadcast для отмены."
    )

# Функция для выполнения рассылки
def send_broadcast(admin_id, text, media=None):
    """
    Функция для отправки сообщения всем зарегистрированным пользователям
    """
    # Получаем всех пользователей из базы данных
    try:
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM users WHERE user_id != ?", (admin_id,))  # Не отправляем самому админу
        users = cursor.fetchall()
        conn.close()
    except Exception as e:
        bot.send_message(admin_id, f"❌ Ошибка при получении списка пользователей: {e}")
        return
    
    if not users:
        bot.send_message(admin_id, "❌ В базе данных нет зарегистрированных пользователей.")
        return
    
    # Статистика отправки
    success_count = 0
    fail_count = 0
    fail_list = []
    
    # Отправляем сообщение каждому пользователю
    bot.send_message(admin_id, f"📤 Начинаю рассылку...\nВсего получателей: {len(users)}")
    
    for user in users:
        user_id = user[0]
        try:
            if media:
                if media['type'] == 'photo':
                    bot.send_photo(user_id, photo=media['file_id'], caption=text, parse_mode="Markdown")
                elif media['type'] == 'video':
                    bot.send_video(user_id, video=media['file_id'], caption=text, parse_mode="Markdown")
                elif media['type'] == 'document':
                    bot.send_document(user_id, document=media['file_id'], caption=text, parse_mode="Markdown")
            else:
                bot.send_message(user_id, text, parse_mode="Markdown")
            success_count += 1
        except Exception as e:
            fail_count += 1
            fail_list.append(f"{user_id}: {str(e)[:50]}")
    
    # Отправляем отчет администратору
    report = f"""
📊 *Отчет о рассылке*

✅ Успешно отправлено: {success_count}
❌ Не удалось отправить: {fail_count}
👥 Всего получателей: {len(users)}
    """
    
    if fail_list and len(fail_list) <= 10:
        report += "\n\n❌ *Ошибки:*\n" + "\n".join(fail_list[:10])
    elif fail_list:
        report += f"\n\n❌ *Первые 10 ошибок из {len(fail_list)}:*\n" + "\n".join(fail_list[:10])
    
    bot.send_message(admin_id, report, parse_mode="Markdown")
    
    # Очищаем данные рассылки
    if admin_id in broadcast_data:
        del broadcast_data[admin_id]

# Обработчики callback'ов для рассылки
def handle_broadcast_callbacks(call):
    user_id = call.from_user.id
    
    # Проверяем права администратора
    if user_id != ADMIN_ID:
        bot.answer_callback_query(call.id, "У вас нет прав для этого действия.", show_alert=True)
        return
    
    action = call.data.replace('broadcast_', '')
    
    if action == 'cancel':
        # Отмена рассылки
        if user_id in broadcast_data:
            del broadcast_data[user_id]
        
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="❌ Рассылка отменена.",
            parse_mode="Markdown"
        )
        bot.send_message(user_id, "Вы можете продолжить работу.", reply_markup=get_main_keyboard())
        bot.answer_callback_query(call.id)
    
    elif action == 'edit':
        # Редактирование текста
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="✏️ Отправьте новый текст для рассылки:",
            parse_mode="Markdown"
        )
        
        if user_id in broadcast_data:
            broadcast_data[user_id]['stage'] = 'waiting_for_broadcast_text'
        
        bot.answer_callback_query(call.id)
    
    elif action == 'confirm':
        # Подтверждение и запуск рассылки
        if user_id not in broadcast_data or 'text' not in broadcast_data[user_id]:
            bot.answer_callback_query(call.id, "Ошибка: данные рассылки не найдены", show_alert=True)
            return
        
        # Удаляем сообщение с подтверждением
        bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
        
        # Запускаем рассылку
        text = broadcast_data[user_id]['text']
        media = broadcast_data[user_id].get('media')
        
        send_broadcast(user_id, text, media)
        bot.answer_callback_query(call.id, "Рассылка запущена!")

# Команда /help с информацией о доступных командах
@bot.message_handler(commands=['help'])
def help_command(message):
    user_id = message.from_user.id
    
    help_text = """
📚 *Доступные команды:*

/start - Начать работу с ботом (регистрация)
/help - Показать это сообщение

    """
    
    # Добавляем информацию о команде broadcast только для администратора
    if user_id == ADMIN_ID:
        help_text += """
👑 *Команды администратора:*
/broadcast - Сделать рассылку всем пользователям
        """
    
    bot.send_message(message.chat.id, help_text, parse_mode="Markdown")

# -------------------- ЗАПУСК БОТА -------------------------
if __name__ == '__main__':
    
# Создаем папку для шаблонов, если её нет
    templates_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
    if not os.path.exists(templates_dir):
        os.makedirs(templates_dir)
        print(f"Создана папка для шаблонов: {templates_dir}")
        print("Пожалуйста, поместите файлы шаблонов в эту папку:")
        print("  - vacation.docx")
        print("  - contract_template.docx")
        print("  - act_template.docx")
        print("  - memo_template.docx")
    
    print("Бот запущен...")
    print("Нажмите Ctrl+C для остановки")
    bot.polling(none_stop=True)
