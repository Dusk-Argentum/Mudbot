# Version 3.0 of Mudbot is a go!
import disnake  # Imports Disnake, the module used to communicate with Discord's API.
from disnake.ext import commands  # Imports the commands submodule from Disnake.

import os  # Imports the os builtin, for use in reaching the environment variables of the host machine.


DESCRIPTION = """A bot for use exclusively on the Aether Hunts Discord server (ID: 542602456132091904). \
Developed by Dusk Argentum (ID: 97153790897045504)."""  # Defines the bot's description.
# This variable goes unused, but I figured I'd keep it around for clarity's sake.
GUILD = 348897377400258560  # Defines the guild this bot is intended to be used on. Defaults to my test guild.
TESTS = []  # Defines an empty list of testing servers.
TOKEN = os.environ.get("Mudbot_TOKEN")  # Defines the token the bot uses to log in to Discord.
VERSION = "v3.0"  # Defines the current version of the bot.


if TOKEN == os.environ.get("Mudbot_TOKEN"):  # This conditional block sets the base guild to Aether Hunts if
    # the current version of the bot is the production version.
    GUILD = 542602456132091904
elif TOKEN == os.environ.get("Mudbot_BETA_TOKEN"):  # This conditional block sets the base guild to my testing server
    # if the current version of the bot is the beta version.
    GUILD = 348897377400258560
    TESTS = [348897377400258560]  # Fills the TESTS variable with my testing server.


command_sync_flags = commands.CommandSyncFlags.default()  # Defines the Command Sync Flags to the default ones. For use
# with all-beloved Slash Commands endpoints.


intents = disnake.Intents.default()  # Defines the Intents that Mudbot will need access to. Set to the default for now.


bot = commands.InteractionBot(command_sync_flags=command_sync_flags, intents=intents, test_guilds=TESTS,
                              owner_id=97153790897045504)  # Defines the bot as a bot. Which it is.


bot.load_extension("mudcogs.admin")
bot.load_extension("mudcogs.events")  # Loads the cogs, which are the subfiles where all the juicy stuff lives.
bot.load_extension("mudcogs.help")  # If you're reading these comments, hi! Also, I'm sorry!
bot.load_extension("mudcogs.owner")  # If you're following along and something isn't explained in the comments in the
bot.load_extension("mudcogs.rep")  # cog you're looking at, try checking one of the earlier cogs alphabetically.
bot.load_extension("mudcogs.tasks")  # I had to redo all the comments along with the code because so much shifted around
bot.load_extension("mudcogs.verification")  # and I'm looking forward to you suffering with me!


if __name__ == "__main__":  # This conditional block allows the bot to run if this is the main file. Which it is.
    bot.run(TOKEN)
