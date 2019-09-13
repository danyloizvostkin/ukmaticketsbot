# bot.py
import requests
import os
from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy


BOT_URL = f'https://api.telegram.org/bot{os.environ["BOT_KEY"]}/'

# business logic const
ADMIN_CHAT_ID = os.environ["ADMIN_CHAT_ID"]
MESSAGE_URL = BOT_URL + 'sendMessage'

callback_texts = {
    'button1': "Метро (46 поїздок) - 148 грн.",
    'button2': "Метро - Автобус (46 поїздок) - 289 грн.",
    'button3': "Метро - Тролейбус (46 поїздок) - 289 грн.",
    'button4': "Метро - Трамвай (46 поїздок) - 289 грн.",
    'button5': "Метро 62 поїздок) - 199 грн.",
    'button6': "Метро - Автобус (62 поїздки) - 340 грн.",
    'button7': "Метро - Тролейбус (62 поїздки) - 340 грн.",
    'button8': "Метро - Трамвай (62 поїздки) - 340 грн.",
    'button9': "Метро (Безліміт) - 309 грн.",
    'button10': "Метро - Автобус (Безліміт) - 436 грн.",
    'button11': "Метро - Тролейбус (Безліміт) - 436 грн.",
    'button12': "Метро - Трамвай (Безліміт) - 436 грн.",
}

greetings_keyboard = [
    [{
        "text": callback_texts["button1"],
        "callback_data": "button1"
    }],
    [{
        "text": callback_texts["button2"],
        "callback_data": "button2"
    }],
    [{
        "text": callback_texts["button3"],
        "callback_data": "button3"
    }],
    [{
        "text": callback_texts["button4"],
        "callback_data": "button4"
    }],
    [{
        "text": callback_texts["button5"],
        "callback_data": "button5"
    }],
    [{
        "text": callback_texts["button6"],
        "callback_data": "button6"
    }],
    [{
        "text": callback_texts["button7"],
        "callback_data": "button7"
    }],
    [{
        "text": callback_texts["button8"],
        "callback_data": "button8"
    }],
    [{
        "text": callback_texts["button9"],
        "callback_data": "button9"
    }],
    [{
        "text": callback_texts["button10"],
        "callback_data": "button10"
    }],
    [{
        "text": callback_texts["button11"],
        "callback_data": "button11"
    }],
    [{
        "text": callback_texts["button12"],
        "callback_data": "button12"
    }]
]

payment_keyboard = [
    [{
        "text": "Уже оплатив",
        "callback_data": "payment_done"
    }]
]

# db configs
POSTGRES_URL = os.environ["POSTGRES_URL"]
POSTGRES_USER = os.environ["POSTGRES_USER"]
POSTGRES_PW = os.environ["POSTGRES_PW"]
POSTGRES_DB = os.environ["POSTGRES_DB"]
DB_URL = 'postgresql+psycopg2://{user}:{pw}@{url}/{db}'.format(user=POSTGRES_USER,pw=POSTGRES_PW,url=POSTGRES_URL,db=POSTGRES_DB)


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = DB_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class User(db.Model):
    chat_id = db.Column(db.Integer, primary_key=True)
    chat_state = db.Column(db.Integer, unique=False, nullable=False)
    name = db.Column(db.String(200), unique=False, nullable=True)
    surname = db.Column(db.String(200), unique=False, nullable=True)
    bilet_type = db.Column(db.String(200), unique=False, nullable=True)
    purchase_time = db.Column(db.String(200), unique=False, nullable=True)


db.create_all()


@app.route('/', methods=['POST'])
def handle():
    input_data = request.json
    print(input_data)  # heroku logs

    if 'message' in input_data:
        chat_id = input_data['message']['from']['id']
        firstname = input_data['message']['from']['first_name']

    if 'callback_query' in input_data:
        chat_id = input_data['callback_query']['from']['id']
        callback = input_data['callback_query']['data']
        callback_handler(chat_id, callback)

    message = ''
    try:
        message = input_data['message']['text'] # TODO check if text exist
    except:
        pass

    if message != '':
        if message == '/start':
            send_message_with_keyboard(chat_id, "Привіт, %s\nОбери тип проїздного на жовтень, який тобі потрібен:" % firstname, greetings_keyboard)
            user = User(chat_id=chat_id, chat_state=0)
            try:
                db.session.add(user)
                db.session.commit()
            except:
                print("init user data error")
        else:
            if user_state(chat_id) == 1:
                username = input_data['message']['from']['username']
                save_purchase_time(chat_id, message)
                send_message_to_admin(message="%s %s" % ("@%s" % username, message))
                send_message_to_user(chat_id=chat_id, message="Дякую! Проїздний буде готовий приблизно 28 вересня")
                update_user_state(chat_id, 0)
            else:
                send_message_with_keyboard(chat_id, "Вибачте, бот Вас не розуміє :(\nНатисніть на один із запропонованих варіантів нижче", greetings_keyboard)

    return ''


def callback_handler(chat_id, callback):
    if callback in callback_texts:
        send_message_with_keyboard(chat_id=chat_id,
                                   message="Чудово, твій вибір: проїздний %s\nЗдійсни оплату на картку Приватбанк - 123456789012 Ізв Д.О. та натисни кнопку \"Уже оплатив!\"" % callback_texts[callback],
                                   keyboard=payment_keyboard)
        set_user_bilet_type(chat_id, callback_texts[callback])
    elif callback == "payment_done":
        update_user_state(chat_id, 1)
        send_message_to_user(chat_id=chat_id, message="Введіть час здійснення переказу коштів:")


def send_message_to_user(chat_id, message):
    send_data = {
        "chat_id": chat_id,
        "text": message,
    }
    requests.post(MESSAGE_URL, json=send_data)


def send_message_with_keyboard(chat_id, message, keyboard):
    send_data = {
        "chat_id": chat_id,
        "text": message,
        "reply_markup": {
            "inline_keyboard": keyboard
        }
    }
    print(send_data)
    requests.post(MESSAGE_URL, json=send_data)
    print("keyboard sent")

def send_message_to_admin(message):
    send_message_to_user(ADMIN_CHAT_ID, message)


def update_user_state(chat_id, new_state):
    user = User.query.filter_by(chat_id=chat_id).first()
    user.chat_state = new_state
    db.session.commit()


def user_state(chat_id):
    return User.query.filter_by(chat_id=chat_id).first().chat_state


def save_purchase_time(chat_id, time):
    user = User.query.filter_by(chat_id=chat_id).first()
    user.purchase_time = time
    db.session.commit()

def set_user_bilet_type(chat_id, bilet_type):
    user = User.query.filter_by(chat_id=chat_id).first()
    user.bilet_type = bilet_type
    db.session.commit()


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
