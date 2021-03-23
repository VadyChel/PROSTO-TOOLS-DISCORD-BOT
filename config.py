import os


class Config:
	# Client config
	DEF_PREFIX = 'p.'
	OWNERS = (660110922865704980,)
	SHOPLIST_COSTS = [500, 1000, 100, 1100, 100, 600]
	MIN_BALANCE = -5000
	TEMP_PATH = './data/tempfiles/'
	DEF_PROFILE_BG = './data/images/lime.png'
	FONT = './data/fonts/a_AlternaSw.ttf'
	SAVE_IMG = './data/images/usercard.png'
	BOT_NAME = 'ProstoTools.exe'
	BOT_ID = 700767394154414142
	HELP_SERVER = 'https://discord.gg/6SHKgj43r9'
	FOOTER_TEXT = 'ProstoTools.exe || Copyright 2020-2021'
	MUTE_ROLE = 'PT-MUTED'
	VMUTE_ROLE = 'PT-VMUTED'
	SOFTBAN_ROLE = 'PT-SOFT-BANNED'
	CAPTCHA_ROLE = "PT-CHECKING"
	COLOR_ROLE = 'PT-COLOR-'
	TOKEN = os.getenv('BOT_TOKEN')
	ALLOWED_COGS = (
		"Clans",
		"Different",
		"Economy",
		"Games",
		"Moderate",
		"Settings",
		"Utils",
		"Reminders",
		"StatusReminders",
		"Works",
		"FunOther",
		"FunEditImage",
		"FunRandomImage",
		"Information"
	)

	# Database config
	DB_PASSWORD = os.getenv('DB_PASSWORD')
	DB_HOST = os.getenv('DB_HOST')
	DB_USER = os.getenv('DB_USER')
	DB_DATABASE = os.getenv('DB_DATABASE')