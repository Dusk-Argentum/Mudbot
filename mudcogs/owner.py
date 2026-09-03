import disnake
from disnake import ApplicationCommandInteraction  # Imports the ApplicationCommandInteraction class from disnake for
# use in a check later.
from disnake.ext import commands
from disnake.ext.commands import NotOwner  # Imports the NotOwner exception, which is thrown when someone who isn't the
# owner tries to use any of these commands.

import json


class Owner(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_slash_command_check(self, inter: ApplicationCommandInteraction):  # Defines a check that checks if
        # the user running the command is the owner.
        if inter.author.id != self.bot.owner_id:
            raise NotOwner  # Raises the NotOwner exception if the user isn't the owner.
        return inter.author.id == self.bot.owner_id  # Returns an affirmative if the user is the owner.

    @commands.slash_command(description="OWNER. Sends a message as Mudbot.", name="echo")
    @commands.contexts(guild=True)
    async def echo(self, inter, words: str):  # Defines a command which takes the words argument and projects them back
        # out. Looks cooler when I can delete the context message, but that's not possible with Slash Commands.
        await inter.response.defer()
        await inter.response.edit_original_response(content=words)

    @commands.slash_command(description="OWNER. Lists the guilds the bot is on.", name="guilds")
    @commands.contexts(guild=True)
    async def guilds(self, inter):
        await inter.response.defer()
        embed = disnake.Embed(color=disnake.Color(0x3b9da5),
                             description=f"Leave an undesired guild with /leave.",
                             title="The guilds, as requested.")
        embed.set_author(icon_url=self.bot.user.avatar.url, name=self.bot.user.name)
        embed.set_thumbnail(url=inter.author.avatar.url)
        for guild in self.bot.guilds:  # Loops through every guild the bot is in and does the below.
            embed.add_field(inline=False, name=guild.id, value=guild.name)
        embed.set_footer(icon_url=self.bot.user.avatar.url, text=self.bot.user.name)
        await inter.response.edit_original_response(delete_after=300, embed=embed)

    @commands.slash_command(description="OWNER. Leaves the specified server.", name="leave")
    @commands.contexts(guild=True)
    async def leave(self, inter, guild: int):
        await inter.response.defer()
        guild = self.bot.get_guild(guild)  # Gets the guild by the ID specified in the guild argument.
        await guild.leave()  # Leaves the aforementioned guild.
        embed = disnake.Embed(color=disnake.Color(0x3b9da5),
                              description=f"{self.bot.user.name} is no longer in {guild.name} ({guild.id}).",
                              title="Guild left.")
        embed.set_author(icon_url=self.bot.user.avatar.url, name=self.bot.user.name)
        embed.set_thumbnail(url=inter.author.avatar.url)
        embed.set_footer(icon_url=self.bot.user.avatar.url, text=self.bot.user.name)
        await inter.response.edit_original_response(delete_after=300, embed=embed)

    @commands.slash_command(description="OWNER. Sets whether the status should rotate.", name="rotate")
    @commands.contexts(guild=True)
    async def rotate(self, inter, rotate: bool):  # Takes rotate boolean (True/False) argument.
        await inter.response.defer()
        with open("bot_config.json", "r+") as bot_config:  # Opens a file on the host machine in the bot's program
            # directory in the read+ mode (basically a fancy way of saying "do whatever").
            data = json.load(bot_config)  # Loads the file as a JSON object.
            update = {"state": f"{str(rotate)}"}  # Updates a dict within the JSON object with the specified value.
            data["bot_config"]["status"].update(update)  # Commits the update to the dict.
            if rotate:  # Functions in this block execute if rotate was True.
                update = {"custom_status": "None"}
                data["bot_config"]["status"].update(update)  # Does the same as before but for a different line.
                # This makes the status able to rotate again.
            bot_config.seek(0)  # Moves the "cursor" to the beginning of the file. Freaks out if not used. Trust me.
            json.dump(data, bot_config, indent=4)  # Commits the updated data to the file.
            bot_config.truncate()  # Removes errant spaces.
        embed = disnake.Embed(color=disnake.Color(0x3b9da5),
                              description=f"The status rotation configuration has been set to {str(rotate)}.",
                              title="Configuration updated.")
        embed.set_author(icon_url=self.bot.user.avatar.url, name=self.bot.user.name)
        embed.set_thumbnail(url=inter.author.avatar.url)
        embed.set_footer(icon_url=self.bot.user.avatar.url, text=self.bot.user.name)
        await inter.response.edit_original_response(delete_after=300, embed=embed)

    @commands.slash_command(description="OWNER. Sets the status.", name="set")
    @commands.contexts(guild=True)
    async def set(self, inter, status: str):  # Takes the status argument as a custom status to set on the bot.
        # This is where "Playing:" used to go. It's the little text beneath the bot's name on the Member List.
        await inter.response.defer()
        with open("bot_config.json", "r+") as bot_config:
            data = json.load(bot_config)
            update = {"state": "False"}
            data["bot_config"]["status"].update(update)
            update = {"custom_status": f"{status}"}
            data["bot_config"]["status"].update(update)
            bot_config.seek(0)
            json.dump(data, bot_config, indent=4)
            bot_config.truncate()
        await self.bot.change_presence(activity=disnake.Game(f"{status} | /help"))  # Updates the bot's "Presence"
        # (which encapsulates a bunch of things, but we use it only for Custom Status) to the specified status.
        embed = disnake.Embed(color=disnake.Color(0x3b9da5),
                              description=f"The custom status is now `{status}`.",
                              title="Configuration updated.")
        embed.set_author(icon_url=self.bot.user.avatar.url, name=self.bot.user.name)
        embed.set_thumbnail(url=inter.author.avatar.url)
        embed.set_footer(icon_url=self.bot.user.avatar.url, text=self.bot.user.name)
        await inter.response.edit_original_response(delete_after=300, embed=embed)


def setup(bot):
    bot.add_cog(Owner(bot))
