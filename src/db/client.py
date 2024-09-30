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

    async def execute(self, query, *args, **kwargs):
        async with self.pool.acquire() as con:
            await con.execute(query, *args, **kwargs)

    async def insert(self, table, data: List[Dict[str, Any]] | Dict[str, Any]) -> None:
        if not isinstance(data, list):
            data = [data]
        columns, idxs = self._prepare_insertion(data[0])
        values = [tuple(x.values()) for x in data]
        query = f"""
            INSERT INTO {table}({columns}) VALUES({idxs})
        """
        async with self.pool.acquire() as con:
            await con.executemany(query, values)

    async def select_dish_history(self, dttm):
        async with self.pool.acquire() as con:
            rows = await con.fetch(
                """
                SELECT * 
                FROM 
                    dishes as t1
                    INNER JOIN messages as t2 ON t1.user_id = t2.user_id AND t1.message_id = t2.message_id
                WHERE 
                    t2.message_dttm >= $1
            """,
                dttm,
            )
            return rows
