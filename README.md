# Sistema de Controle de Vaga de Garagem

Um sistema web PWA (Progressive Web App) para monitorar e registrar o status de uma vaga de garagem compartilhada. A aplicação permite que os usuários atualizem o status da vaga (livre/ocupada) e recebam notificações push em tempo real.

## Tecnologias Utilizadas
- **Backend:** Python 3 com Flask e SQLAlchemy
- **Frontend:** HTML5, CSS3, JavaScript
- **Servidor WSGI:** Gunicorn com workers `gevent` para suportar Server-Sent Events (SSE).
- **Banco de Dados:** PostgreSQL (recomendado para deploy)
- **Notificações:** Web Push Protocol (VAPID)

## Estrutura do Projeto
/
├── app.py             # Servidor web, lógica da API e notificações
├── gunicorn_config.py # Configuração do Gunicorn para deploy
├── requirements.txt   # Dependências do Python
├── .gitignore         # Arquivos a serem ignorados pelo Git
└── /templates
    └── index.html     # Interface do usuário (frontend)
└── /static
    ├── style.css
    ├── service-worker.js # Lógica do PWA e notificações
    ├── manifest.json
    └── *.png          # Ícones da aplicação

## Configuração e Execução

### 1. Pré-requisitos
- Python 3.8+
- Git

### 2. Clone o Repositório
```bash
git clone <URL_DO_SEU_REPOSITORIO>
cd <NOME_DA_PASTA>