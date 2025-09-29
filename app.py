# --- CORREÇÃO PARA O RECURSIONERROR EM PRODUÇÃO ---
# O monkey-patch do gevent deve ser a primeira coisa a ser executada
# para garantir que todas as bibliotecas padrão (como ssl) sejam não-bloqueantes.
from gevent import monkey
monkey.patch_all()
# --- FIM DA CORREÇÃO ---

import os
import json
import sys
import subprocess
from flask import Flask, render_template, request, jsonify, Response, send_from_directory
from datetime import datetime
from zoneinfo import ZoneInfo
from sqlalchemy import create_engine, text
import time
from threading import Thread
from dotenv import load_dotenv
import requests

# Carrega as variáveis do arquivo .env para o ambiente
load_dotenv()

app = Flask(__name__)

# --- CONFIGURAÇÃO DAS VARIÁVEIS DE AMBIENTE ---
DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///local_dev.db')
VAPID_PRIVATE_KEY = os.environ.get('VAPID_PRIVATE_KEY')
VAPID_PUBLIC_KEY = os.environ.get('VAPID_PUBLIC_KEY')
VAPID_CLAIMS_EMAIL = "3.seixa_analogicos@icloud.com"
NASA_API_KEY = os.environ.get('NASA_API_KEY', 'DEMO_KEY')

if not all([VAPID_PRIVATE_KEY, VAPID_PUBLIC_KEY]):
    raise RuntimeError("As variáveis VAPID_PUBLIC_KEY e VAPID_PRIVATE_KEY não foram encontradas. Verifique seu arquivo .env.")

engine = create_engine(DATABASE_URL)
subscriptions_sse = []

# --- FEATURE: EXTERNALIZAR STRINGS ---
# Carrega as strings de um arquivo JSON
with open('strings.json', 'r', encoding='utf-8') as f:
    strings = json.load(f)
# --- FIM DA FEATURE ---

# --- INICIALIZAÇÃO DO BANCO DE DADOS ---
def initialize_database():
    is_sqlite = DATABASE_URL.startswith('sqlite')
    log_table = """
    CREATE TABLE IF NOT EXISTS log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp VARCHAR(50), pessoa VARCHAR(50), carro VARCHAR(50), acao VARCHAR(20)
    );"""
    subscriptions_table = """
    CREATE TABLE IF NOT EXISTS subscriptions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        subscription_json TEXT NOT NULL UNIQUE
    );"""
    
    if not is_sqlite:
        log_table = log_table.replace("INTEGER PRIMARY KEY AUTOINCREMENT", "SERIAL PRIMARY KEY")
        subscriptions_table = subscriptions_table.replace("INTEGER PRIMARY KEY AUTOINCREMENT", "SERIAL PRIMARY KEY")

    with engine.connect() as conn:
        conn.execute(text("CREATE TABLE IF NOT EXISTS status (id INT PRIMARY KEY, status VARCHAR(20), carro VARCHAR(50), pessoa VARCHAR(50), timestamp VARCHAR(50));"))
        conn.execute(text(log_table))
        conn.execute(text(subscriptions_table))
        if conn.execute(text("SELECT COUNT(*) FROM status WHERE id = 1;")).scalar() == 0:
            conn.execute(text("INSERT INTO status (id, status, carro, pessoa, timestamp) VALUES (1, 'LIVRE', 'Nenhum', 'Ninguém', '');"))
        conn.commit()

# --- LÓGICA DE NOTIFICAÇÃO ---
def send_notification_to_all(payload_title, payload_body):
    with app.app_context():
        with engine.connect() as conn:
            subscriptions = conn.execute(text("SELECT subscription_json FROM subscriptions;")).fetchall()
        
        payload = json.dumps({"title": payload_title, "body": payload_body})
        
        for sub_row in subscriptions:
            subscription_json = sub_row[0]
            command = [
                sys.executable,
                "send_push.py",
                subscription_json,
                payload,
                VAPID_PRIVATE_KEY,
                VAPID_CLAIMS_EMAIL
            ]
            subprocess.Popen(command)

# --- ROTAS DA APLICAÇÃO ---
@app.route('/')
def index():
    return render_template('index.html')

# --- FEATURE: EXTERNALIZAR STRINGS ---
# Rota para servir o arquivo de strings
@app.route('/api/strings')
def get_strings():
    return jsonify(strings)
# --- FIM DA FEATURE ---

@app.route('/service-worker.js')
def service_worker():
    return send_from_directory('static', 'service-worker.js', mimetype='application/javascript')

@app.route('/api/status')
def get_status():
    with engine.connect() as conn:
        result = conn.execute(text("SELECT status, carro, pessoa, timestamp FROM status WHERE id = 1;")).first()
        return jsonify(dict(result._mapping) if result else {"status": "LIVRE", "carro": "Nenhum", "pessoa": "Sistema", "timestamp": ""})

@app.route('/api/update', methods=['POST'])
def update_status():
    data = request.json
    pessoa, carro, acao = data.get('pessoa'), data.get('carro'), data.get('acao')
    now_str = datetime.now(ZoneInfo("America/Sao_Paulo")).strftime('%d/%m/%Y %H:%M:%S')
    notification_title, notification_body = "", ""

    with engine.connect() as conn:
        if acao == 'SAIDA':
            conn.execute(text("UPDATE status SET status='LIVRE', carro='Nenhum', pessoa=:p, timestamp=:ts WHERE id=1;"), {"p": pessoa, "ts": now_str})
            # --- FEATURE: EXTERNALIZAR STRINGS ---
            notification_title = strings["notifications"]["vacantTitle"]
            notification_body = strings["notifications"]["vacantBody"].format(person=pessoa)
            # --- FIM DA FEATURE ---
        elif acao == 'ENTRADA':
            conn.execute(text("UPDATE status SET status='OCUPADA', carro=:c, pessoa=:p, timestamp=:ts WHERE id=1;"), {"c": carro, "p": pessoa, "ts": now_str})
            # --- FEATURE: EXTERNALIZAR STRINGS ---
            notification_title = strings["notifications"]["occupiedTitle"]
            # Mantendo a lógica original de como o nome do carro é exibido na notificação
            notification_body = strings["notifications"]["occupiedBody"].format(person=pessoa, car=carro)
            # --- FIM DA FEATURE ---
        conn.execute(text("INSERT INTO log (timestamp, pessoa, carro, acao) VALUES (:ts, :p, :c, :a);"), {"ts": now_str, "p": pessoa, "c": carro, "a": acao})
        conn.commit()

    if notification_title:
        send_notification_to_all(notification_title, notification_body)
    
    with engine.connect() as conn:
        result = conn.execute(text("SELECT status, carro, pessoa, timestamp FROM status WHERE id = 1;")).first()
        status_json = json.dumps(dict(result._mapping))
        for q in subscriptions_sse:
            q.append(status_json)
    
    return jsonify({'message': 'Status atualizado com sucesso!'})

@app.route('/api/apod')
def get_apod():
    try:
        api_url = f'https://api.nasa.gov/planetary/apod?api_key={NASA_API_KEY}'
        response = requests.get(api_url, timeout=10) 
        response.raise_for_status()  
        return jsonify(response.json())
    except requests.exceptions.RequestException as e:
        error_message = f"[APOD ERROR] Falha ao buscar dados da NASA: {e}"
        print(error_message, file=sys.stderr)
        # --- FEATURE: EXTERNALIZAR STRINGS ---
        return jsonify({"error": strings["warnings"]["couldNotGetImage"]}), 500
        # --- FIM DA FEATURE ---

@app.route('/api/vapid_public_key')
def get_vapid_public_key():
    return jsonify({'public_key': VAPID_PUBLIC_KEY})

@app.route('/api/subscribe', methods=['POST'])
def subscribe():
    with engine.connect() as conn:
        conn.execute(text("INSERT INTO subscriptions (subscription_json) VALUES (:sub) ON CONFLICT (subscription_json) DO NOTHING;"), {"sub": json.dumps(request.json)})
        conn.commit()
    return jsonify({'message': 'Inscrição recebida.'})

@app.route('/api/unsubscribe', methods=['POST'])
def unsubscribe():
    subscription_data = request.json
    with engine.connect() as conn:
        conn.execute(text("DELETE FROM subscriptions WHERE subscription_json = :sub;"), {"sub": json.dumps(subscription_data)})
        conn.commit()
    return jsonify({'message': 'Inscrição removida com sucesso.'})

@app.route('/api/stream')
def stream():
    def event_stream():
        q = []
        subscriptions_sse.append(q)
        try:
            while True:
                yield f"data: {q.pop(0)}\n\n" if q else ": keep-alive\n\n"
                time.sleep(15)
        finally:
            if q in subscriptions_sse:
                subscriptions_sse.remove(q)
    return Response(event_stream(), mimetype='text/event-stream')

with app.app_context():
    initialize_database()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)