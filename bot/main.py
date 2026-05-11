from __future__ import annotations

from bot.client import StarCitizenHubBot
from bot.config import LOG_DIR, load_config
from bot.utils.logger import setup_logging


def main() -> None:
    config = load_config()
    setup_logging(LOG_DIR, config.log_level)
    bot = StarCitizenHubBot(config)
    bot.run(config.token, log_handler=None)
