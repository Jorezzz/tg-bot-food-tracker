from aiohttp import ClientSession
from async_lru import alru_cache
from config import (
    OPENAI_TOKEN,
    logger,
    OPENAI_SYSTEM_PROMPT,
    OPENAI_SYSTEM_SUGGEST_PROMPT,
    OPENAI_SYSTEM_END_DAY_SUGGEST_PROMPT,
    MODEL,
)


def form_output(data):
    output = ""
    energy_total = 0
    proteins_total = 0
    carbohydrates_total = 0
    fats_total = 0
    if len(data["dishes"]) > 0:
        output += f"Блюда:\n"
        for dish in data["dishes"]:
            output += f"{dish['dish_name']}:\n"
            output += f"    Вес: {dish['dish_mass_in_gramms']} грамм - {dish['dish_callories']} ккал\n"
            output += f"    Белки {dish['dish_proteins']}\n"
            output += f"    Углеводы {dish['dish_carbohydrates']}\n"
            output += f"    Жиры {dish['dish_fats']}\n\n"
            energy_total += int(dish["dish_callories"])
            proteins_total += int(dish["dish_proteins"])
            carbohydrates_total += int(dish["dish_carbohydrates"])
            fats_total += int(dish["dish_fats"])
    if len(data["drinks"]) > 0:
        output += f"Напитки:\n"
        for dish in data["drinks"]:
            output += f"{dish['drink_name']}:\n"
            output += f"    Обьём: {dish['drink_volume_in_milliliters']} грамм - {dish['drink_callories']} ккал\n"
            output += f"    Белки {dish['drink_proteins']}\n"
            output += f"    Углеводы {dish['drink_carbohydrates']}\n"
            output += f"    Жиры {dish['drink_fats']}\n\n"
            energy_total += int(dish["drink_callories"])
            proteins_total += int(dish["drink_proteins"])
            carbohydrates_total += int(dish["drink_carbohydrates"])
            fats_total += int(dish["drink_fats"])
    output += f"Всего {energy_total} калорий"
    return {
        "output_text": output,
        "energy_total": energy_total,
        "proteins_total": proteins_total,
        "carbohydrates_total": carbohydrates_total,
        "fats_total": fats_total,
    }


async def make_request(headers, payload):
    async with ClientSession(headers=headers) as session:
        async with session.post(
            "https://api.openai.com/v1/chat/completions", json=payload
        ) as response:
            result = await response.json()
            logger.info(f"{result}")
            return result


@alru_cache(150)
async def get_chatgpt_photo_description(b64_photo, optional_text=None):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_TOKEN}",
    }

    if optional_text:
        context = [
            {
                "type": "text",
                "text": optional_text,
            },
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{b64_photo}"},
            },
        ]
    else:
        context = [
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{b64_photo}"},
            },
        ]

    payload = {
        "model": MODEL,
        "messages": [
            {
                "role": "system",
                "content": [{"type": "text", "text": OPENAI_SYSTEM_PROMPT}],
            },
        ]
        + [{"role": "user", "content": context}],
        "max_tokens": 1000,
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "meal_composition",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "dishes": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "dish_name": {"type": "string"},
                                    "dish_mass_in_gramms": {"type": "number"},
                                    "dish_callories": {"type": "number"},
                                    "dish_proteins": {"type": "number"},
                                    "dish_carbohydrates": {"type": "number"},
                                    "dish_fats": {"type": "number"},
                                },
                                "required": [
                                    "dish_name",
                                    "dish_mass_in_gramms",
                                    "dish_callories",
                                    "dish_proteins",
                                    "dish_carbohydrates",
                                    "dish_fats",
                                ],
                                "additionalProperties": False,
                            },
                        },
                        "drinks": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "drink_name": {"type": "string"},
                                    "drink_volume_in_milliliters": {"type": "number"},
                                    "drink_callories": {"type": "number"},
                                    "drink_proteins": {"type": "number"},
                                    "drink_carbohydrates": {"type": "number"},
                                    "drink_fats": {"type": "number"},
                                },
                                "required": [
                                    "drink_name",
                                    "drink_volume_in_milliliters",
                                    "drink_callories",
                                    "drink_proteins",
                                    "drink_carbohydrates",
                                    "drink_fats",
                                ],
                                "additionalProperties": False,
                            },
                        },
                    },
                    "required": ["dishes", "drinks"],
                    "additionalProperties": False,
                },
            },
        },
    }

    response = await make_request(headers, payload)
    return response["choices"][0]["message"]


@alru_cache(maxsize=150)
async def get_chatgpt_remaining_energy_suggestion(remaining_energy):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_TOKEN}",
    }
    payload = {
        "model": MODEL,
        "messages": [
            {
                "role": "system",
                "content": [
                    {
                        "type": "text",
                        "text": OPENAI_SYSTEM_SUGGEST_PROMPT,
                    }
                ],
            },
        ]
        + [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": (
                            f"Осталось до дневного лимита {remaining_energy}"
                            if remaining_energy > 0
                            else f"Дневной лимит превышен на {abs(remaining_energy)}"
                        ),
                    }
                ],
            }
        ],
        "max_tokens": 500,
    }
    response = await make_request(headers, payload)
    return response["choices"][0]["message"]["content"]


async def get_chatgpt_end_day_suggestion(
    dish_history,
    remaining_energy,
    remaining_proteins,
    remaining_carbohydrates,
    remaining_fats,
):
    dishes = ", ".join([x["name"] for x in dish_history])
    energy = (
        f"До лимита по калориям осталось {remaining_energy}"
        if remaining_energy > 0
        else f"Лимит калллорий превышен на {abs(remaining_energy)}"
    )
    proteins = (
        f"До лимита по белкам осталось {remaining_proteins}"
        if remaining_proteins > 0
        else f"Лимит белков превышен на {abs(remaining_proteins)}"
    )
    carbohydrates = (
        f"До лимита по углеводам осталось {remaining_carbohydrates}"
        if remaining_carbohydrates > 0
        else f"Лимит углеводов превышен на {abs(remaining_carbohydrates)}"
    )
    fats = (
        f"До лимита по жирам осталось {remaining_fats}"
        if remaining_fats > 0
        else f"Лимит по жирам превышен на {abs(remaining_fats)}"
    )

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_TOKEN}",
    }

    payload = {
        "model": MODEL,
        "messages": [
            {
                "role": "system",
                "content": [
                    {
                        "type": "text",
                        "text": OPENAI_SYSTEM_END_DAY_SUGGEST_PROMPT,
                    }
                ],
            },
        ]
        + [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": (
                            f"Блюда за день {dishes}. {energy}. {proteins}. {carbohydrates}. {fats}."
                        ),
                    }
                ],
            }
        ],
        "max_tokens": 1000,
    }
    response = await make_request(headers, payload)
    return response["choices"][0]["message"]["content"]
