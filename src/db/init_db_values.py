from create_bot import dp

promocodes = [
    {
        "name": "Test promoaction",
        "password": "tst-gcP83fC2",
        "quantity": 1,
        "remaining_quantity": 1,
        "balance_boost": 10000,
        "aux_property": "unlimited",
    }
]


async def init_promocode_values():
    pg_client = dp["pg_client"]
    await pg_client.insert(
        "promocodes", promocodes, additional_query="ON CONFLICT (name) DO NOTHING"
    )


async def init_all_db_values():
    await init_promocode_values()
