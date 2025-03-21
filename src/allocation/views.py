from allocation.service_layer import unit_of_work


def allocations(orderid: str, uow: unit_of_work.SqlAlchemyUnitOfWork):
    with uow:
        results = uow.session.execute(
            """
            SELECT sku, batchref FROM allocations_view WHERE orderid = :orderid
            """,
            dict(orderid=orderid),
        )
    return [dict(r) for r in results]


def orders(orderid: str, uow: unit_of_work.SqlAlchemyUnitOfWork):
    with uow:
        result = uow.session.execute(
            """
            SELECT orderid, sku, qty FROM order_lines WHERE orderid = :orderid
            """,
            dict(orderid=orderid),
        ).first()
    return dict(result) if result else result
