from create_bot import dp


async def get_promocode(password):
    pg_client = dp["pg_client"]
    result = await pg_client.select_one("promocodes", {"password": str(password)})
    return result


async def update_promocode_quantity(password, new_amount):
    pg_client = dp["pg_client"]
    await pg_client.update(
        "promocodes", {"password": str(password)}, {"remaining_quantity": new_amount}
    )
