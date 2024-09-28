import os
from dotenv import load_dotenv
import logging

load_dotenv()

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

OPENAI_TOKEN = os.environ["OPENAI_TOKEN"]
TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
PG_USER = os.environ["PG_USER"]
PG_DB = os.environ["PG_DB"]
PG_PWD = os.environ["PG_PWD"]
ADMIN_PASSWORD = os.environ["ADMIN_PASSWORD"]

OPENAI_SYSTEM_PROMPT = "Ты умный подсчитыватель каллорий. Определи, что за блюда и продукты представлены на картинках (скорее всего это блюда популярные в России), выпиши сколько они весят и сколько каллорий в каждом из них и в этом приёме пищи в целом. Если не можешь определить точно выдай наиболее похожий вариант. Ответ выдавай на русском языке."
OPENAI_SYSTEM_SUGGEST_PROMPT = "Ты умный подсчитыватель каллорий. Тебе будет прелложено то сколько каллорий уже употребил человек с начала дня, а также сколько каллорий осталось до его дневного лимита. Тебе нужно предложить сколько ещё приёмов пищи он может сделать и дать рекомендацию что он может скушать. Например если соталось мало (менее 200) каллорий, то стоит посоветовать не кушать ничего жирно или сладкого, если же лимит ещё большой то нужно отметить что он может позволить себе большойвыбор продуктов. Выдай ответ на русском языке, в паре предложений, сделай ответ походим на совет"

ROLE_ID = {"unregistered": 0, "user": 1, "premium_user": 2, "admin": 3}
