import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ChatMemberStatus

from config import BOT_TOKEN, CHANNEL_ID, CHANNEL_URL, BOT_USERNAME
from database import init_db, register_user, get_points, deactivate_user, get_referrer, get_top_users, user_exists

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    args = message.text.split()
    referrer_id = None
    
    if len(args) > 1 and args[1].isdigit():
        referrer_id = int(args[1])
        if referrer_id == user_id:
            referrer_id = None
    
    if register_user(user_id, referrer_id):
        if referrer_id:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📢 Вступить в канал", url=CHANNEL_URL)]
            ])
            await message.answer(
                f"🎉 Вы зарегистрированы по реферальной ссылке!\n\n"
                f"📢 Вступите в канал, чтобы активировать очки:\n"
                f"{CHANNEL_URL}\n\n"
                f"🔥 Ваша реферальная ссылка:\n"
                f"https://t.me/{BOT_USERNAME}?start={user_id}\n\n"
                f"💰 За каждого друга вы получите +2 очка!",
                reply_markup=keyboard
            )
        else:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📢 Вступить в канал", url=CHANNEL_URL)]
            ])
            await message.answer(
                f"👋 Добро пожаловать, {message.from_user.first_name}!\n\n"
                f"🔥 Ваша реферальная ссылка:\n"
                f"https://t.me/{BOT_USERNAME}?start={user_id}\n\n"
                f"📢 Вступите в канал:\n"
                f"{CHANNEL_URL}\n\n"
                f"💰 За каждого друга вы получите +2 очка!",
                reply_markup=keyboard
            )
    else:
        points = get_points(user_id)
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📢 Вступить в канал", url=CHANNEL_URL)]
        ])
        await message.answer(
            f"✋ Вы уже зарегистрированы!\n\n"
            f"🏆 Ваши очки: {points}\n\n"
            f"🔥 Ваша реферальная ссылка:\n"
            f"https://t.me/{BOT_USERNAME}?start={user_id}",
            reply_markup=keyboard
        )

@dp.message(Command("link"))
async def cmd_link(message: types.Message):
    user_id = message.from_user.id
    
    if not user_exists(user_id):
        register_user(user_id, None)
    
    points = get_points(user_id)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Вступить в канал", url=CHANNEL_URL)]
    ])
    
    await message.answer(
        f"🔗 Ваша реферальная ссылка:\n"
        f"https://t.me/{BOT_USERNAME}?start={user_id}\n\n"
        f"🏆 Ваши очки: {points}\n\n"
        f"💡 Как это работает:\n"
        f"• Отправьте ссылку другу\n"
        f"• Друг переходит по ссылке и запускает бота\n"
        f"• Друг вступает в канал {CHANNEL_URL}\n"
        f"• Вы получаете +2 очка\n"
        f"• Если друг выйдет → -2 очка",
        reply_markup=keyboard
    )

@dp.message(Command("score"))
async def cmd_score(message: types.Message):
    user_id = message.from_user.id
    
    if not user_exists(user_id):
        await message.answer("❓ Вы ещё не зарегистрированы. Напишите /start")
        return
    
    points = get_points(user_id)
    
    await message.answer(
        f"🏆 Ваш баланс: {points} очков\n\n"
        f"💡 Как получать очки:\n"
        f"• Приглашайте друзей по вашей ссылке\n"
        f"• Друг должен вступить в канал {CHANNEL_URL}\n"
        f"• Вы получаете +2 очка\n"
        f"• Если друг выйдет → -2 очка"
    )

@dp.message(Command("top"))
async def cmd_top(message: types.Message):
    top_users = get_top_users(10)
    
    if not top_users:
        await message.answer("📊 Пока никого нет в топе!")
        return
    
    text = "🏆 ТОП-10 ПРИГЛАШАЮЩИХ 🏆\n\n"
    
    for i, (user_id, score) in enumerate(top_users, 1):
        try:
            user = await bot.get_chat(user_id)
            name = user.first_name
            if user.username:
                name += f" (@{user.username})"
        except:
            name = f"Пользователь {user_id}"
        
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "📌"
        text += f"{medal} {i}. {name} — {score} очков\n"
    
    await message.answer(text)

@dp.my_chat_member()
async def track_channel_members(event: types.ChatMemberUpdated):
    if event.chat.id != CHANNEL_ID:
        return
    
    user_id = event.new_chat_member.user.id
    old_status = event.old_chat_member.status
    new_status = event.new_chat_member.status
    
    # Пользователь зашел в канал
    if new_status == ChatMemberStatus.MEMBER and old_status != ChatMemberStatus.MEMBER:
        print(f"✅ Пользователь {user_id} зашел в канал")
        
        # Проверяем, есть ли у пользователя пригласитель
        referrer_id = get_referrer(user_id)
        
        if referrer_id:
            # Начисляем очки пригласителю (если ещё не начислены за этот вход)
            print(f"👤 Пригласитель {referrer_id} получает +2 очка!")
            # Не начисляем повторно, если уже начислено при регистрации
        else:
            print(f"⚠️ У пользователя {user_id} нет пригласителя")
    
    # Пользователь вышел из канала
    elif old_status == ChatMemberStatus.MEMBER and new_status != ChatMemberStatus.MEMBER:
        print(f"❌ Пользователь {user_id} вышел из канала")
        deactivate_user(user_id)

@dp.message()
async def echo(message: types.Message):
    if message.text.startswith("/"):
        await message.answer(
            "❓ Неизвестная команда\n\n"
            "Доступные команды:\n"
            "/start - Начать\n"
            "/link - Моя реферальная ссылка\n"
            "/score - Мои очки\n"
            "/top - Топ приглашающих"
        )

async def main():
    init_db()
    
    try:
        chat = await bot.get_chat(CHANNEL_ID)
        print(f"✅ Бот подключен к каналу: {chat.title}")
    except Exception as e:
        print(f"⚠️ Ошибка: {e}")
        print(f"   Убедись, что бот @{BOT_USERNAME} добавлен в канал как администратор!")
    
    print("🚀 Бот запущен!")
    print(f"🤖 Бот: https://t.me/{BOT_USERNAME}")
    print(f"📢 Канал: {CHANNEL_URL}")
    
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())