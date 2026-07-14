import disnake
from disnake.ext import commands, tasks  # Imports, in addition to the typical commands, the tasks submodule, which
# allows me to set tasks that execute at certain intervals.

import json

import random


class Tasks(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @tasks.loop(minutes=5)  # Declares a task which executes every 5 minutes.
    async def status_rotation(self):
        with open("bot_config.json", "r") as bot_config:
            data = json.load(bot_config)
        if data["bot_config"]["status"]["custom_status"] != "None":  # Reads the status section of the JSON object
            # and sets the custom status as the custom status if the custom status is "None", which is automatically
            # set if the status is supposed to rotate automatically.
            status = data["bot_config"]["status"]["custom_status"]
        else:
            status = (data["bot_config"]["status"]["statuses"]
            [str(random.randint(1, len(data["bot_config"]["status"]["statuses"])))])  # Reads the list of custom
# statuses the bot will normally rotate through and generates a random number between 1 and the maximum and sets the
        # status to that one. Notably: The "custom status" bit from earlier is a DIFFERENT custom status to this one;
        # the earlier "custom status" is used for statuses outside the random ones. Confusing, I know.
        await self.bot.change_presence(activity=disnake.Game(f"{status} | /help"))


def setup(bot):
    bot.add_cog(Tasks(bot))
