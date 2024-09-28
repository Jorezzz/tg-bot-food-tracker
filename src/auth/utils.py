from db.functions import get_user
from config import logger, ROLE_ID


async def permission_allowed(user_id, minimum_role_id):
    user = await get_user(user_id)
    if int(user.get("role_id", 0)) >= minimum_role_id:
        return True
    logger.info(f"Faild permission check {user_id=}")
    return False
