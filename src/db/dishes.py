from create_bot import dp
from db.users import get_user, update_user


async def get_dish_by_id(user_id, message_id, dish_id):
    pg_client = dp["pg_client"]
    dish = await pg_client.select_one(
        "dishes", {"user_id": user_id, "message_id": message_id, "dish_id": dish_id}
    )
    return dish


async def remove_dish_from_user_day(user_id, message_id, dish_id):
    user_data = await get_user(user_id)
    pg_client = dp["pg_client"]
    dish = await get_dish_by_id(user_id, message_id, dish_id)
    await update_user(
        user_id,
        update_dict={
            "current_energy": int(user_data["current_energy"]) - int(dish["callories"]),
            "current_proteins": int(user_data["current_proteins"])
            - int(dish["proteins"]),
            "current_carbohydrates": int(user_data["current_carbohydrates"])
            - int(dish["carbohydrates"]),
            "current_fats": int(user_data["current_fats"]) - int(dish["fats"]),
        },
    )
    await pg_client.update(
        "dishes",
        {"user_id": user_id, "message_id": message_id, "dish_id": dish_id},
        {"included": False},
    )


async def update_dish_quantity(user_id, message_id, dish_id, new_quantity):
    user_data = await get_user(user_id)
    pg_client = dp["pg_client"]
    dish_params = await get_dish_by_id(user_id, message_id, dish_id)
    dish_new_energy = int(
        float(new_quantity) / float(dish_params["quantity"]) * dish_params["callories"]
    )
    dish_new_proteins = int(
        float(new_quantity) / float(dish_params["quantity"]) * dish_params["proteins"]
    )
    dish_new_carbohydrates = int(
        float(new_quantity)
        / float(dish_params["quantity"])
        * dish_params["carbohydrates"]
    )
    dish_new_fats = int(
        float(new_quantity) / float(dish_params["quantity"]) * dish_params["fats"]
    )
    await update_user(
        user_id,
        update_dict={
            "current_energy": int(user_data["current_energy"])
            - int(dish_params["callories"])
            + int(dish_new_energy),
            "current_proteins": int(user_data["current_proteins"])
            - int(dish_params["proteins"])
            + int(dish_new_proteins),
            "current_carbohydrates": int(user_data["current_carbohydrates"])
            - int(dish_params["carbohydrates"])
            + int(dish_new_carbohydrates),
            "current_fats": int(user_data["current_fats"])
            - int(dish_params["fats"])
            + int(dish_new_fats),
        },
    )
    await pg_client.update(
        "dishes",
        {"user_id": user_id, "message_id": message_id, "dish_id": dish_id},
        update_dict={
            "quantity": new_quantity,
            "callories": dish_new_energy,
            "proteins": dish_new_proteins,
            "carbohydrates": dish_new_carbohydrates,
            "fats": dish_new_fats,
        },
    )
