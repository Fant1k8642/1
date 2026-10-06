import os
import asyncio
import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv

# Загружаем переменные окружения из панели хостинга BotHost
load_dotenv()

# Получаем токен из настроек хостинга
BOT_TOKEN = os.getenv("BOT_TOKEN")

# ID голосового канала, в который бот должен зайти
VOICE_CHANNEL_ID = 1495076456403959909  

# Настройка намерений (Intents)
intents = discord.Intents.default()
intents.message_content = True  
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)

async def safe_connect(channel):
    """Безопасная функция подключения к войсу"""
    guild = channel.guild
    
    # Проверяем, не подключен ли бот уже
    if guild.voice_client:
        if guild.voice_client.channel.id == channel.id and guild.voice_client.is_connected():
            return guild.voice_client
        else:
            # Если бот в другом канале или завис — переподключаем
            await guild.voice_client.disconnect(force=True)
            await asyncio.sleep(1)

    try:
        # self_deaf=True заглушает бота (серьёзно снижает нагрузку на CPU/сеть BotHost)
        # reconnect=True разрешает библиотеке авто-переподключение
        vc = await channel.connect(reconnect=True, timeout=30.0, self_deaf=True)
        print(f'✅ Бот успешно зашел в канал: {channel.name}')
        return vc
    except Exception as e:
        print(f'❌ Ошибка при подключении к каналу: {e}')
        return None

@tasks.loop(seconds=15)
async def check_voice_connection():
    """Фоновая задача: каждые 15 секунд проверяет и восстанавливает войс"""
    channel = bot.get_channel(VOICE_CHANNEL_ID)
    if not channel:
        return

    guild = channel.guild
    vc = guild.voice_client

    # Если бот должен быть в канале, но вылетел — подключаем заново
    if not vc or not vc.is_connected():
        print("⚠️ Обнаружен разрыв голосового соединения. Восстанавливаем...")
        await safe_connect(channel)

@bot.event
async def on_ready():
    print(f'Бот {bot.user.name} успешно запущен и готов к работе!')
    
    # Поиск канала по ID
    channel = bot.get_channel(VOICE_CHANNEL_ID)
    
    if channel and isinstance(channel, discord.VoiceChannel):
        await safe_connect(channel)
        
        # Запускаем фоновую проверку соединения, если она еще не запущена
        if not check_voice_connection.is_running():
            check_voice_connection.start()
    else:
        print('❌ Канал не найден или ID не принадлежит голосовому каналу!')

@bot.event
async def on_voice_state_update(member, before, after):
    """Событие: если бота кикнули или сбросили соединение"""
    if member.id == bot.user.id:
        # Если бот отключился от войса
        if before.channel and not after.channel:
            print("⚠️ Бот был отключен от голосового канала. Пробуем переподключиться...")
            await asyncio.sleep(2)
            channel = bot.get_channel(VOICE_CHANNEL_ID)
            if channel:
                await safe_connect(channel)

# Запуск бота
bot.run(BOT_TOKEN)
