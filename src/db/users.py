from create_bot import dp, bot
from aiogram.methods.send_message import SendMessage
from config import END_DAY_SUGGESTION_PRICE
from utils import hash, get_pfc_limits_from_callories_limit
from model import get_chatgpt_end_day_suggestion
import pytz
import datetime
from aiogram.exceptions import TelegramForbiddenError

TZ = pytz.timezone("Europe/Moscow")


async def pg_log_message(message, model_output, optional_text=None):
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
            "input_text": optional_text,  # message.caption,
            "image": message.photo[-1].file_id,
            "resonse_raw": str(model_output),
        },
    )
    await pg_client.insert("dishes", dishes)


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
        if user_result is not None:
            user_results.append(user_result)
    if len(user_results) > 0:
        await pg_client.insert("daily_energy", user_results)
        await pg_client.update(
            "users",
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
    try:
        if user["current_energy"] != 0:
            started_dttm = user["dttm_started_dttm"]
            results = f'🚀Итоги за день:\n\nКалории — {user["current_energy"]}/{user["energy_limit"]} ккал\nБелки — {user["current_proteins"]}/{user["proteins_limit"]} г\nЖиры — {user["current_fats"]}/{user["fats_limit"]} г\nУглеводы — {user["current_carbohydrates"]}/{user["carbohydrates_limit"]} г'
            await bot(
                SendMessage(
                    chat_id=int(user["user_id"]),
                    text=results,
                    disable_notification=True,
                )
            )
            return {
                "user_id": user["user_id"],
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
    except TelegramForbiddenError as e:
        return None
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
