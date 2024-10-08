async def permission_allowed(user, minimum_role_id):
    if int(user.get("role_id", 0)) >= minimum_role_id:
        return True
    return False


async def check_if_valid_balance(user, required_balance):
    if int(user.get("role_id", 0)) >= 3:
        return True
    if int(user.get("balance", 0)) >= int(required_balance):
        return True
    return False
