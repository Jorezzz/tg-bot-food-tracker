async def permission_allowed(user, minimum_role_id):
    if int(user["role_id"]) >= minimum_role_id:
        return True
    return False


async def check_if_valid_balance(user, required_balance):
    if int(user["role_id"]) >= 3:
        return True
    if int(user["balance"]) >= int(required_balance):
        return True
    return False
