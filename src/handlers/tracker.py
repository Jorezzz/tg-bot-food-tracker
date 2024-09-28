from aiogram import Router, F
from aiogram.types import Message
from create_bot import bot
from config import logger, OPENAI_TOKEN
from auth.utils import permission_allowed
import io
from utils import encode_image
from model import (
    get_chatgpt_photo_description,
    get_chatgpt_remaining_energy_suggestion,
    form_output,
)
from db.functions import add_daily_energy, get_user, update_user, pg_log_message
from aiogram.utils.chat_action import ChatActionSender


tracker_router = Router()


@tracker_router.message(F.text.contains("Статус за день"))
@tracker_router.message(F.text == "/daily_total")
async def get_daily_total(message: Message):
    try:
        user_data = await get_user(message.from_user.id)
        await message.answer(
            text=f"Дневной лимит каллорий {user_data['current_energy']} из {user_data['energy_limit']}"
        )
        suggestion = await get_chatgpt_remaining_energy_suggestion(
            user_data["current_energy"],
            int(user_data["energy_limit"]) - int(user_data["current_energy"]),
        )
        await message.answer(text=suggestion)
    except Exception as e:
        logger.error(f"{e}")
        await message.answer(text="Some error ocured")


@tracker_router.message(F.photo)
async def parse_photo(message: Message):
    user_id = message.from_user.id
    is_allowed = await permission_allowed(user_id, 1)
    if not is_allowed:
        await message.answer("Недостаточно прав")
        return None

    async with ChatActionSender.typing(bot=bot, chat_id=user_id):
        file_in_io = io.BytesIO()
        file = await bot.get_file(message.photo[-1].file_id)
        await bot.download_file(file.file_path, file_in_io)
        b64_photo = encode_image(file_in_io.read())

        text = None  # message.caption
        if text is not None:
            response = await get_chatgpt_photo_description(b64_photo, text)
        else:
            response = await get_chatgpt_photo_description(b64_photo)
        model_output = eval(response["content"])
        output = form_output(model_output)
        await pg_log_message(message, model_output, b64_photo)
        await update_user(user_id, {"last_image_message_id": message.message_id})

        await add_daily_energy(user_id, output[1])
        await message.answer(text=output[0])
