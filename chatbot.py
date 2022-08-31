import telebot
from telebot import types
from telebot.types import LabeledPrice, ShippingOption
import config
from collections import defaultdict
from datetime import time
import random
import sqlite3


reply_buttons = ['🔥 Услуги', '☎ Заявка', '💡 FAQ', '📝 Компания',
                 '👩‍ Спросить', '🥇 Отзывы', '💰 Оплатить']
from_lang = {'f_lang': ['Перевод с английского',
                        'Перевод с немецкого',
                        'Перевод с испанского',
                        'Перевод с итальянского',
                        'Перевод с французского',
                        'Перевод с китайского',
                        'Перевод с японского'],
             'call_back': ['from_en',
                           'from_de',
                           'from_es',
                           'from_it',
                           'from_fr',
                           'from_zh',
                           'from_ja']}

to_lang = {'to_lang': ['Перевод на английский',
                       'Перевод на немецкий',
                       'Перевод на испанский',
                       'Перевод на итальянский',
                       'Перевод на французский',
                       'Перевод на китайский',
                       'Перевод на японский'],
           'call_back': ['to_en',
                         'to_de',
                         'to_es',
                         'to_it',
                         'to_fr',
                         'to_zh',
                         'to_ja']}

review_list = {1: 'Отзыв 1',
               2: 'Отзыв 2',
               3: 'Отзыв 3'}

START, TITLE, LANGS, EMAIL, PHONE, FILE, CONFIRMATION, PAYMENT = range(8)
USER_STATE = defaultdict(lambda: START)
USER_REQUEST = defaultdict(lambda: {})

my_id = config.MY_ID

# @BotFather -> Bot Settings -> Payments
provider_token = config.PAYMENT_TOKEN
prices = [LabeledPrice(label='Заказ на письменный перевод', amount=5750),
          LabeledPrice('Верстка', 500)]
shipping_options = [
    ShippingOption(id='instant', title='Доп. услуги').add_price(LabeledPrice(
        'Верстка', 300)),
    ShippingOption(id='pickup', title='Доп. услуги').add_price(LabeledPrice(
        'Предоставление оборудования', 1000))]

# Loading of text data of company information
def textfile_load(filename):
    f = open(filename, 'r', encoding='UTF-8')
    text = f.read()
    f.close()
    return text


# Initiation of reply keyboard
def reply_keyboard(received_buttons):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = [types.KeyboardButton(c) for c in received_buttons]
    keyboard.add(*buttons)
    return keyboard


# Initiation of inline keyboard
def inline_keyboard(received_buttons, callback):
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    buttons = [types.InlineKeyboardButton(text=c, callback_data=cb)
               for c, cb in zip(received_buttons, callback)]
    keyboard.add(*buttons)
    return keyboard


# Initiation of multiline keyboard
def multiline_keyboard(received_buttons, callback):
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    for row_num in range(0, len(received_buttons[0])):
        buttons = [types.InlineKeyboardButton(
            text=received_buttons[0][row_num],
            callback_data=callback[0][row_num]),
            types.InlineKeyboardButton(
                text=received_buttons[1][row_num],
                callback_data=callback[1][row_num])]
        keyboard.add(*buttons)
    return keyboard


# Receipt of user state
def get_state(message):
    return USER_STATE[message.chat.id]


# Update of user state
def update_state(message, state):
    USER_STATE[message.chat.id] = state


# Update dict for database
def update_reqdict(user_id, key, value):
    USER_REQUEST[user_id][key] = value


# Receipt of dict for database
def get_reqdict(user_id):
    return USER_REQUEST[user_id]


# Saving and sending request data into database
# TITLE, LANGS, EMAIL, PHONE, FILE, CONFIRMATION
def save_data(message, data):
    if message:
        conn = sqlite3.connect('requests.db')
        cur = conn.cursor()
        cur.execute("""CREATE TABLE IF NOT EXISTS requests(
                   user_id INT PRIMARY KEY,
                   title TEXT,
                   langs TEXT,
                   user_email TEXT,
                   phone TEXT,
                   file_link TEXT);
                """)
        conn.commit()

        request_info = (data['user_id'],
                        data['title'],
                        data['langs'],
                        data['user_email'],
                        data['phone'],
                        data['file_link'])

        cur.execute("INSERT OR IGNORE INTO users VALUES(?, ?, ?, ?, ?, ?);",
                    request_info)
        conn.commit()
        cur.close()
    else:
        # conn = sqlite3.connect('requests.db')
        # cur = conn.cursor()
        # sql_delete_query = f"""DELETE from requests.db where user_id = {data['user_id']}"""
        # cur.execute(sql_delete_query)
        # conn.commit()
        # print('Заявка удалена')
        # cur.close()
        USER_REQUEST = {}


# Sending user info to a personal chat
def get_info_user(bot, message):
    bot.send_message(my_id, 'Свяжитесь, пожалуйста, с ' + ' '
                     + f'{message.chat.id}' + ' '
                     + f'{message.from_user.first_name}' + ' '
                     + f'{message.from_user.last_name}')


# Initiation of a chatbot
def run_bot():
    bot = telebot.TeleBot(config.TOKEN)

    @bot.message_handler(commands=['start'])
    def start_command(message, res=False):
        keyboard = reply_keyboard(reply_buttons)
        # Greeting
        bot.send_message(
            message.chat.id,
            f'Здравствуйте, {message.from_user.first_name} '
            f'{message.from_user.last_name}! Я - бот Рутекст. Благодарю за в '
            f'нашу компанию.\n' + 'Вы можете выбрать нужный раздел, нажав\n' +
            'соответствующую кнопку ниже. Или просто написать мне\n' +
            'интересующий Вас вопрос.', reply_markup=keyboard)

    @bot.message_handler(commands=['help'])
    def help_command(message):
        keyboard = inline_keyboard(['Связаться с разработчиком'],
                                   ['telegram.me/translator1986'])
        bot.send_message(message.chat.id,
                         '1) Выберите нужное действие, нажав кнопку. Или\n' +
                         '2) Отправьте сообщение с Вашим вопросом.\n',
                         reply_markup=keyboard)

    # @bot.message_handler(content_types=['text'])
    @bot.message_handler(func=lambda message: get_state(message) == START)
    # @bot.message_handler(func=lambda message: message in reply_buttons)
    def text_handle(message):
        # About us
        if message.text == '📝 Компания':
            keyboard = inline_keyboard(['О нас', 'Вакансии'],
                                       ['about-us', 'vacancies'])
            bot.send_message(message.chat.id, 'Выберите, что Вас интересует:',
                             reply_markup=keyboard)
        # FAQ
        if message.text == '💡 FAQ':
            bot.send_message(message.chat.id, textfile_load('faq'),
                             parse_mode='MarkdownV2')
        # Asking a manager
        if message.text == '👩‍ Спросить':
            bot.send_message(message.chat.id, 'Менеджер получил уведомление '
                                              'и в скором времени свяжется с'
                                              ' Вами.')
            get_info_user(bot, message)

        # A function for sending a notification to a manager
        # shall be added.
        # ---
        # Reviews
        if message.text == '🥇 Отзывы':
            keyboard = inline_keyboard(['Отзывы о нас', 'Оставить отзыв'],
                                       ['reviews', 'feedback'])
            bot.send_message(message.chat.id,
                             'Нажмите кнопку и выберите случайный отзыв:',
                             reply_markup=keyboard)
        # Services
        if message.text == '🔥 Услуги':
            keyboard = multiline_keyboard([from_lang['f_lang'],
                                           to_lang['to_lang']],
                                          [from_lang['call_back'],
                                           to_lang['call_back']])
            bot.send_message(message.chat.id, 'Выберите услугу, которая Вас '
                                              'интересует:',
                             reply_markup=keyboard)
        # Payment
        if message.text == '💰 Оплатить':
            bot.send_message(message.chat.id, 'Введите, пожалуйста, номер '
                                              'Вашей заявки:')
            update_state(message, PAYMENT)
        # Request
        if message.text == '☎ Заявка':
            bot.send_message(message.chat.id, 'Введите, пожалуйста, свое имя '
                                              'и фамилию:')
            update_state(message, TITLE)

    # START, TITLE, LANGS, EMAIL, PHONE, FILE, CONFIRMATION
    @bot.message_handler(func=lambda message: get_state(message) == TITLE)
    def handle_name(message):
        if message.text not in reply_buttons:
            update_reqdict(message.chat.id, 'user_id', message.chat.id)
            update_reqdict(message.chat.id, 'title', message.text)
            bot.send_message(message.chat.id,
                             'Выберите язык оригинала и язык, '
                             'на который требуется перевести:')
            update_state(message, LANGS)
        else:
            text_handle(message)

    @bot.message_handler(func=lambda message: get_state(message) == LANGS)
    def handle_lang(message):
        if message.text not in reply_buttons:
            update_reqdict(message.chat.id, 'langs', message.text)
            bot.send_message(message.chat.id, 'Введите Ваш e-mail:')
            update_state(message, EMAIL)
        else:
            text_handle(message)

    @bot.message_handler(func=lambda message: get_state(message) == EMAIL)
    def handle_email(message):
        if message.text not in reply_buttons:
            update_reqdict(message.chat.id, 'user_email', message.text)
            bot.send_message(message.chat.id, 'Введите Ваш номер телефона:')
            update_state(message, PHONE)
        else:
            text_handle(message)

    @bot.message_handler(func=lambda message: get_state(message) == PHONE)
    def handle_phone(message):
        if message.text not in reply_buttons:
            update_reqdict(message.chat.id, 'phone', message.text)
            bot.send_message(message.chat.id, 'Отправьте ссылку на файл:')
            update_state(message, FILE)
        else:
            text_handle(message)

    @bot.message_handler(func=lambda message: get_state(message) == FILE)
    def handle_file(message):
        if message.text not in reply_buttons:
            update_reqdict(message.chat.id, 'file_link', message.text)
            keyboard = inline_keyboard(['Да', 'Нет'],
                                       ['send_true', 'send_false'])
            bot.send_message(message.chat.id, 'Отправить заявку?',
                             reply_markup=keyboard)
            update_state(message, START)
        else:
            text_handle(message)

        # Processing of inline buttons

    @bot.callback_query_handler(func=lambda call: True)
    def iq_callback(query):
        bot.answer_callback_query(query.id)
        send_message(query.message, query.data)

    def send_message(message, data):
        if data == 'about-us':
            bot.send_message(message.chat.id,
                             textfile_load('about_us'))
        if data == 'vacancies':
            bot.send_message(message.chat.id,
                             textfile_load('vacancies'))
        if data == 'from_en':
            bot.send_message(message.chat.id,
                             'Перевод с английского')
        if data == 'to_en':
            bot.send_message(message.chat.id,
                             'Перевод на английский')
        if data == 'send_true':
            save_data(True, get_reqdict(message.chat.id))
            bot.send_message(message.chat.id,
                             f'Номер Вашей заявки {message.chat.id}. '
                             f'Менеджер уже приступил к ее обработке.')
            update_state(message, START)
        if data == 'send_false':
            save_data(False, get_reqdict(message.chat.id))
            bot.send_message(message.chat.id,
                             'Ваша заявка удалена.')
            update_state(message, START)
        if data == 'reviews':
            bot.send_message(message.chat.id,
                             f'О нас говорят следующее: '
                             f'{random.choice(list(review_list.values()))}')
        if data == 'feedback':
            bot.send_message(message.chat.id, 'Благодарим за Ваш отзыв! Он '
                                              'поможет нам стать лучше.')
            # Create a function saving client's feedback in the database
            # ---

            # A function for calculating number of words in doc, exl and other
            # readable format files shall be added in the tab Request
            #

    @bot.message_handler(func=lambda message: get_state(message) == PAYMENT)
    def handle_name(message):
        if message.text not in reply_buttons:
            bot.send_message(message.chat.id,
                             f"Я не принимаю настоящие карты. С Вашего счета "
                             f"не будут списаны деньги. Используйте данную "
                             f"карту, чтобы оплатить счет: 1111 1111 1111 "
                             f"1026, 12/22, CVC 000.\nНомер заявки: "
                             f"{message.chat.id}.\nДанный счет тестовый.",
                             parse_mode='Markdown')
            #
            # A function for extracting request data shall be realized
            #
            # Sending invoice
            bot.send_invoice(
                message.chat.id,  # chat_id
                'Заказ на перевод',  # title
                'Заказ на письменный перевод документа объемом 10 стр. с '
                'английского языка на русский. Номер заявки {}',  # description
                'Инвойс',  # invoice_payload
                provider_token,  # provider_token
                'rub',  # currency
                prices,  # prices
                start_parameter='order-example')
            update_state(message, START)
        else:
            text_handle(message)

    @bot.shipping_query_handler(func=lambda query: True)
    def shipping(shipping_query):
        print(shipping_query)
        bot.answer_shipping_query(shipping_query.id, ok=True,
                                  shipping_options=shipping_options,
                                  error_message='Ой, похоже неполадки на '
                                                'линии. Повторите платеж '
                                                'позднее!')

    @bot.pre_checkout_query_handler(func=lambda query: True)
    def checkout(pre_checkout_query):
        bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True,
                                      error_message="Злоумышленники "
                                                    "попытались украсть "
                                                    "CVV-номер Вашей карты, "
                                                    "но мы защитили их. "
                                                    "Повторите, пожалуйста,  "
                                                    "попытку через несколько "
                                                    "минут. Aliens tried to "
                                                    "steal your card's CVV, "
                                                    "but we successfully "
                                                    "protected your "
                                                    "credentials")

    @bot.message_handler(content_types=['successful_payment'])
    def got_payment(message):
        bot.send_message(message.chat.id,
                         'Ура! Спасибо за платеж! Мы обработаем Ваш заказ в '
                         'ближайшее время. '
                         'Оставайтесь на связи.\n\nНажмите кнопку '
                         '"Оплатить", чтобы сделать еще один заказ!'.format(
                             message.successful_payment.total_amount / 100,
                             message.successful_payment.currency),
                         parse_mode='Markdown')

    # Polling function
    while True:
        print('=^.^=')

        try:
            bot.polling(none_stop=True, interval=3, timeout=20)
            print('Этого не должно быть')
        except telebot.apihelper.ApiException:
            print('Проверьте связь и API')
            time.sleep(10)
        except Exception as e:
            print(e)
            time.sleep(60)


if __name__ == '__main__':
    run_bot()
