from typing import Dict, Any
from create_bot import db_manager

class PGClient:
    def __init__(self, pool, logger):
        self.pool = pool
        self.logger = logger
        self.logger.info('PG Client initialized')

    async def insert_one(self, table, data: Dict[str, Any]) -> None:
        columns = ', '.join(list(data.keys()))
        values = list(data.values())
        idxs = ', '.join([f"${i+1}" for i in range(len(data))])
        async with self.pool.acquire() as con:
            query = f'''
                INSERT INTO {table}({columns}) VALUES({idxs})
            '''
            self.logger.info(query)
            await con.execute(query, *values)