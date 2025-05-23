from typing import Dict, Any, List


class PGClient:
    def __init__(self, pool):
        self.pool = pool

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

    async def select_one(self, table_name, where_dict):
        where_query = self._prepare_where_query(where_dict)
        values = list(where_dict.values())
        async with self.pool.acquire() as con:
            row = await con.fetchrow(
                f"""
                    SELECT *
                    FROM {table_name}
                    {where_query}
                """,
                *values,
            )
            return row

    async def select_many(self, table_name, where_dict):
        where_query = self._prepare_where_query(where_dict)
        values = list(where_dict.values())
        async with self.pool.acquire() as con:
            rows = await con.fetch(
                f"""
                    SELECT *
                    FROM {table_name}
                    {where_query}
                """,
                *values,
            )
            return rows

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
