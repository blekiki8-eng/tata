# Додай цей маршрут у список арі
async def sell_to_system(request):
    data = await request.json()
    u_id, item_id = str(data.get("user_id")), data.get("item_id")
    
    # Визначаємо ціну викупу системою (наприклад, 50% від номіналу або фіксовано)
    prices = {"fish_1": 10, "fish_2": 25, "fish_3": 150}
    sell_price = prices.get(item_id, 5)

    user = await users_col.find_one({"user_id": u_id})
    inv = user.get("inventory", [])
    
    for idx, item in enumerate(inv):
        if item["id"] == item_id:
            inv.pop(idx)
            await users_col.update_one(
                {"user_id": u_id}, 
                {"$set": {"inventory": inv}, "$inc": {"coins": sell_price}}
            )
            return web.json_response({"ok": True, "new_balance": user['coins'] + sell_price})
            
    return web.json_response({"ok": False})

# Не забудь зареєструвати маршрут:
# app.router.add_post('/api/sell_system', sell_to_system)
