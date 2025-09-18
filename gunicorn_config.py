# Configuração do Gunicorn para usar workers assíncronos (meinheld)
# Essencial para aplicações com Server-Sent Events (SSE) e alta performance.
worker_class = 'meinheld.gmeinheld.MeinheldWorker'
workers = 1 
threads = 10
timeout = 120