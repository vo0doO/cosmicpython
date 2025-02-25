import abc

import model


class AbstractRepository(abc.ABC):
    @abc.abstractmethod
    def add(self, batch: model.Batch):
        raise NotImplementedError

    @abc.abstractmethod
    def get(self, reference) -> model.Batch:
        raise NotImplementedError


class SqlRepository(AbstractRepository):
    def __init__(self, session):
        self.session = session

    def add(self, batch):
        result = self.session.execute(
            "INSERT INTO batches (reference, sku, _purchased_quantity, eta)"
            "VALUES (:ref, :sku, :qty, :eta)"
            "RETURNING id",
            dict(
                ref=batch.reference,
                sku=batch.sku,
                qty=batch._purchased_quantity,
                eta=batch.eta,
            ),
        )

        batch_id = result.scalar()

        if allocations := batch._allocations:
            for orderline in allocations:
                result = self.session.execute(
                    "INSERT INTO order_lines (sku, qty, orderid)"
                    "VALUES (:sku, :qty, :orderid)"
                    "RETURNING id",
                    dict(
                        sku=orderline.sku, qty=orderline.qty, orderid=orderline.orderid
                    ),
                )

                orderline_id = result.scalar()

                self.session.execute(
                    "INSERT INTO allocations (orderline_id, batch_id)"
                    "VALUES (:orderline_id, :batch_id)",
                    dict(orderline_id=orderline_id, batch_id=batch_id),
                )

    def get(self, reference) -> model.Batch:

        batch = model.Batch(
            *self.session.execute(
                "SELECT * FROM batches WHERE reference=:ref", dict(ref=reference)
            ).first()[1:]
        )
        batch._allocations = self.get_allocations(reference)
        return batch

    def get_allocations(self, batchid):
        query = """
        SELECT 
        order_lines.orderid, 
        order_lines.sku,  
        order_lines.qty 
        FROM allocations
        JOIN order_lines ON allocations.orderline_id = order_lines.id
        JOIN batches ON allocations.batch_id = batches.id
        WHERE batches.reference = :batchid;
        """  # noqa: F841

        rows = list(self.session.execute(query, dict(batchid=batchid)))
        return set(model.OrderLine(*row) for row in rows)
