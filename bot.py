# bot.py
import requests
import os
from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy


BOT_URL = f'https://api.telegram.org/bot{os.environ["BOT_KEY"]}/'

# business logic const
ADMIN_CHAT_ID = os.environ["ADMIN_CHAT_ID"]
MESSAGE_URL = BOT_URL + 'sendMessage'
greetings_keyboard = [
    [{
        "text": "temp1 - 100 грн",
        "callback_data": "button1"
    }],
    [{
        "text": "temp2 - 200 грн",
        "callback_data": "button2"
    }],
    [{
        "text": "temp3 - 300 грн",
        "callback_data": "button3"
    }],
    [{
        "text": "temp4 - 400 грн",
        "callback_data": "button4"
    }],
    [{
        "text": "temp5 - 500 грн",
        "callback_data": "button5"
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
        firstname = input_data['message']['from']['first_name']

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
            send_message_to_admin(message)
            send_message_to_user(chat_id, message)
    return ''


def callback_handler(chat_id,callback):
    pass


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


def update_user_state(chart_id, new_state):
    user = User.query.filter_by(chart_id=chart_id).first()
    user.chat_state = new_state
    db.session.commit()


def set_user_bilet_type(chart_id, bilet_type):
    user = User.query.filter_by(chart_id=chart_id).first()
    user.bilet_type = bilet_type
    db.session.commit()


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
