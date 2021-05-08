import logging
from logging.handlers import RotatingFileHandler

logging.basicConfig(
    level=logging.DEBUG,
    filename='ya_hw_bot.log',
    filemode='a',
    format='%(asctime)s, %(levelname)s, %(message)s, %(name)s',
)

# настройка логгера 1
logger = logging.getLogger()
logging.getLogger('urlib3').setLevel(logging.WARNING)
logging.getLogger('telegram').setLevel(logging.WARNING)
handler = RotatingFileHandler('ya_hw_bot.log', maxBytes=2000000, backupCount=5)
logger.addHandler(handler)
