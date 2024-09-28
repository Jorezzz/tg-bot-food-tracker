from typing import Dict, Any, List
from create_bot import logger


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
