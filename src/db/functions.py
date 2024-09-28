from create_bot import logger, client, client_times, dp
from utils import convert_dict_from_bytes, convert_list_from_bytes, fill_null
import pytz
import datetime
import hashlib

FORMAT_STRING = "%Y-%m-%d %H:%M:%S"
TZ = pytz.timezone("Europe/Moscow")


async def pg_log_message(message, model_output, image):
    user_id = message.from_user.id
    message_dttm = message.date.replace(tzinfo=None)
    message_id = message.message_id
    dishes = []
    for _, dish in enumerate(model_output["dishes"]):
        for ingridient in dish["composition"]:
            dishes.append(
                {
                    "user_id": user_id,
                    "message_id": message_id,
                    "dish_name": dish["dish_name"],
                    "ingridient_name": ingridient["ingridient_name"],
                    "ingridient_mass": ingridient["ingridient_mass_in_grams"],
                    "ingridient_energy": ingridient["ingridient_callories"],
                }
            )
    pg_client = dp["pg_client"]
    await pg_client.insert(
        "messages",
        {
            "message_dttm": message_dttm,
            "user_id": user_id,
            "message_id": message_id,
            "image": image,
        },
    )
    await pg_client.insert("dishes", dishes)


async def register_user(message):
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name
    now = datetime.datetime.now(TZ).strftime(FORMAT_STRING)
    await client.hset(
        str(user_id),
        mapping={
            "registered_dttm": now,
            "username": username,
            "first_name": fill_null(first_name, ""),
            "last_name": fill_null(last_name, ""),
            "current_energy": 0,
            "energy_limit": 1500,
            "role": "user",
            "dttm_started_dttm": now,
            "end_hour": 0,
            "end_minute": 0,
        },
    )
    await client_times.sadd("0.0", str(user_id))


async def get_user(user_id):
    res = await client.hgetall(str(user_id))
    return convert_dict_from_bytes(res)


async def update_user(user_id, update_dict):
    await client.hset(str(user_id), mapping=update_dict)


async def add_daily_energy(user_id, energy_to_add):
    user_data = await get_user(user_id)
    current_energy = int(user_data["current_energy"]) + energy_to_add
    await update_user(user_id, update_dict={"current_energy": current_energy})


async def swap_time(user_id, hour, minute):
    user_data = await get_user(user_id)
    new_string = hour + "." + minute
    old_string = str(user_data["end_hour"]) + "." + str(user_data["end_minute"])
    logger.info(f"{old_string=} {new_string=}")
    await update_user(user_id, {"end_hour": hour, "end_minute": minute})
    await client_times.sadd(new_string, str(user_id))
    await client_times.srem(old_string, str(user_id))


async def finish_day_check_all_users():
    dttm = datetime.datetime.now(pytz.timezone("Europe/Moscow")).replace(tzinfo=None)
    logger.info(f"{dttm=}")
    res = await client_times.smembers(str(dttm.hour) + "." + str(dttm.minute))
    res = convert_list_from_bytes(res)
    logger.info(f"{res=}")
    for user in res:
        await finish_user_day(user, dttm)


async def finish_user_day(user_id, dttm):
    user_data = await get_user(user_id)
    pg_client = dp["pg_client"]
    await pg_client.insert(
        "daily_energy",
        {
            "day_id": hashlib.sha256(
                (str(user_id) + str(user_data["dttm_started_dttm"])).encode()
            ).hexdigest(),
            "user_id": int(user_id),
            "dttm_started_dttm": datetime.datetime.strptime(
                user_data["dttm_started_dttm"], FORMAT_STRING
            ).replace(tzinfo=None),
            "dttm_finished_dttm": dttm,
            "current_energy": int(user_data["current_energy"]),
            "energy_limit": int(user_data["energy_limit"]),
        },
    )
    await update_user(
        user_id,
        update_dict={
            "current_energy": 0,
            "dttm_started_dttm": dttm.strftime(FORMAT_STRING),
        },
    )
