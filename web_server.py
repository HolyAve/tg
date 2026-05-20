from flask import Flask
from threading import Thread
import os

app = Flask(__name__)

@app.route('/')
def home():
    return "Бот работает!"

@app.route('/health')
def health():
    return "OK", 200

def run():
    # Запускаем Flask-сервер на порту, который назначил Render
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

def keep_alive():
    # Запускаем сервер в отдельном потоке, чтобы он не блокировал бота
    t = Thread(target=run)
    t.start()