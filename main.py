import discord
from discord.ext import commands

# Токен вашего бота (получите на портале разработчиков Discord)
TOKEN = 'MTUxOTcwNzcwNjYyMDExNzEyNQ.GFx-R4.2UF49NZ6x1Encm-g9n1zuxkgVQEmYHBln1VJwM'

# ID голосового канала, в который бот должен зайти
VOICE_CHANNEL_ID = 1495076456403959909  # Замените на реальный ID

# Настройка намерений (Intents). Для работы с голосовыми каналами нужен voice_states
intents = discord.Intents.default()
intents.message_content = True  # Если захотите добавлять текстовые команды
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f'Бот {bot.user.name} успешно запущен и готов к работе!')
    
    # Поиск канала по ID
    channel = bot.get_channel(VOICE_CHANNEL_ID)
    
    if channel:
        if isinstance(channel, discord.VoiceChannel):
            try:
                # Подключение к голосовому каналу
                await channel.connect()
                print(f'Бот успешно зашел в канал: {channel.name}')
            except Exception as e:
                print(f'Не удалось подключиться к каналу: {e}')
        else:
            print('Указанный ID не принадлежит голосовому каналу!')
    else:
        print('Канал с таким ID не найден. Убедитесь, что бот добавлен на нужный сервер.')

# Запуск бота
bot.run(TOKEN)
