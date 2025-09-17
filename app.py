# app.py modificado

import os
import json
from flask import Flask, render_template, request, jsonify
from datetime import datetime
from zoneinfo import ZoneInfo
from sqlalchemy import create_engine, text
from pywebpush import webpush, WebPushException

app = Flask(__name__)

# --- CONFIGURAÇÃO ---
DATABASE_URL = os.environ.get('DATABASE_URL')
VAPID_PRIVATE_KEY = os.environ.get('VAPID_PRIVATE_KEY')
VAPID_PUBLIC_KEY = os.environ.get('VAPID_PUBLIC_KEY') # Apenas para o endpoint

if not all([DATABASE_URL, VAPID_PRIVATE_KEY, VAPID_PUBLIC_KEY]):
    raise RuntimeError("Variáveis de ambiente do banco de dados e/ou VAPID não configuradas.")

engine = create_engine(DATABASE_URL)

# --- INICIALIZAÇÃO DO BANCO DE DADOS ---
# app.py - Substitua esta função inteira

# --- INICIALIZAÇÃO DO BANCO DE DADOS ---
def initialize_database():
    with engine.connect() as conn:
        # Tabela para o status atual (apenas 1 linha)
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS status (
                id INT PRIMARY KEY,
                status VARCHAR(20),
                carro VARCHAR(50),
                pessoa VARCHAR(50),
                timestamp VARCHAR(50)
            );
        """))
        # Tabela para o log
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS log (
                id SERIAL PRIMARY KEY,
                timestamp VARCHAR(50),
                pessoa VARCHAR(50),
                carro VARCHAR(50),
                acao VARCHAR(20)
            );
        """))
        
        # NOVA Tabela para armazenar as inscrições de notificação
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS subscriptions (
                id SERIAL PRIMARY KEY,
                subscription_json TEXT NOT NULL UNIQUE
            );
        """))

        # Insere a linha inicial de status se não existir
        result = conn.execute(text("SELECT COUNT(*) FROM status WHERE id = 1;")).scalar()
        if result == 0:
            conn.execute(text("INSERT INTO status (id, status, carro, pessoa, timestamp) VALUES (1, 'LIVRE', 'Nenhum', 'Ninguém', '');"))
        conn.commit()

# --- FUNÇÃO HELPER PARA ENVIAR NOTIFICAÇÕES ---
def send_notification_to_all(payload_title, payload_body):
    with engine.connect() as conn:
        result = conn.execute(text("SELECT subscription_json FROM subscriptions;"))
        subscriptions = result.fetchall()

    for sub_row in subscriptions:
        try:
            subscription_data = json.loads(sub_row.subscription_json)
            webpush(
                subscription_info=subscription_data,
                data=json.dumps({"title": payload_title, "body": payload_body}),
                vapid_private_key=VAPID_PRIVATE_KEY,
                vapid_claims={"sub": "mailto:your-email@example.com"} # Mude para seu e-mail
            )
        except WebPushException as ex:
            print(f"Erro ao enviar notificação: {ex}")
            # Se a inscrição for inválida (ex: 410 Gone), remova-a do banco de dados
            if ex.response and ex.response.status_code in [404, 410]:
                with engine.connect() as conn:
                    conn.execute(text("DELETE FROM subscriptions WHERE subscription_json = :sub_json;"), {"sub_json": sub_row.subscription_json})
                    conn.commit()


# --- ROTAS DA APLICAÇÃO ---
@app.route('/')
def index():
    return render_template('index.html')

# Rota existente, sem mudanças
@app.route('/api/status')
def get_status():
    # ... seu código existente aqui ...
    return jsonify(status_data)

# --- NOVAS ROTAS PARA PUSH NOTIFICATIONS ---
@app.route('/api/vapid_public_key')
def get_vapid_public_key():
    return jsonify({'public_key': VAPID_PUBLIC_KEY})

@app.route('/api/subscribe', methods=['POST'])
def subscribe():
    subscription_data = request.json
    subscription_json = json.dumps(subscription_data)
    with engine.connect() as conn:
        # Evita duplicados
        conn.execute(text("INSERT INTO subscriptions (subscription_json) VALUES (:sub) ON CONFLICT (subscription_json) DO NOTHING;"), {"sub": subscription_json})
        conn.commit()
    return jsonify({'message': 'Inscrição recebida.'})

# --- ROTA DE UPDATE MODIFICADA ---
@app.route('/api/update', methods=['POST'])
def update_status():
    # ... seu código existente para pegar os dados e formatar a data ...
    data = request.json
    pessoa = data.get('pessoa')
    carro = data.get('carro')
    acao = data.get('acao')
    
    fuso_horario_local = ZoneInfo("America/Sao_Paulo")
    agora_local = datetime.now(fuso_horario_local)
    now_str = agora_local.strftime('%d/%m/%Y %H:%M:%S')

    with engine.connect() as conn:
        # ... seu código existente para inserir no log ...
        
        # Atualiza o status e prepara a notificação
        notification_title = ""
        notification_body = ""
        if acao == 'ENTRADA':
            conn.execute(text(
                "UPDATE status SET status='OCUPADA', carro=:c, pessoa=:p, timestamp=:ts WHERE id=1;"),
                {"c": carro, "p": pessoa, "ts": now_str}
            )
            notification_title = "Vaga Ocupada"
            notification_body = f"{pessoa} acabou de chegar com o {carro}."
        else: # SAIDA
            conn.execute(text(
                "UPDATE status SET status='LIVRE', carro='Nenhum', pessoa=:p, timestamp=:ts WHERE id=1;"),
                {"p": pessoa, "ts": now_str}
            )
            notification_title = "Vaga Livre!"
            notification_body = f"{pessoa} acabou de sair da garagem."
        conn.commit()
    
    # Envia a notificação para todos os inscritos
    if notification_title:
        send_notification_to_all(notification_title, notification_body)
    
    return jsonify({'message': 'Status atualizado com sucesso!'})


# --- INICIALIZAÇÃO ---
with app.app_context():
    initialize_database()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)