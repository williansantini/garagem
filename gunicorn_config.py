# Configuração do Gunicorn para usar workers assíncronos (gevent)
worker_class = 'gevent'
workers = 1 
threads = 10
timeout = 120