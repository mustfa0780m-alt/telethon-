import asyncio
from telethon import TelegramClient, events, types, functions

# ===== إعدادات البوت =====
api_id = 19544986
api_hash = '83d3621e6be385938ba3618fa0f0b543'
bot_token = '8426678140:AAG3721Hak7V0u_ACZOl2pQHzMgY7Udxk4k'
channel_username = '@sutazz'  # رابط القناة

client = TelegramClient('bot_session', api_id, api_hash).start(bot_token=bot_token)

# حفظ الأعضاء المقيّدين لتجنب تكرار الرسائل
restricted_users = {}  # dict: {user_id: chat_id}

async def is_subscribed(user_id):
    """التحقق من أن العضو مشترك في القناة"""
    try:
        await client.get_participant(channel_username, user_id)
        return True
    except:
        return False

async def restrict_member(chat_id, user_id):
    """تقييد العضو فقط من إرسال الرسائل"""
    try:
        await client(functions.channels.EditBannedRequest(
            channel=chat_id,
            participant=user_id,
            banned_rights=types.ChatBannedRights(
                until_date=None,
                send_messages=True,
                send_media=True,
                send_stickers=True,
                send_gifs=True,
                send_games=True,
                send_inline=True,
                embed_links=True
            )
        ))
    except:
        pass

async def unrestrict_member(chat_id, user_id):
    """رفع التقييد عن العضو"""
    try:
        await client(functions.channels.EditBannedRequest(
            channel=chat_id,
            participant=user_id,
            banned_rights=types.ChatBannedRights(
                until_date=None,
                send_messages=False,
                send_media=False,
                send_stickers=False,
                send_gifs=False,
                send_games=False,
                send_inline=False,
                embed_links=False
            )
        ))
    except:
        pass

@client.on(events.NewMessage)
async def handler(event):
    if not event.is_group:
        return

    sender = await event.get_sender()
    chat = await event.get_chat()
    user_id = sender.id

    # تجاهل البوت نفسه
    if user_id == (await client.get_me()).id:
        return

    username = f"@{sender.username}" if sender.username else sender.first_name

    subscribed = await is_subscribed(user_id)

    if subscribed:
        # رفع التقييد إذا كان موجود مسبقًا
        if user_id in restricted_users:
            await unrestrict_member(restricted_users[user_id], user_id)
            restricted_users.pop(user_id)
        return  # العضو مشترك، لا نقوم بأي تقييد

    # العضو غير مشترك
    if user_id not in restricted_users:
        # الرد برسالة تحذيرية مرة واحدة
        await event.reply(
            f"عزيزي {username}، يرجى الاشتراك في القناة: {channel_username} ثم يمكنك العودة والإرسال"
        )
        restricted_users[user_id] = chat.id
        await restrict_member(chat.id, user_id)

async def monitor_restrictions():
    """التحقق الدوري من جميع الأعضاء المقيّدين ورفع التقييد عند الاشتراك"""
    while True:
        await asyncio.sleep(10)  # التحقق كل 10 ثوانٍ
        to_remove = []
        for user_id, chat_id in restricted_users.items():
            try:
                if await is_subscribed(user_id):
                    await unrestrict_member(chat_id, user_id)
                    to_remove.append(user_id)
            except:
                continue
        for uid in to_remove:
            restricted_users.pop(uid, None)

async def main():
    await client.start()
    asyncio.create_task(monitor_restrictions())
    print("Bot is running...")
    await client.run_until_disconnected()

asyncio.run(main())