import os
import asyncio
import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
VOICE_CHANNEL_ID = 1495076456403959909  

intents = discord.Intents.default()
intents.message_content = True  
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Переменная-флаг, чтобы избежать одновременных попыток подключения
is_connecting = False

async def safe_connect(channel):
    global is_connecting
    if is_connecting:
        print("⏳ Подключение уже выполняется, пропускаем дублирующий запрос...")
        return None
        
    guild = channel.guild
    is_connecting = True
    
    # Корректно завершаем старые зависшие сессии
    if guild.voice_client:
        try:
            print("🔄 Закрываем старое подвисшее соединение...")
            await guild.voice_client.disconnect(force=True)
            await asyncio.sleep(2)
        except Exception:
            pass

    try:
        print(f'🔄 Попытка подключения к каналу: {channel.name}...')
        # self_deaf=True критически важен на BotHost, чтобы экономить трафик контейнера
        # Убрали жесткий таймаут в 20 секунд, чтобы дать discord.py завершить handshake самостоятельно
        vc = await channel.connect(reconnect=True, self_deaf=True)
        print(f'✅ Бот успешно зашел в канал: {channel.name}')
        return vc
    except Exception as e:
        print(f'❌ Ошибка при подключении к каналу: {e}')
        return None
    finally:
        is_connecting = False

# Оптимальный интервал проверки для BotHost
@tasks.loop(seconds=60)
async def check_voice_connection():
    """Фоновая задача проверки соединения"""
    if is_connecting:
        return

    channel = bot.get_channel(VOICE_CHANNEL_ID)
    if not channel:
        return

    guild = channel.guild
    vc = guild.voice_client

    # Запускаем ручное восстановление ТОЛЬКО если клиента вообще нет 
    # или он полностью отключен (не в режиме автоматического реконнекта)
    if not vc or not vc.is_connected():
        print("⚠️ Голосовое соединение полностью отсутствует. Восстанавливаем...")
        await safe_connect(channel)

@bot.event
async def on_ready():
    print(f'Бот {bot.user.name} успешно запущен!')
    channel = bot.get_channel(VOICE_CHANNEL_ID)
    
    if channel and isinstance(channel, discord.VoiceChannel):
        await safe_connect(channel)
        if not check_voice_connection.is_running():
            check_voice_connection.start()
    else:
        print('❌ Канал не найден или указан неверный ID!')

@bot.event
async def on_voice_state_update(member, before, after):
    """Событие срабатывает при изменении статуса голосовых каналов"""
    if member.id == bot.user.id:
        # Если бота принудительно кикнули из канала пользователи (был канал, теперь нет)
        if before.channel and not after.channel and not is_connecting:
            print("⚠️ Бот был принудительно отключен пользователем. Переподключаемся...")
            channel = bot.get_channel(VOICE_CHANNEL_ID)
            if channel:
                await safe_connect(channel)

bot.run(BOT_TOKEN)
