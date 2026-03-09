from celery import Celery
import os

# Configuração do Broker (Redis) - O endereço 'redis' refere-se ao nome do serviço no Docker
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

# Inicialização da instância do Celery
celery_app = Celery(
    "worker",
    broker=REDIS_URL,
    backend=REDIS_URL
)

# Configurações adicionais para otimização
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="America/Sao_Paulo",
    enable_utc=True,
    # Garante que o worker procura tarefas no ficheiro correto
    imports=["app.tasks.worker"]
)

from celery.schedules import crontab

celery_app.conf.beat_schedule = {
    "sincronizacao-noturna-drive-3am": {
        "task": "sincronizacao_noturna_drive",
        "schedule": crontab(hour=3, minute=0),
    },
}