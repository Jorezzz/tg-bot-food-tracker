from create_bot import db_manager, logger

# async def pg_log_message(pool, message, user_id):
#     async with pool.acquire() as connection:
#         async with connection.transaction():
#             data = []
#             for _, dish in enumerate(data['dishes']):
#                 output += f"{dish['dish_name']}:\n"
#                 dish_total = 0
#                 for ingridient in dish['composition']:
#                     output += f"  {ingridient['ingridient_name']}: {ingridient['ingridient_mass_in_grams']} грамм - {ingridient['ingridient_callories']} каллорий\n"
#                     dish_total += int(ingridient['ingridient_callories'])
#                 output += f"В блюде {dish_total} каллорий\n\n"
#                 message_total += dish_total
#             output += f"\nВсего {message_total} каллорий"
#             return output, message_total
        
# def update_current_energy(pool, user_id,energy_to_add):

async def register_user(message):
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name
    async with db_manager as db:
        await db.insert_data_with_update(
            table_name='users',
            records_data={
                'user_id': user_id,
                'username': username,
                'first_name': first_name,
                'last_name': last_name,
            },
            conflict_column='user_id'
        )


async def get_user(user_id):
    async with db_manager as db:
        res = await db.select_data(
            table_name='users',
            where_dict={
                'user_id': user_id
            }
        )
        return res[-1]
      

async def update_user(user_id, update_dict):
    async with db_manager as db:
        await db.update_data(
            table_name='users',
            where_dict={
                'user_id': user_id
            },
            update_dict=update_dict
        )


async def add_daily_energy(user_id, energy_to_add):
    user_data = await get_user(user_id)
    current_energy = int(user_data['current_energy']) + energy_to_add
    await update_user(
        user_id, 
        update_dict={
            'current_energy': current_energy
        }
    )