from aiohttp import ClientSession

OPENAI_SYSTEM_PROMPT = "Ты умный подсчитыватель каллорий. Определи, что за блюда и продукты представлены на картинках (скорее всего это блюда популярные в России), выпиши сколько они весят и сколько каллорий в каждом из них и в этом приёме пищи в целом. Если не можешь определить точно выдай наиболее похожий вариант. Ответ выдавай на русском языке."


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


async def get_chatgpt_description(b64_photo, OPENAI_TOKEN, logger):
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

    async with ClientSession(headers=headers) as session:
        async with session.post(
            "https://api.openai.com/v1/chat/completions", json=payload
        ) as response:
            result = await response.json()
            logger.info(f"{result}")
            return result["choices"][0]["message"]
