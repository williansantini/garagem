# Configuração do Gunicorn para usar workers assíncronos (gevent)
# Isso é essencial para aplicações com Server-Sent Events (SSE) ou WebSockets

worker_class = 'gevent'
workers = 1 # Render geralmente lida com concorrência externamente
threads = 10 # Número de threads por worker
timeout = 120 # Aumenta o timeout para conexões de longa duração como SSE