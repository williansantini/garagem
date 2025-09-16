import os
import csv
import json
from flask import Flask, render_template, request, jsonify
from datetime import datetime

app = Flask(__name__)

# Caminhos para os arquivos de dados
STATUS_FILE = 'status.json'
LOG_FILE = 'log.csv'

# Função para garantir que os arquivos de dados existam
def initialize_data_files():
    # Garante a existência do arquivo de status
    if not os.path.exists(STATUS_FILE):
        with open(STATUS_FILE, 'w') as f:
            json.dump({'status': 'LIVRE', 'carro': 'Nenhum', 'pessoa': 'Ninguém', 'timestamp': ''}, f)
    
    # Garante a existência e o cabeçalho do arquivo de log
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['timestamp', 'pessoa', 'carro', 'acao'])

# Rota principal: exibe a página web
@app.route('/')
def index():
    return render_template('index.html')

# API: retorna o status atual da garagem
@app.route('/api/status')
def get_status():
    with open(STATUS_FILE, 'r') as f:
        status_data = json.load(f)
    return jsonify(status_data)

# API: atualiza o status e escreve no log
@app.route('/api/update', methods=['POST'])
def update_status():
    data = request.json
    pessoa = data.get('pessoa')
    carro = data.get('carro')
    acao = data.get('acao')
    
    # Prepara os dados de status e log
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    new_status = {
        'timestamp': now_str
    }
    
    if acao == 'ENTRADA':
        new_status['status'] = 'OCUPADA'
        new_status['carro'] = carro
        new_status['pessoa'] = pessoa
    else: # SAIDA
        new_status['status'] = 'LIVRE'
        new_status['carro'] = 'Nenhum'
        new_status['pessoa'] = pessoa # Registra quem liberou

    # Atualiza o arquivo de status
    with open(STATUS_FILE, 'w') as f:
        json.dump(new_status, f)
        
    # Adiciona a entrada no log CSV
    with open(LOG_FILE, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([now_str, pessoa, carro, acao])
        
    return jsonify({'message': 'Status atualizado com sucesso!', 'new_status': new_status})

if __name__ == '__main__':
    initialize_data_files()
    # Para acessar de outros dispositivos na mesma rede, use 0.0.0.0
    app.run(host='0.0.0.0', port=5000)