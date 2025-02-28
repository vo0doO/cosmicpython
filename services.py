from __future__ import annotations

from datetime import date

import model
from model import Batch, OrderLine
from repository import AbstractRepository


class InvalidSku(Exception):
    pass


def is_valid_sku(sku, batches):
    return sku in {b.sku for b in batches}


def allocate(line: OrderLine, repo: AbstractRepository, session) -> str:
    batches = repo.list()  # type: ignore
    if not is_valid_sku(line.sku, batches):
        raise InvalidSku(f"Invalid sku {line.sku}")
    batchref = model.allocate(line, batches)
    session.commit()
    return batchref


def deallocate(orderid: str, sku: str, repo: AbstractRepository, session) -> None:
    batches = repo.list()  # type: ignore
    model.deallocate(orderid, sku, batches)
    session.commit()


def add_batch(batch: model.Batch, repo: AbstractRepository, session) -> None:
    repo.add(batch)
    session.commit()
    return
