from typing import Dict, Any, List
from config import logger


class PGClient:
    def __init__(self, pool):
        self.pool = pool
        logger.info("PG Client initialized")

    def _prepare_insertion(self, data: Dict[str, Any]):
        columns = ", ".join(list(data.keys()))
        idxs = ", ".join([f"${i+1}" for i in range(len(data))])
        return columns, idxs

    def _prepare_where_query(self, data: Dict[str, Any], additive=0):
        query = "WHERE "
        query += " AND ".join(
            [f"{k_v[0]} = ${i+1+additive}" for i, k_v in enumerate(data.items())]
        )
        return query

    def _prepare_update_query(self, data: Dict[str, Any], additive=0):
        query = "SET "
        query += ", ".join(
            [f"{k_v[0]} = ${i+1+additive}" for i, k_v in enumerate(data.items())]
        )
        return query

    async def execute(self, query, *args, **kwargs):
        async with self.pool.acquire() as con:
            await con.execute(query, *args, **kwargs)

    async def insert(
        self, table, data: List[Dict[str, Any]] | Dict[str, Any], additional_query=""
    ) -> None:
        if not isinstance(data, list):
            data = [data]
        columns, idxs = self._prepare_insertion(data[0])
        values = [tuple(x.values()) for x in data]
        query = f"""
            INSERT INTO {table}({columns}) VALUES({idxs}) {additional_query}
        """
        async with self.pool.acquire() as con:
            await con.executemany(query, values)

    async def select_dish(self, user_id, message_id, dish_id):
        async with self.pool.acquire() as con:
            row = await con.fetchrow(
                """
                SELECT * 
                FROM dishes
                WHERE 
                    user_id = $1 AND message_id = $2 AND dish_id = $3
            """,
                int(user_id),
                int(message_id),
                int(dish_id),
            )
            return row

    async def update(self, table_name, where_dict, update_dict):
        update_query = self._prepare_update_query(update_dict)
        additive = len(update_dict)
        where_query = self._prepare_where_query(where_dict, additive)
        values = list(update_dict.values()) + list(where_dict.values())
        await self.execute(
            f"""
                UPDATE {table_name} {update_query}
                {where_query}
            """,
            *values,
        )

    async def update_dish(self, user_id, message_id, dish_id, update_dict):
        where_dict = {
            "user_id": int(user_id),
            "message_id": int(message_id),
            "dish_id": int(dish_id),
        }
        await self.update("dishes", where_dict, update_dict)

    async def select_dish_history(self, dttm):
        async with self.pool.acquire() as con:
            rows = await con.fetch(
                """
                SELECT * 
                FROM 
                    dishes as t1
                    INNER JOIN messages as t2 ON t1.user_id = t2.user_id AND t1.message_id = t2.message_id
                WHERE 
                    t2.message_dttm >= $1 AND t1.included
            """,
                dttm,
            )
            return rows

    async def select_promocode(self, password):
        async with self.pool.acquire() as con:
            row = await con.fetchrow(
                """
                SELECT *
                FROM promocodes
                WHERE password = $1
            """,
                str(password),
            )
            return row
