import json
import logging

import redis

from allocation import config
from allocation.adapters import orm
from allocation.domain import commands
from allocation.service_layer import messagebus, unit_of_work

# Настройка логгера
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

r = redis.Redis(**config.get_redis_host_and_port())


def main():
    orm.start_mappers()
    pubsub = r.pubsub(ignore_subscribe_messages=True)
    pubsub.subscribe("change_batch_quantity")
    pubsub.subscribe("allocate")

    for m in pubsub.listen():
        channel = m["channel"]
        if channel == b"change_batch_quantity":
            handle_change_batch_quantity(m)
        elif channel == b"allocate":
            handle_allocate(m)


def handle_change_batch_quantity(m):
    logging.debug("handling %s", m)
    data = json.loads(m["data"])
    cmd = commands.ChangeBatchQuantity(ref=data["batchref"], qty=data["qty"])
    messagebus.handle(cmd, uow=unit_of_work.SqlAlchemyUnitOfWork())


def handle_allocate(m):
    logging.debug("handling %s", m)
    data = json.loads(m["data"])
    cmd = commands.Allocate(orderid=data["orderid"], sku=data["sku"], qty=data["qty"])
    messagebus.handle(cmd, uow=unit_of_work.SqlAlchemyUnitOfWork())


if __name__ == "__main__":
    logging.debug("Event consumer started")
    main()
