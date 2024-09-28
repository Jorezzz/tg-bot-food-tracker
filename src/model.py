from aiohttp import ClientSession
from config import (
    OPENAI_TOKEN,
    logger,
    OPENAI_SYSTEM_PROMPT,
    OPENAI_SYSTEM_SUGGEST_PROMPT,
)


def form_output(data):
    output = ""
    message_total = 0
    for _, dish in enumerate(data["dishes"]):
        output += f"{dish['dish_name']}:\n"
        dish_total = 0
        for ingridient in dish["composition"]:
            output += f"  {ingridient['ingridient_name']}: {ingridient['ingridient_mass_in_grams']} грамм - {ingridient['ingridient_callories']} каллорий\n"
            dish_total += int(ingridient["ingridient_callories"])
        output += f"В блюде {dish_total} каллорий\n\n"
        message_total += dish_total
    output += f"Всего {message_total} каллорий"
    return output, message_total


async def make_request(headers, payload):
    async with ClientSession(headers=headers) as session:
        async with session.post(
            "https://api.openai.com/v1/chat/completions", json=payload
        ) as response:
            result = await response.json()
            logger.info(f"{result}")
            return result["choices"][0]["message"]


async def get_chatgpt_photo_description(b64_photo):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_TOKEN}",
    }

    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {
                "role": "system",
                "content": [{"type": "text", "text": OPENAI_SYSTEM_PROMPT}],
            },
        ]
        + [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{b64_photo}"},
                    }
                ],
            }
        ],
        "max_tokens": 500,
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "dish_composition",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "dishes": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "composition": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "ingridient_name": {"type": "string"},
                                                "ingridient_mass_in_grams": {
                                                    "type": "number"
                                                },
                                                "ingridient_callories": {
                                                    "type": "number"
                                                },
                                            },
                                            "required": [
                                                "ingridient_name",
                                                "ingridient_mass_in_grams",
                                                "ingridient_callories",
                                            ],
                                            "additionalProperties": False,
                                        },
                                    },
                                    "dish_name": {"type": "string"},
                                },
                                "required": ["composition", "dish_name"],
                                "additionalProperties": False,
                            },
                        },
                    },
                    "required": ["dishes"],
                    "additionalProperties": False,
                },
            },
        },
    }

    response = await make_request(headers, payload)
    return response


async def get_chatgpt_remaining_energy_suggestion(current_energy, remaining_energy):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_TOKEN}",
    }

    payload = {
        "model": "gpt-4o-mini",
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
                            f"Текущее количество каллорий {current_energy}, осталось до дневного лимита {remaining_energy}"
                            if remaining_energy > 0
                            else f"Текущее количество каллорий {current_energy}, дневной лимит превышен на {remaining_energy}"
                        ),
                    }
                ],
            }
        ],
        "max_tokens": 500,
    }

    response = await make_request(headers, payload)
    return response["content"]
