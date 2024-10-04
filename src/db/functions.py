from create_bot import client, client_times, dp, bot
from aiogram.methods.send_message import SendMessage
from config import logger
from utils import convert_dict_from_bytes, convert_list_from_bytes, fill_null
from model import get_chatgpt_end_day_suggestion
import pytz
import datetime

FORMAT_STRING = "%Y-%m-%d %H:%M:%S"
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
    message, current_energy=0, energy_limit=1500, role_id=1, end_hour=0, end_minute=0
):
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name
    now = datetime.datetime.now(TZ).strftime(FORMAT_STRING)
    limits = get_pfc_limits_from_callories_limit(energy_limit)
    await client.hset(
        str(user_id),
        mapping={
            "registered_dttm": now,
            "username": username,
            "first_name": fill_null(first_name, ""),
            "last_name": fill_null(last_name, ""),
            "current_energy": current_energy,
            "current_proteins": current_energy,
            "current_carbohydrates": current_energy,
            "current_fats": current_energy,
            "proteins_limit": limits["proteins_limit"],
            "carbohydrates_limit": limits["carbohydrates_limit"],
            "fats_limit": limits["fats_limit"],
            "energy_limit": energy_limit,
            "role_id": role_id,
            "dttm_started_dttm": now,
            "end_hour": end_hour,
            "end_minute": end_minute,
        },
    )
    await client_times.sadd("0.0", str(user_id))


async def get_user(user_id):
    res = await client.hgetall(str(user_id))
    return convert_dict_from_bytes(res) if res is not None else None


async def update_user(user_id, update_dict):
    await client.hset(str(user_id), mapping=update_dict)


async def add_meal_energy(user_id, energy, proteins, carbohydrates, fats):
    user_data = await get_user(user_id)
    current_energy = int(user_data["current_energy"]) + energy
    current_proteins = int(user_data["current_proteins"]) + proteins
    current_carbohydrates = int(user_data["current_carbohydrates"]) + carbohydrates
    current_fats = int(user_data["current_fats"]) + fats
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
    user_data = await get_user(user_id)
    new_string = hour + "." + minute
    old_string = str(user_data["end_hour"]) + "." + str(user_data["end_minute"])
    # logger.info(f"{old_string=} {new_string=}")
    await update_user(user_id, {"end_hour": hour, "end_minute": minute})
    await client_times.sadd(new_string, str(user_id))
    await client_times.srem(old_string, str(user_id))


async def finish_day_check_all_users():
    dttm = datetime.datetime.now(pytz.timezone("Europe/Moscow")).replace(tzinfo=None)
    # logger.info(f"{dttm=}")
    res = await client_times.smembers(str(dttm.hour) + "." + str(dttm.minute))
    res = convert_list_from_bytes(res)
    # logger.info(f"{res=}")
    for user in res:
        await finish_user_day(user, dttm)


async def finish_user_day(user_id, dttm):
    user_data = await get_user(user_id)
    started_dttm = datetime.datetime.strptime(
        user_data["dttm_started_dttm"], FORMAT_STRING
    ).replace(tzinfo=None)
    pg_client = dp["pg_client"]
    await pg_client.insert(
        "daily_energy",
        {
            "user_id": int(user_id),
            "dttm_started_dttm": started_dttm,
            "dttm_finished_dttm": dttm,
            "current_energy": int(user_data["current_energy"]),
            "energy_limit": int(user_data["energy_limit"]),
            "current_proteins": int(user_data["current_proteins"]),
            "proteins_limit": int(user_data["proteins_limit"]),
            "current_carbohydrates": int(user_data["current_carbohydrates"]),
            "carbohydrates_limit": int(user_data["carbohydrates_limit"]),
            "current_fats": int(user_data["current_fats"]),
            "fats_limit": int(user_data["fats_limit"]),
        },
    )
    await update_user(
        user_id,
        update_dict={
            "current_energy": 0,
            "current_proteins": 0,
            "current_carbohydrates": 0,
            "current_fats": 0,
            "dttm_started_dttm": dttm.strftime(FORMAT_STRING),
        },
    )
    # if int(user_data["current_energy"]) > int(user_data["energy_limit"]):
    #     text = f'Сегодня вы превысили лимит каллорий на {int(user_data["current_energy"]) - int(user_data["energy_limit"])}, но не стоит расстраиваться. Похудение это сложный процесс, уверен завтра у вас всё получится!'
    # elif int(user_data["current_energy"]) == int(user_data["energy_limit"]):
    #     text = f"Сегодня вы ровно уложились в днейвной лимит каллорий. Так держать!"
    # else:
    #     text = f'Сегодня вы уложились в днейвной лимит каллорий, и даже остался запас в {int(user_data["energy_limit"]) - int(user_data["current_energy"])}. Так держать!'
    dish_history = await pg_client.select_dish_history(started_dttm)
    text = await get_chatgpt_end_day_suggestion(
        dish_history,
        int(user_data["energy_limit"]) - int(user_data["current_energy"]),
        int(user_data["proteins_limit"]) - int(user_data["current_proteins"]),
        int(user_data["carbohydrates_limit"]) - int(user_data["current_carbohydrates"]),
        int(user_data["fats_limit"]) - int(user_data["current_fats"]),
    )
    results = f'Итоги за день:\nКалории {user_data["current_energy"]}/{user_data["energy_limit"]}\nБелки {user_data["current_proteins"]}/{user_data["proteins_limit"]}\nЖиры {user_data["current_fats"]}/{user_data["fats_limit"]}\nУглеводы {user_data["current_carbohydrates"]}/{user_data["carbohydrates_limit"]}'
    await bot(
        SendMessage(chat_id=int(user_id), text=results, disable_notification=True)
    )
    await bot(SendMessage(chat_id=int(user_id), text=text, disable_notification=True))
