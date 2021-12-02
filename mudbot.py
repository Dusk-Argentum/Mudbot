# Welcome to the Mudbot rewrite.
import disnake  # Mudbot uses Disnake to connect and communicate with Discord. RIP d.py.
from disnake.ext import commands  # Imports the commands submodule of Disnake.


import os  # Imports the OS module, used to access environment variables.


DESCRIPTION = """A bot for use in the Aether Hunts Discord server. Made by Dusk Argentum#6530."""  # The bot's
# description.
GUILD = 348897377400258560  # The default GUILD global variable. Defines the ID of the testing server's guild.
PREFIX = "DEFAULT_PREFIX"  # The default PREFIX global variable. Defines the default prefix used to invoke the bot's
# commands.
TOKEN = os.environ.get("Mudbot_TOKEN")  # The token used to authenticate with Discord. Obscured in an
# environment variable.
VERSION = "v2.0.2"  # The version of the bot. Sometimes I forget to update it. It's fine.


if TOKEN == os.environ.get("Mudbot_TOKEN"):  # The following blocks re-set certain global variables depending on the
    # token used to connect to Discord.
    GUILD = 542602456132091904
    PREFIX = "+"
elif TOKEN == os.environ.get("Mudbot_BETA_TOKEN"):
    GUILD = 348897377400258560
    PREFIX = "-"
elif TOKEN == os.environ.get("Mudbot_REWRITE_TOKEN"):
    GUILD = 348897377400258560
    PREFIX = "="

intents = disnake.Intents.all()  # Defines the intents that the bot requires to work. Set to all.
# intents.members = True  # Enables the Members intent, which facilitates certain logs.


bot = commands.Bot(case_insensitive=True, command_prefix=PREFIX, description=DESCRIPTION, intents=intents,
                   owner_id=97153790897045504)  # Defines the bot as a bot and uses certain variables.


bot.remove_command("help")  # Removes the default help command in favor of a custom one.


bot.load_extension("mudcogs.cog_admin")  # The following lines load cogs.
bot.load_extension("mudcogs.cog_events")  # Cogs are a better way to sort related functions and commands.
bot.load_extension("mudcogs.cog_help")
bot.load_extension("mudcogs.cog_hunt")  # If you're reading through all this code and trying to make sense of it,
bot.load_extension("mudcogs.cog_mod")  # if something doesn't have a comment, look through previous cogs
bot.load_extension("mudcogs.cog_owner")  # (alphabetically) and it will likely be explained.
bot.load_extension("mudcogs.cog_rep")
bot.load_extension("mudcogs.cog_tasks")  # Or not. Commenting everything is hard.
bot.load_extension("mudcogs.cog_verification")


if __name__ == "__main__":  # Runs the bot if this is the main file. Since it is, it will.
    bot.run(TOKEN)  # Runs the bot, using the appropriate token to verify.
