import os
from flask import Flask, render_template, request, jsonify
from datetime import datetime
from sqlalchemy import create_engine, text

app = Flask(__name__)

# Pega a URL do banco de dados do ambiente. O Render vai injetar isso.
DATABASE_URL = os.environ.get('DATABASE_URL')
engine = create_engine(DATABASE_URL)

# Função para garantir que as tabelas existam
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
        # Insere a linha inicial de status se não existir
        result = conn.execute(text("SELECT COUNT(*) FROM status;")).scalar()
        if result == 0:
            conn.execute(text("INSERT INTO status VALUES (1, 'LIVRE', 'Nenhum', 'Ninguém', '');"))
        conn.commit()


@app.route('/api/status')
def get_status():
    with engine.connect() as conn:
        result = conn.execute(text("SELECT status, carro, pessoa, timestamp FROM status WHERE id = 1;")).first()
        status_data = {
            "status": result[0], "carro": result[1], "pessoa": result[2], "timestamp": result[3]
        }
    return jsonify(status_data)

@app.route('/api/update', methods=['POST'])
def update_status():
    data = request.json
    pessoa = data.get('pessoa')
    carro = data.get('carro')
    acao = data.get('acao')
    now_str = datetime.now().strftime('%d/%m/%Y %H:%M:%S')

    with engine.connect() as conn:
        # Insere no log
        conn.execute(text(
            "INSERT INTO log (timestamp, pessoa, carro, acao) VALUES (:ts, :p, :c, :a);"),
            {"ts": now_str, "p": pessoa, "c": carro, "a": acao}
        )
        # Atualiza o status
        if acao == 'ENTRADA':
            conn.execute(text(
                "UPDATE status SET status='OCUPADA', carro=:c, pessoa=:p, timestamp=:ts WHERE id=1;"),
                {"c": carro, "p": pessoa, "ts": now_str}
            )
        else: # SAIDA
            conn.execute(text(
                "UPDATE status SET status='LIVRE', carro='Nenhum', pessoa=:p, timestamp=:ts WHERE id=1;"),
                {"p": pessoa, "ts": now_str}
            )
        conn.commit()

    return jsonify({'message': 'Status atualizado com sucesso!'})

# ... (o resto do seu código, como a rota '/')
@app.route('/')
def index():
    return render_template('index.html')

initialize_database()

# O __main__ não é usado pelo Render, mas é bom para testes locais
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)