import logging

from kombu import Exchange, Queue

from celery import Celery, Task
from celery.signals import (
    after_task_publish,
    task_prerun,
    task_postrun,
    task_failure
)

from src.config import BROKER_URL
from src.session import SessionLocal


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

file_handler = logging.FileHandler("celery_tasks.log")
file_handler.setLevel(logging.INFO)
formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


@after_task_publish.connect
def task_sent_handler(sender=None, headers=None, body=None, **kwargs):
    logger.info(f"Task {sender} sent with id {headers['id']}")


@task_prerun.connect
def task_started_handler(task_id=None, task=None, **kwargs):
    logger.info(f"Task {task.name} with id {task_id} started")


@task_postrun.connect
def task_succeeded_handler(task_id=None, task=None, retval=None, **kwargs):
    logger.info(f"Task {task.name} with id {task_id} completed successfully")


@task_failure.connect
def task_failure_handler(task_id=None, exception=None, traceback=None, sender=None, **kwargs):
    logger.error(f"Task {sender.name} with id {task_id} failed due to {exception}")


class DatabaseTask(Task):
    _db = None

    @property
    def db(self):
        if self._db is None:
            self._db = SessionLocal()
        return self._db

    def on_success(self, retval, task_id, args, kwargs):
        self.close_db()

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        self.close_db()

    def close_db(self):
        if self._db:
            self._db.close()
            self._db = None


celery_app = Celery("celery", broker=BROKER_URL, include=['src.celery_tasks'])

celery_app.conf.update(
    task_default_queue='default',
    worker_pool='prefork',
    worker_concurrency=4,
    timezone="Europe/Kiev",
    worker_hijack_root_logger=False,
    worker_log_format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    worker_task_log_format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",

)

celery_app.conf.task_queues = (
    Queue('default', Exchange('default'), routing_key='default'),
    Queue('tts', Exchange('tts'), routing_key='tts'),
    Queue('auth', Exchange('auth'), routing_key='auth'),
    Queue('stripe', Exchange('stripe'), routing_key='stripe'),
    Queue('course', Exchange('course'), routing_key='course'),
)

celery_app.Task = DatabaseTask
