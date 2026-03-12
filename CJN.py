import asyncio
import logging
import random
import time
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import Message, ChatMemberUpdated, InlineKeyboardMarkup, InlineKeyboardButton

# Токен бота
TOKEN = "8688344588:AAGobwSVDR6SzdkXakQT0tc-_HuQRdlIYVE"

# Включаем логирование
logging.basicConfig(level=logging.INFO)

# Создаем бота и диспетчер
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Словари для хранения данных
user_folds = {}      # {user_id: количество_складок}
user_kg = {}         # {user_id: общий вес в кг}
user_cooldowns = {}  # {user_id: время_последнего_фарма}

# КОГДА БОТА ДОБАВЛЯЮТ В ГРУППУ
@dp.my_chat_member()
async def bot_added_to_group(update: ChatMemberUpdated):
    if update.new_chat_member.status in ["member", "administrator"]:
        if update.old_chat_member.status in ["left", "kicked"]:
            await bot.send_message(update.chat.id, "вечер в хату, пасаны")

# Приветствие новых участников
@dp.message(F.new_chat_members)
async def new_member(message: Message):
    for member in message.new_chat_members:
        if not member.is_bot:
            await message.reply(f'вечер в хату, {member.first_name}')

# Команда /start с предложением добавить в группу
@dp.message(Command("start"))
async def start(message: Message):
    # Создаем клавиатуру с кнопкой для добавления бота
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="➕ Добавить бота в группу",
                url=f"https://t.me/{bot.username}?startgroup=true"
            )]
        ]
    )
    
    await message.reply(
        "🚬 вечер в хату, пасаны\n\n"
        "👤 **для себя:**\n"
        "/farm - фармить жировые складки (раз в 3 часа)\n"
        "/stats - моя статистика\n"
        "/reset - сбросить всё\n\n"
        "👥 **для группы:**\n"
        "/top - топ игроков\n"
        "добавь меня в группу и я буду приветствовать новых\n"
        "а также можно фармить складки прямо в группе!",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

# Команда /farm - получаем складки и килограммы
@dp.message(Command("farm"))
async def farm(message: Message):
    user_id = message.from_user.id
    current_time = time.time()
    
    # Ставим реакцию
    try:
        await message.react([{"type": "emoji", "emoji": "💩"}])
    except:
        pass
    
    # Проверка кулдауна
    if user_id in user_cooldowns:
        last_farm = user_cooldowns[user_id]
        time_passed = current_time - last_farm
        hours_passed = time_passed / 3600
        
        if hours_passed < 3:
            remaining = 3 - hours_passed
            hours = int(remaining)
            minutes = int((remaining - hours) * 60)
            await message.reply(f'⏳ осталось {hours}ч {minutes}м до следующего фарма')
            return
    
    # Генерируем случайные значения
    folds = random.randint(1, 10)  # 1-10 складок
    kg_per_fold = random.uniform(1.0, 2.0)  # каждая складка весит 1-2 кг
    total_kg = round(folds * kg_per_fold, 1)  # общий вес за фарм
    
    # Сохраняем данные
    user_folds[user_id] = user_folds.get(user_id, 0) + folds
    user_kg[user_id] = user_kg.get(user_id, 0) + total_kg
    user_cooldowns[user_id] = current_time
    
    await message.reply(
        f"✅ **фарм удался!**\n\n"
        f"• жировых складок: +{folds} 🥩\n"
        f"• вес одной складки: {kg_per_fold:.1f} кг\n"
        f"• общий вес: +{total_kg} кг ⚖️\n\n"
        f"📊 **всего:**\n"
        f"складок: {user_folds[user_id]}\n"
        f"вес: {user_kg[user_id]:.1f} кг",
        parse_mode="Markdown"
    )

# Команда /stats - статистика
@dp.message(Command("stats"))
async def stats(message: Message):
    user_id = message.from_user.id
    
    # Ставим реакцию
    try:
        await message.react([{"type": "emoji", "emoji": "💩"}])
    except:
        pass
    
    folds = user_folds.get(user_id, 0)
    kg = user_kg.get(user_id, 0)
    
    # Рассчитываем средний вес складки
    avg_kg = kg / folds if folds > 0 else 0
    
    if user_id in user_cooldowns:
        last_farm = user_cooldowns[user_id]
        time_passed = time.time() - last_farm
        if time_passed < 10800:
            remaining = 10800 - time_passed
            hours = int(remaining / 3600)
            minutes = int((remaining % 3600) / 60)
            next_farm = f"⏳ следующий фарм через: {hours}ч {minutes}м"
        else:
            next_farm = "✅ можно фармить! /farm"
    else:
        next_farm = "✅ можно фармить! /farm"
    
    await message.reply(
        f"📊 **твоя статистика:**\n\n"
        f"• жировых складок: {folds} 🥩\n"
        f"• общий вес: {kg:.1f} кг ⚖️\n"
        f"• средний вес складки: {avg_kg:.1f} кг\n\n"
        f"{next_farm}",
        parse_mode="Markdown"
    )

# КОМАНДА /top - ОБЩАЯ СТАТИСТИКА
@dp.message(Command("top"))
async def top(message: Message):
    # Ставим реакцию
    try:
        await message.react([{"type": "emoji", "emoji": "💩"}])
    except:
        pass
    
    if not user_folds:
        await message.reply("📊 пока никто не фармил складки")
        return
    
    # Сортируем пользователей по количеству складок
    sorted_by_folds = sorted(user_folds.items(), key=lambda x: x[1], reverse=True)[:10]
    # Сортируем пользователей по весу
    sorted_by_kg = sorted(user_kg.items(), key=lambda x: x[1], reverse=True)[:10]
    
    # Общая статистика
    total_users = len(user_folds)
    total_folds = sum(user_folds.values())
    total_kg_all = sum(user_kg.values())
    avg_folds = round(total_folds / total_users, 1)
    avg_kg = round(total_kg_all / total_users, 1)
    
    # Формируем топ по складкам
    folds_text = "**🥩 ТОП по складкам:**\n"
    for i, (uid, folds) in enumerate(sorted_by_folds, 1):
        try:
            user = await bot.get_chat(uid)
            name = user.first_name
        except:
            name = f"User{uid}"
        folds_text += f"{i}. {name}: {folds} складок\n"
    
    # Формируем топ по весу
    kg_text = "\n**⚖️ ТОП по весу:**\n"
    for i, (uid, kg) in enumerate(sorted_by_kg, 1):
        try:
            user = await bot.get_chat(uid)
            name = user.first_name
        except:
            name = f"User{uid}"
        kg_text += f"{i}. {name}: {kg:.1f} кг\n"
    
    # Общая статистика
    total_text = (
        f"\n**📊 ОБЩАЯ СТАТИСТИКА:**\n"
        f"• всего игроков: {total_users}\n"
        f"• всего складок: {total_folds}\n"
        f"• всего жира: {total_kg_all:.1f} кг\n"
        f"• в среднем на игрока: {avg_folds} складок / {avg_kg} кг"
    )
    
    await message.reply(
        folds_text + kg_text + total_text,
        parse_mode="Markdown"
    )

# Команда /reset - сброс
@dp.message(Command("reset"))
async def reset(message: Message):
    # Ставим реакцию
    try:
        await message.react([{"type": "emoji", "emoji": "💩"}])
    except:
        pass
    
    uid = message.from_user.id
    user_folds.pop(uid, None)
    user_kg.pop(uid, None)
    user_cooldowns.pop(uid, None)
    await message.reply('🧹 все данные обнулены')

# НА СЛОВО "БАН" - "ПАПЛАЧ"
@dp.message(F.text.lower().contains('бан'))
async def ban_handler(message: Message):
    # Ставим реакцию
    try:
        await message.react([{"type": "emoji", "emoji": "😢"}])
    except:
        pass
    
    await message.reply("паплач 😢")

# НА СЛОВО "БОТ" - "БОШ НА МЕСТЕ"
@dp.message(F.text.lower().contains('бот'))
async def bot_handler(message: Message):
    # Ставим реакцию
    try:
        await message.react([{"type": "emoji", "emoji": "🤖"}])
    except:
        pass
    
    await message.reply("бош на месте 🧠")

# НА УПОМИНАНИЕ @growbellybot - ОТКАЗ ОТ БРАКА
@dp.message(F.text.contains("@growbellybot"))
async def mention_handler(message: Message):
    # Ставим реакцию
    try:
        await message.react([{"type": "emoji", "emoji": "💔"}])
    except:
        pass
    
    await message.reply("нет нихачу брак, уйди 😤")

# СЕКРЕТНАЯ ФИЧА: на "окак" бот отвечает "окак" и ставит сердечко
@dp.message(F.text.lower() == 'окак')
async def oaka_handler(message: Message):
    # Ставим реакцию сердечко
    try:
        await message.react([{"type": "emoji", "emoji": "❤️"}])
    except:
        pass
    
    # Отвечаем "окак"
    await message.reply("окак 🤫")

# Обработчик неизвестных команд
@dp.message(F.text.startswith('/'))
async def unknown_command(message: Message):
    try:
        await message.react([{"type": "emoji", "emoji": "💩"}])
        await message.reply(
            '❌ неизвестная команда\n\n'
            'доступные:\n'
            '/farm - фармить складки\n'
            '/stats - статистика\n'
            '/top - общий топ\n'
            '/reset - сброс'
        )
    except:
        pass

# Ответ на "вечер в хату"
@dp.message(F.text.lower() == 'вечер в хату')
async def evening_reply(message: Message):
    await message.reply('вечер в хату, пасаны')

# Запуск
async def main():
    # Устанавливаем имя бота для ссылки
    await bot.delete_webhook(drop_pending_updates=True)
    bot_info = await bot.get_me()
    bot.username = bot_info.username
    
    print("🚀 Бот запущен...")
    print(f"Username: @{bot.username}")
    print("Доступные команды: /farm, /stats, /top, /reset")
    print("Секретная фича: 'окак' ❤️")
    print("Триггеры: 'бан' → паплач 😢, 'бот' → бош на месте 🧠")
    print("Упоминание @growbellybot → отказ от брака 💔")
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
