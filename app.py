import os
import json
from flask import Flask, render_template, request, jsonify, Response, send_from_directory
from datetime import datetime
from zoneinfo import ZoneInfo
from sqlalchemy import create_engine, text
from pywebpush import webpush, WebPushException
import time

app = Flask(__name__)

# --- CONFIGURAÇÃO DAS VARIÁVEIS DE AMBIENTE ---
DATABASE_URL = os.environ.get('DATABASE_URL')
VAPID_PRIVATE_KEY = os.environ.get('VAPID_PRIVATE_KEY')
VAPID_PUBLIC_KEY = os.environ.get('VAPID_PUBLIC_KEY')

if not all([DATABASE_URL, VAPID_PRIVATE_KEY, VAPID_PUBLIC_KEY]):
    raise RuntimeError("As variáveis de ambiente DATABASE_URL, VAPID_PRIVATE_KEY e VAPID_PUBLIC_KEY devem estar configuradas.")

engine = create_engine(DATABASE_URL)

# Lista para manter as conexões SSE ativas
subscriptions_sse = []

# --- INICIALIZAÇÃO DO BANCO DE DADOS ---
def initialize_database():
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS status (id INT PRIMARY KEY, status VARCHAR(20), carro VARCHAR(50), pessoa VARCHAR(50), timestamp VARCHAR(50));
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS log (id SERIAL PRIMARY KEY, timestamp VARCHAR(50), pessoa VARCHAR(50), carro VARCHAR(50), acao VARCHAR(20));
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS subscriptions (id SERIAL PRIMARY KEY, subscription_json TEXT NOT NULL UNIQUE);
        """))
        result = conn.execute(text("SELECT COUNT(*) FROM status WHERE id = 1;")).scalar()
        if result == 0:
            conn.execute(text("INSERT INTO status (id, status, carro, pessoa, timestamp) VALUES (1, 'LIVRE', 'Nenhum', 'Ninguém', '');"))
        conn.commit()

# --- FUNÇÃO HELPER PARA ENVIAR NOTIFICAÇÕES (COM LOG DETALHADO) ---
def send_notification_to_all(payload_title, payload_body):
    print("--- [NOTIFICAÇÃO] Iniciando processo de envio ---")
    with engine.connect() as conn:
        subscriptions = conn.execute(text("SELECT subscription_json FROM subscriptions;")).fetchall()

    print(f"--- [NOTIFICAÇÃO] Encontradas {len(subscriptions)} inscrições no banco de dados.")

    if not subscriptions:
        print("--- [NOTIFICAÇÃO] Nenhuma inscrição encontrada. Abortando envio.")
        return

    for sub_row in subscriptions:
        try:
            subscription_data = json.loads(sub_row.subscription_json)
            print(f"--- [NOTIFICAÇÃO] Tentando enviar para a inscrição com endpoint: {subscription_data.get('endpoint', 'N/A')}")
            
            webpush(
                subscription_info=subscription_data,
                data=json.dumps({"title": payload_title, "body": payload_body}),
                vapid_private_key=VAPID_PRIVATE_KEY,
                vapid_claims={"sub": "mailto:3.seixa_analogicos@icloud.com"} # MANTENHA SEU E-MAIL AQUI
            )

            print("--- [NOTIFICAÇÃO] Envio realizado com sucesso para um dispositivo.")

        except WebPushException as ex:
            print(f"--- [NOTIFICAÇÃO] ERRO WebPushException: {ex}")
            if ex.response:
                print(f"--- [NOTIFICAÇÃO] Resposta do servidor de push: {ex.response.status_code}, {ex.response.text}")

            if ex.response and ex.response.status_code in [404, 410]:
                print(f"--- [NOTIFICAÇÃO] Removendo inscrição expirada do banco de dados.")
                with engine.connect() as conn:
                    conn.execute(text("DELETE FROM subscriptions WHERE subscription_json = :sub_json;"), {"sub_json": sub_row.subscription_json})
                    conn.commit()
        except Exception as e:
            print(f"--- [NOTIFICAÇÃO] ERRO INESPERADO: {e}")
    
    print("--- [NOTIFICAÇÃO] Processo de envio finalizado ---")

# --- ROTAS DA APLICAÇÃO ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/service-worker.js')
def service_worker():
    return send_from_directory('static', 'service-worker.js', mimetype='application/javascript')

@app.route('/api/status')
def get_status():
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT status, carro, pessoa, timestamp FROM status WHERE id = 1;")).first()
            if result:
                status_data = {"status": result.status, "carro": result.carro, "pessoa": result.pessoa, "timestamp": result.timestamp}
            else:
                status_data = {"status": "LIVRE", "carro": "Nenhum", "pessoa": "Sistema", "timestamp": "Iniciado agora"}
        return jsonify(status_data)
    except Exception as e:
        return jsonify({"error": "Não foi possível buscar o status no banco de dados."}), 500

@app.route('/api/update', methods=['POST'])
def update_status():
    data = request.json
    pessoa = data.get('pessoa')
    carro = data.get('carro')
    acao = data.get('acao')
    
    fuso_horario_local = ZoneInfo("America/Sao_Paulo")
    now_str = datetime.now(fuso_horario_local).strftime('%d/%m/%Y %H:%M:%S')

    notification_title, notification_body = "", ""

    with engine.connect() as conn:
        conn.execute(text("INSERT INTO log (timestamp, pessoa, carro, acao) VALUES (:ts, :p, :c, :a);"), {"ts": now_str, "p": pessoa, "c": carro, "a": acao})
        if acao == 'ENTRADA':
            conn.execute(text("UPDATE status SET status='OCUPADA', carro=:c, pessoa=:p, timestamp=:ts WHERE id=1;"), {"c": carro, "p": pessoa, "ts": now_str})
            notification_title, notification_body = "Vaga Ocupada", f"{pessoa} acabou de chegar com o {carro}."
        else:
            conn.execute(text("UPDATE status SET status='LIVRE', carro='Nenhum', pessoa=:p, timestamp=:ts WHERE id=1;"), {"p": pessoa, "ts": now_str})
            notification_title, notification_body = "Vaga Livre!", f"{pessoa} acabou de sair da garagem."
        conn.commit()
    
    with engine.connect() as conn:
        result = conn.execute(text("SELECT status, carro, pessoa, timestamp FROM status WHERE id = 1;")).first()
        if result:
            status_data = {"status": result.status, "carro": result.carro, "pessoa": result.pessoa, "timestamp": result.timestamp}
            status_json = json.dumps(status_data)
            for q in subscriptions_sse:
                q.append(status_json)
    
    if notification_title:
        send_notification_to_all(notification_title, notification_body)
    
    return jsonify({'message': 'Status atualizado com sucesso!'})

@app.route('/api/vapid_public_key')
def get_vapid_public_key():
    return jsonify({'public_key': VAPID_PUBLIC_KEY})

@app.route('/api/subscribe', methods=['POST'])
def subscribe():
    subscription_json = json.dumps(request.json)
    with engine.connect() as conn:
        conn.execute(text("INSERT INTO subscriptions (subscription_json) VALUES (:sub) ON CONFLICT (subscription_json) DO NOTHING;"), {"sub": subscription_json})
        conn.commit()
    return jsonify({'message': 'Inscrição recebida.'})

@app.route('/api/stream')
def stream():
    def event_stream():
        q = []
        subscriptions_sse.append(q)
        try:
            while True:
                if q:
                    yield f"data: {q.pop(0)}\n\n"
                yield ": keep-alive\n\n"
                time.sleep(15)
        finally:
            subscriptions_sse.remove(q)
    return Response(event_stream(), mimetype='text/event-stream')

with app.app_context():
    initialize_database()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))