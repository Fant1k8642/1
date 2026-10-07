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
            await guild.voice_client.disconnect(force=True)
            await asyncio.sleep(2)
        except Exception:
            pass

    try:
        print(f'🔄 Попытка подключения к каналу: {channel.name}...')
        # self_deaf=True критически важен на BotHost, чтобы не тратить входящий трафик
        vc = await channel.connect(reconnect=True, timeout=20.0, self_deaf=True)
        print(f'✅ Бот успешно зашел в канал: {channel.name}')
        return vc
    except Exception as e:
        print(f'❌ Ошибка при подключении к каналу: {e}')
        return None
    finally:
        is_connecting = False

# Увеличиваем интервал до 45 секунд, чтобы он превышал таймаут коннекта (20-30с)
@tasks.loop(seconds=45)
async def check_voice_connection():
    """Фоновая задача проверки соединения"""
    if is_connecting:
        return

    channel = bot.get_channel(VOICE_CHANNEL_ID)
    if not channel:
        return

    guild = channel.guild
    vc = guild.voice_client

    # Подключаем только если вообще нет войс-клиента или статус коннекта окончательно упал
    if not vc or not vc.is_connected():
        print("⚠️ Голосовое соединение отсутствует. Запускаем восстановление...")
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
    """Событие срабатывает только при реальном ручном кике бота из канала"""
    if member.id == bot.user.id:
        # Если бота именно выгнали (был канал, теперь нет)
        if before.channel and not after.channel and not is_connecting:
            print("⚠️ Бот был принудительно отключен пользователем. Переподключаемся...")
            channel = bot.get_channel(VOICE_CHANNEL_ID)
            if channel:
                await safe_connect(channel)

bot.run(BOT_TOKEN)
