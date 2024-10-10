from create_bot import dp, bot
from aiogram.methods.send_message import SendMessage
from config import END_DAY_SUGGESTION_PRICE, Configuration
from utils import hash
from model import get_chatgpt_end_day_suggestion
import pytz
import datetime
import json
from yookassa import Payment

TZ = pytz.timezone("Europe/Moscow")


async def pg_log_message(message, model_output, image):
    user_id = message.from_user.id
    message_dttm = message.date.replace(tzinfo=None)
    message_id = message.message_id
    dishes = []
    for dish in model_output["dishes"]:
        dishes.append(
            {
                "user_id": user_id,
                "message_id": message_id,
                "name": dish["dish_name"],
                "quantity": dish["dish_mass_in_gramms"],
                "callories": dish["dish_callories"],
                "proteins": dish["dish_proteins"],
                "carbohydrates": dish["dish_carbohydrates"],
                "fats": dish["dish_fats"],
                "dish_id": hash(dish["dish_name"]),
            }
        )
    for dish in model_output["drinks"]:
        dishes.append(
            {
                "user_id": user_id,
                "message_id": message_id,
                "name": dish["drink_name"],
                "quantity": dish["drink_volume_in_milliliters"],
                "callories": dish["drink_callories"],
                "proteins": dish["drink_proteins"],
                "carbohydrates": dish["drink_carbohydrates"],
                "fats": dish["drink_fats"],
                "dish_id": hash(dish["drink_name"]),
            }
        )
    pg_client = dp["pg_client"]
    await pg_client.insert(
        "messages",
        {
            "message_dttm": message_dttm,
            "user_id": user_id,
            "message_id": message_id,
            "input_text": None,  # message.caption,
            "image": image,
            "resonse_raw": str(model_output),
        },
    )
    await pg_client.insert("dishes", dishes)


def get_pfc_limits_from_callories_limit(energy_limit):
    return {
        "proteins_limit": int(energy_limit * 0.3 / 4),
        "carbohydrates_limit": int(energy_limit * 0.4 / 4),
        "fats_limit": int(energy_limit * 0.3 / 9),
    }


async def register_user(
    message,
    energy_limit=1500,
    role_id=1,
    end_hour=0,
    end_minute=0,
    balance=0,
):
    limits = get_pfc_limits_from_callories_limit(energy_limit)
    pg_client = dp["pg_client"]
    await pg_client.insert(
        "users",
        {
            "user_id": message.from_user.id,
            "username": message.from_user.username,
            "first_name": message.from_user.first_name,
            "last_name": message.from_user.last_name,
            "current_energy": 0,
            "current_proteins": 0,
            "current_carbohydrates": 0,
            "current_fats": 0,
            "proteins_limit": limits["proteins_limit"],
            "carbohydrates_limit": limits["carbohydrates_limit"],
            "fats_limit": limits["fats_limit"],
            "energy_limit": energy_limit,
            "role_id": role_id,
            "end_hour": end_hour,
            "end_minute": end_minute,
            "balance": balance,
        },
        additional_query="ON CONFLICT (user_id) DO NOTHING",
    )


async def get_user(user_id):
    pg_client = dp["pg_client"]
    res = await pg_client.select_one("users", {"user_id": user_id})
    return res


async def update_user(user_id, update_dict):
    pg_client = dp["pg_client"]
    await pg_client.update("users", {"user_id": user_id}, update_dict)


async def add_meal_energy(user_id, energy, proteins, carbohydrates, fats):
    user_data = await get_user(user_id)
    current_energy = user_data["current_energy"] + energy
    current_proteins = user_data["current_proteins"] + proteins
    current_carbohydrates = user_data["current_carbohydrates"] + carbohydrates
    current_fats = user_data["current_fats"] + fats
    await update_user(
        user_id,
        update_dict={
            "current_energy": current_energy,
            "current_proteins": current_proteins,
            "current_carbohydrates": current_carbohydrates,
            "current_fats": current_fats,
        },
    )


async def swap_time(user_id, hour, minute):
    await update_user(user_id, {"end_hour": hour, "end_minute": minute})


async def finish_day_check_all_users():
    dttm = datetime.datetime.now(pytz.timezone("Europe/Moscow")).replace(tzinfo=None)
    pg_client = dp["pg_client"]
    hour = dttm.hour
    minute = dttm.minute
    res = await pg_client.select_many("users", {"end_hour": hour, "end_minute": minute})
    user_results = []
    for user in res:
        user_result = await finish_user_day(user, dttm)
        user_results.append(user_result)
    if len(user_results) > 0:
        await pg_client.insert(
            "daily_energy",
            user_results
        )
        await pg_client.update(
            'users',
            {"end_hour": hour, "end_minute": minute},
            update_dict={
                "current_energy": 0,
                "current_proteins": 0,
                "current_carbohydrates": 0,
                "current_fats": 0,
                "dttm_started_dttm": dttm,
            },
        )


async def finish_user_day(user, dttm):
    started_dttm = user["dttm_started_dttm"]
    results = f'🚀Итоги за день:\n\nКалории — {user["current_energy"]}/{user["energy_limit"]} ккал\nБелки — {user["current_proteins"]}/{user["proteins_limit"]} г\nЖиры — {user["current_fats"]}/{user["fats_limit"]} г\nУглеводы — {user["current_carbohydrates"]}/{user["carbohydrates_limit"]} г'
    await bot(
        SendMessage(chat_id=int(user['user_id']), text=results, disable_notification=True)
    )
    return {
            "user_id": user['user_id'],
            "dttm_started_dttm": started_dttm,
            "dttm_finished_dttm": dttm,
            "current_energy": user["current_energy"],
            "energy_limit": user["energy_limit"],
            "current_proteins": user["current_proteins"],
            "proteins_limit": user["proteins_limit"],
            "current_carbohydrates": user["current_carbohydrates"],
            "carbohydrates_limit": user["carbohydrates_limit"],
            "current_fats": user["current_fats"],
            "fats_limit": user["fats_limit"],
        }
    # dish_history = await pg_client.select_dish_history(started_dttm)
    # text = await get_chatgpt_end_day_suggestion(
    #     dish_history,
    #     int(user_data["energy_limit"]) - int(user_data["current_energy"]),
    #     int(user_data["proteins_limit"]) - int(user_data["current_proteins"]),
    #     int(user_data["carbohydrates_limit"])
    #     - int(user_data["current_carbohydrates"]),
    #     int(user_data["fats_limit"]) - int(user_data["current_fats"]),
    # )
    # await bot(
    #     SendMessage(chat_id=int(user_id), text=text, disable_notification=True)
    # )


async def get_dish_by_id(user_id, message_id, dish_id):
    pg_client = dp["pg_client"]
    dish_params = await pg_client.select_dish(user_id, message_id, dish_id)
    return dish_params


async def remove_dish_from_user_day(user_id, message_id, dish_id):
    user_data = await get_user(user_id)
    pg_client = dp["pg_client"]
    dish_params = await pg_client.select_dish(user_id, message_id, dish_id)
    await update_user(
        user_id,
        update_dict={
            "current_energy": int(user_data["current_energy"])
            - int(dish_params["callories"]),
            "current_proteins": int(user_data["current_proteins"])
            - int(dish_params["proteins"]),
            "current_carbohydrates": int(user_data["current_carbohydrates"])
            - int(dish_params["carbohydrates"]),
            "current_fats": int(user_data["current_fats"]) - int(dish_params["fats"]),
        },
    )
    await pg_client.update_dish(
        user_id, message_id, dish_id, update_dict={"included": False}
    )


async def update_dish_quantity(user_id, message_id, dish_id, new_quantity):
    user_data = await get_user(user_id)
    pg_client = dp["pg_client"]
    dish_params = await pg_client.select_dish(user_id, message_id, dish_id)
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
    await pg_client.update_dish(
        user_id,
        message_id,
        dish_id,
        update_dict={
            "quantity": new_quantity,
            "callories": dish_new_energy,
            "proteins": dish_new_proteins,
            "carbohydrates": dish_new_carbohydrates,
            "fats": dish_new_fats,
        },
    )


async def get_promocode(password):
    pg_client = dp["pg_client"]
    result = await pg_client.select_promocode(password)
    return result


async def update_promocode_quantity(password, new_amount):
    pg_client = dp["pg_client"]
    await pg_client.update(
        "promocodes", {"password": str(password)}, {"remaining_quantity": new_amount}
    )


async def update_user_balance(user_id, new_balance):
    await update_user(user_id, {"balance": new_balance})


# async def check_payment(payment_id):
#     payment = json.loads((Payment.find_one(payment_id)).json())
#     while payment["status"] == "pending":
#         payment = json.loads((Payment.find_one(payment_id)).json())
#         await asyncio.sleep(3)

#     if payment["status"] == "succeeded":
#         print("SUCCSESS RETURN")
#         print(payment)
#         return True
#     else:
#         print("BAD RETURN")
#         print(payment)
#         return False


# async def check_all_pending_invoices():
#     pg_client = dp["pg_client"]
#     rows = await pg_client.select_many("payments", {"status": "pending"})
#     async for row in rows:
#         payment = json.loads((Payment.find_one(row["payment_id"])).json())


# async def add_payment(payment_id, user_id, amount, balance_boost):
#     pg_client = dp["pg_client"]
#     await pg_client.insert(
#         "payments",
#         {
#             "payment_id": payment_id,
#             "user_id": user_id,
#             "amount": amount,
#             "balance_boost": balance_boost,
#             "status": "pending",
#         },
#     )


# async def update_status_payment(payment_id, new_status):
#     pg_client = dp["pg_client"]
#     now = datetime.datetime.now(pytz.timezone("Europe/Moscow")).replace(tzinfo=None)
#     await pg_client.update(
#         "payments",
#         {"payment_id": payment_id},
#         {"status": new_status, "dttm_updated": now},
#     )
