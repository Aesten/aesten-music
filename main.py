from scripts import env, bot, scheduler

if __name__ == '__main__':
    env.load()
    scheduler.start()
    bot.start_bot()
