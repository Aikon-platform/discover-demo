from . import config
from flask import Flask

import dramatiq
from dramatiq.brokers.redis import RedisBroker
from dramatiq_abort import Abortable, backends
from dramatiq.middleware import CurrentMessage

app = Flask(__name__)
app.config.from_object(config.FLASK_CONFIG)

broker = RedisBroker(url=config.BROKER_URL)
event_backend = backends.RedisBackend(client=broker.client)
abortable = Abortable(backend=event_backend)
broker.add_middleware(abortable)
broker.add_middleware(CurrentMessage())
dramatiq.set_broker(broker)


from .routes import *
from .tasks import *