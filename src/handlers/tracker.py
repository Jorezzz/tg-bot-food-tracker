from aiogram import Router, F
from aiogram.types import Message
from create_bot import bot, OPENAI_TOKEN, logger
import io
from utils import encode_image
from model import get_chatgpt_description, form_output
from db.functions import add_daily_energy, get_user, update_user, pg_log_message


tracker_router = Router()


@tracker_router.message(F.text == "/daily_total")
async def get_daily_total(message: Message):
    try:
        user_data = await get_user(message.from_user.id)
        await message.answer(
            text=f"Дневной лимит каллорий {user_data['current_energy']} из {user_data['energy_limit']}"
        )
    except Exception as e:
        logger.error(f"{e}")
        await message.answer(text="Some error ocured")


@tracker_router.message(F.photo)
async def parse_photo(message: Message):
    file_in_io = io.BytesIO()
    file = await bot.get_file(message.photo[-1].file_id)
    await bot.download_file(file.file_path, file_in_io)
    b64_photo = encode_image(file_in_io.read())
    response = await get_chatgpt_description(b64_photo, OPENAI_TOKEN, logger)
    model_output = eval(response["content"])
    output = form_output(model_output)
    await pg_log_message(message, model_output, b64_photo)
    await update_user(
        message.from_user.id, {"last_image_message_id": message.message_id}
    )

    await add_daily_energy(message.from_user.id, output[1])
    await message.answer(text=output[0])
