# Sistema de Controle de Vaga de Garagem

Um sistema web simples para monitorar e registrar o status de uma vaga de garagem compartilhada. A aplicação permite que os usuários atualizem o status da vaga (livre/ocupada) através de uma interface web acessível por celular.

## Tecnologias Utilizadas
- **Backend:** Python 3 com Flask
- **Frontend:** HTML5, CSS3, JavaScript
- **Armazenamento de Dados:** Arquivos JSON para o status atual e CSV para o log de histórico.

## Estrutura do Projeto
/
├── app.py             # Servidor web e lógica da API
├── requirements.txt   # Dependências do Python
├── status.json        # Arquivo com o status atual da garagem
├── log.csv            # Histórico de entradas e saídas
└── /templates
└── index.html     # Página da interface do usuário

## Como Executar
1.  **Clone o repositório:**
    ```bash
    git clone <URL_DO_SEU_REPOSITORIO>
    cd <NOME_DA_PASTA>
    ```

2.  **Crie e ative um ambiente virtual (recomendado):**
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    ```

3.  **Instale as dependências:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Execute a aplicação:**
    ```bash
    python3 app.py
    ```
5.  Acesse a interface no seu navegador através do endereço `http://<IP_DO_SERVIDOR>:5000`.

## Como Usar
A interface web exibe o status atual da garagem. Os botões permitem que cada usuário registre a entrada com um carro específico ou a liberação da vaga. Todas as ações são registradas com data e hora no arquivo `log.csv`.

## Endpoints da API
- `GET /api/status`: Retorna um JSON com o estado atual da garagem.
- `POST /api/update`: Recebe um JSON para atualizar o status. Exemplo de corpo: `{"pessoa": "Nome", "carro": "Carro", "acao": "ENTRADA"}`.
