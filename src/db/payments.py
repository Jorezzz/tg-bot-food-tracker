from db.users import update_user


async def update_user_balance(user_id, new_balance):
    await update_user(user_id, {"balance": new_balance})
