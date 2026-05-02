# Додай цю колекцію на початку файлу
market_col = db["market"]

# API: Виставити на продаж
async def list_on_market(request):
    data = await request.json()
    u_id = str(data.get("user_id"))
    item_id = data.get("item_id")
    price = int(data.get("price"))

    # Видаляємо ОДНУ рибу з інвентарю (використовуємо $pull з обмеженням через update_one)
    # Оскільки MongoDB $pull видаляє всі збіги, ми спочатку знаходимо юзера
    user = await users_col.find_one({"user_id": u_id})
    if not user or "inventory" not in user:
        return web.json_response({"ok": False, "message": "No inventory"})
    
    # Шукаємо індекс риби
    inv = user["inventory"]
    item_to_sell = next((i for i in inv if i["id"] == item_id), None)
    
    if item_to_sell:
        inv.remove(item_to_sell)
        await users_col.update_one({"user_id": u_id}, {"$set": {"inventory": inv}})
        
        # Додаємо на ринок
        await market_col.insert_one({
            "seller_id": u_id,
            "seller_name": user.get("name", "Fisherman"),
            "item_id": item_id,
            "price": price
        })
        return web.json_response({"ok": True})
    return web.json_response({"ok": False, "message": "Item not found"})

# API: Отримати всі лоти
async def get_market(request):
    cursor = market_col.find({})
    lots = await cursor.to_list(length=100)
    for l in lots: l.pop("_id")
    return web.json_response(lots)

# API: Купити
async def buy_from_market(request):
    data = await request.json()
    buyer_id = str(data.get("user_id"))
    lot_data = data.get("lot") # Передаємо дані лота
    
    price = lot_data["price"]
    seller_id = lot_data["seller_id"]
    item_id = lot_data["item_id"]

    buyer = await users_col.find_one({"user_id": buyer_id})
    if buyer["coins"] < price:
        return web.json_response({"ok": False, "message": "Not enough coins"})

    # Видаляємо з ринку
    res = await market_col.delete_one({"seller_id": seller_id, "item_id": item_id, "price": price})
    if res.deleted_count > 0:
        # Гроші від покупця до продавця
        await users_col.update_one({"user_id": buyer_id}, {"$inc": {"coins": -price}, "$push": {"inventory": {"id": item_id}}})
        await users_col.update_one({"user_id": seller_id}, {"$inc": {"coins": price}})
        return web.json_response({"ok": True})
    
    return web.json_response({"ok": False, "message": "Item already sold"})

# Не забудь додати ці маршрути в кінці bot.py:
# app.router.add_post('/api/list_item', list_on_market)
# app.router.add_get('/api/get_market', get_market)
# app.router.add_post('/api/buy_item', buy_from_market)
