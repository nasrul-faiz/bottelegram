import logging
from bot import Bot

if __name__ == "__main__":
    logging.info("Starting bot...")
    try:
        bot = Bot()
        print("Bot instance created successfully")
        bot.run()
    except Exception as e:
        logging.error(f"Error running bot: {e}")
        import traceback
        traceback.print_exc()
        raise
