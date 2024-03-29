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
    'button1': "Метро (46 поїздок) - 150 грн.",
    'button2': "Метро - Автобус (46 поїздок) - 290 грн.",
    'button3': "Метро - Тролейбус (46 поїздок) - 290 грн.",
    'button4': "Метро - Трамвай (46 поїздок) - 290 грн.",
    'button5': "Метро (62 поїздки) - 200 грн.",
    'button6': "Метро - Автобус (62 поїздки) - 340 грн.",
    'button7': "Метро - Тролейбус (62 поїздки) - 340 грн.",
    'button8': "Метро - Трамвай (62 поїздки) - 340 грн.",
    'button9': "Метро (Безліміт) - 310 грн.",
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
        "text": "Оплатив(-ла)!",
        "callback_data": "payment_done"
    }]
]

# db configs
POSTGRES_URL = os.environ["POSTGRES_URL"]
POSTGRES_USER = os.environ["POSTGRES_USER"]
POSTGRES_PW = os.environ["POSTGRES_PW"]
POSTGRES_DB = os.environ["POSTGRES_DB"]
DB_URL = 'postgresql+psycopg2://{user}:{pw}@{url}/{db}'.format(user=POSTGRES_USER, pw=POSTGRES_PW, url=POSTGRES_URL,
                                                               db=POSTGRES_DB)

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = DB_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class User(db.Model):
    chat_id = db.Column(db.Integer, primary_key=True)
    chat_state = db.Column(db.Integer, unique=False, nullable=False)
    username = db.Column(db.String(200), unique=False, nullable=True)
    fullname = db.Column(db.String(200), unique=False, nullable=True)
    bilet_type = db.Column(db.String(200), unique=False, nullable=True)
    purchase_time = db.Column(db.String(200), unique=False, nullable=True)


db.create_all()


@app.route('/', methods=['POST'])
def handle():
    input_data = request.json
    print(input_data)  # heroku logs

    username = "No User Name"

    if 'message' in input_data:
        chat_id = input_data['message']['from']['id']
        firstname = input_data['message']['from']['first_name']
        try:
            username = input_data['message']['from']['username']
        except:
            pass

    if 'callback_query' in input_data:
        chat_id = input_data['callback_query']['from']['id']
        callback = input_data['callback_query']['data']
        callback_handler(chat_id, callback)

    message = ''
    try:
        message = input_data['message']['text']  # TODO check if text exist
    except:
        pass

    if message != '':
        if message == '/start':
            send_message_to_user(chat_id=chat_id,
                                 message="Привіт, %s! Тебе вітає бот з закупівлі проїзних:)\nЗараз йде закупівля проїзних на Грудень 2019\nДедлайн 13 листопада о 23:55\nДля початку, напиши своє прізвище та ім'я: " % firstname)
            try:
                update_user_state(chat_id=chat_id, new_state=2)
            except:
                pass

            try:
                user = User(chat_id=chat_id, chat_state=2)
                db.session.add(user)
                db.session.commit()
            except:
                pass
        else:
            if user_state(chat_id) == -1:
                send_message_to_user(chat_id=chat_id,
                                     message="Привіт, %s! Тебе вітає бот з закупівлі проїзних:)\nЗараз йде закупівля проїзних на Грудень 2019\nДедлайн 13 листопада о 23:55\nДля початку, напиши своє прізвище та ім'я: " % firstname)
            elif user_state(chat_id) == 1:
                save_purchase_time(chat_id, message)
                set_user_username(chat_id, username)
                send_message_to_admin(message="%s %s\n%s %s" % (
                    "@%s" % username, message, get_user_fullname(chat_id=chat_id),
                    get_user_bilet_type(chat_id=chat_id)))
                send_message_to_user(chat_id=chat_id,
                                     message="Дякую, твоя відповідь записана! Якщо є якісь питання - пиши в пп @olympiadnik")
                update_user_state(chat_id, 0)
            elif user_state(chat_id) == 2:
                set_user_fullname(chat_id, message)
                send_message_with_keyboard(chat_id=chat_id,
                                           message="Обери тип проїзного, який тобі потрібен:",
                                           keyboard=greetings_keyboard)
                update_user_state(chat_id, 0)
            else:
                send_message_with_keyboard(chat_id,
                                           "Вибач, бот тебе не розуміє :(\nНатисни на один із запропонованих варіантів нижче",
                                           greetings_keyboard)
    return ''


def callback_handler(chat_id, callback):
    if callback in callback_texts:
        try:
            set_user_bilet_type(chat_id, callback_texts[callback])
            send_message_to_user(chat_id=chat_id,
                             message="Чудово, твій вибір: проїзний %s\nЗдійсни оплату на картку ПриватБанк та натисни кнопку \"Оплатив(-ла)!\"" %
                                     callback_texts[callback])
            send_message_with_keyboard(chat_id=chat_id,
                                   message="5169360007048329 Ізв Д.О.",
                                   keyboard=payment_keyboard)
        except:
            handle_no_user_in_db(chat_id)
    elif callback == "payment_done":
        try:
            update_user_state(chat_id, 1)
            send_message_to_user(chat_id=chat_id, message="Введіть, будь ласка, час здійснення переказу коштів:")
        except:
            handle_no_user_in_db(chat_id)


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
    requests.post(MESSAGE_URL, json=send_data)


def send_message_to_admin(message):
    send_message_to_user(ADMIN_CHAT_ID, message)


def update_user_state(chat_id, new_state):
    user = User.query.filter_by(chat_id=chat_id).first()
    user.chat_state = new_state
    db.session.commit()


def user_state(chat_id):
    try:
        return User.query.filter_by(chat_id=chat_id).first().chat_state
    except:
        try:
            user = User(chat_id=chat_id, chat_state=2)
            db.session.add(user)
            db.session.commit()
        except:
            pass
    return -1


def get_user_bilet_type(chat_id):
    return User.query.filter_by(chat_id=chat_id).first().bilet_type


def get_user_fullname(chat_id):
    return User.query.filter_by(chat_id=chat_id).first().fullname


def save_purchase_time(chat_id, time):
    user = User.query.filter_by(chat_id=chat_id).first()
    user.purchase_time = time
    db.session.commit()


def set_user_bilet_type(chat_id, bilet_type):
    user = User.query.filter_by(chat_id=chat_id).first()
    user.bilet_type = bilet_type
    db.session.commit()



def handle_no_user_in_db(chat_id):
    try:
        user = User(chat_id=chat_id, chat_state=2)
        db.session.add(user)
        db.session.commit()
        send_message_to_user(chat_id=chat_id,
                             message="Привіт! Тебе вітає бот з закупівлі проїзних:)\nЗараз йде закупівля проїзних на Грудень 2019\nДедлайн 13 листопада о 23:55\nДля початку, напиши своє прізвище та ім'я: ")
    except:
        pass

def set_user_username(chat_id, username):
    user = User.query.filter_by(chat_id=chat_id).first()
    user.username = username
    db.session.commit()


def set_user_fullname(chat_id, fullname):
    user = User.query.filter_by(chat_id=chat_id).first()
    user.fullname = fullname
    db.session.commit()


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)