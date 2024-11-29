# from sqlalchemy import text
# from sqlalchemy.ext.asyncio import create_async_engine
# from hypern import Hypern
# from hypern.routing import Route, HTTPEndpoint
# from hypern.db.sql import SqlConfig
# from hypern.response import JSONResponse


# class DefaultRoute(HTTPEndpoint):
#     async def get(self, get_session):
#         sql = text(
#             """
#             SELECT
#                 CONCAT(customer.last_name, ', ', customer.first_name) AS customer,
#                 address.phone,
#                 film.title
#             FROM
#                 rental
#                 INNER JOIN customer ON rental.customer_id = customer.customer_id
#                 INNER JOIN address ON customer.address_id = address.address_id
#                 INNER JOIN inventory ON rental.inventory_id = inventory.inventory_id
#                 INNER JOIN film ON inventory.film_id = film.film_id
#             WHERE
#                 rental.return_date IS NULL
#                 AND rental_date < CURRENT_DATE
#             ORDER BY
#                 title
#         """
#         )
#         async with get_session() as session:
#             result = await session.execute(sql)
#             data = result.fetchall()
#         res_data = [dict(row._mapping) for row in data]
#         return JSONResponse(res_data)


# routing = [
#     Route("/benchmark", DefaultRoute),
# ]

# app = Hypern(
#     routes=routing,
# )
# engine = create_async_engine("postgresql+psycopg://postgres:123456@localhost:5432/pagila", pool_size=20, max_overflow=10)
# sql = SqlConfig(default_engine=engine)
# sql.init_app(app)

# if __name__ == "__main__":
#     app.start(
#         port=5000,
#         workers=8,
#         processes=8,
#     )

from hypern.db.sql.model import Model
from hypern.db.sql.query import Q
from hypern.db.sql.field import CharField, IntegerField
from hypern.db.sql import SqlConfig
from hypern.hypern import DatabaseConnection, DatabaseConfig, DatabaseType

import asyncio


class ResPartner(Model):
    __tablename__ = "res_partner"

    class Meta:
        table_name = "res_partner"

    id = IntegerField()
    name = CharField()


async def test_query():
    print("1: =========")
    result = ResPartner.objects().select("id", "name").where(Q(id__gt=1)).execute()
    result = ResPartner.objects().select("id", "name").where(Q(id__gt=1)).execute()
    print("2: =========")
    print(result)


if __name__ == "__main__":
    config = DatabaseConfig(
        driver=DatabaseType.Postgres, url="postgres://nghiem:nghiem@localhost:5432/mms_stag", max_connections=10, min_connections=1, idle_timeout=30
    )
    db = DatabaseConnection(config)
    SqlConfig(driver=DatabaseType.Postgres, url="postgres://nghiem:nghiem@localhost:5432/mms_stag", max_connections=10, min_connections=1, idle_timeout=30)
    asyncio.run(test_query())
