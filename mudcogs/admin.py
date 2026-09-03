# Some comments in this Cog may "re-explain" things commented on later in the alphabetical list,
# contrary to what I mentioned earlier in the Cog list. This is because I remembered to add this last! :D
import disnake
from disnake import ApplicationCommandInteraction, \
    Forbidden, HTTPException  # Imports the error handler classes from Disnake.
from disnake.ext import commands
from disnake.ext.commands import MissingRole

import json  # Imports the JSON module, which is useful in editing JSON objects.


class Admin(commands.Cog):  # Declares a class, which is going to be a disnake Cog. All of our functions live in this.
    def __init__(self, bot):  # Defines variables which will be inherited by other functions in this Cog.
        self.bot = bot  # Bot is inherited from above and passed down below.

    async def cog_slash_command_check(self, inter: ApplicationCommandInteraction):  # Defines a check, which executes
        # before any command in this Cog is run. This one checks to make sure the user has the Admin role before
        # processing any command.
        admin = disnake.utils.get(inter.guild.roles, name="Admin")  # Grabs the "Admin" Role object from the guild's
        # role list.
        if admin not in inter.author.roles:  # Functions in this block execute if the Admin role is not in the
            # roles of the user executing the command.
            raise MissingRole(admin.id)  # Raises a MissingRole exception, to be handled later.
        return admin in inter.author.roles  # Returns a pass, if the check passed.

    @commands.slash_command(description="ADMIN. Cleans non-Aether world roles from the server role list.",
                            name="clean_worlds")  # This is a quick and dirty command to make things a bit easier
    # for the Aether Hunts team as they move out from world roles. Not designed to stay.
    @commands.contexts(guild=True)
    async def clean_worlds(self, inter):
        aether = []
        others = []
        with open("worlds.json", "r+") as worlds:
            data = json.load(worlds)
        count = 0
        for world in data["worlds"]["aether_dc"]:
            aether.append(data["worlds"]["aether_dc"][f"{count}"]["name"])
            count += 1
        count = 0
        for world in data["worlds"]["servers"]:
            if data["worlds"]["servers"][f"{count}"]["name"] not in aether:
                others.append(data["worlds"]["servers"][f"{count}"]["name"])
                count += 1
            elif data["worlds"]["servers"][f"{count}"]["name"] in aether:
                count += 1
                continue
        count = 0
        for role in inter.guild.roles:
            if role.name in others:
                await role.delete()
                count += 1
        await inter.response.send_message(content=f"Deleted {count} role{'s' if count != 1 else ''}.")

    @commands.slash_command(description="ADMIN. Sets whether the level gate should exist.", name="gate")  # Declares a
    # Slash Command, which is objectively the best and coolest way to have commands on any chat platform on the
    # Internet! Don't believe me? Wait until you hear THESE wacky methods for enforcing Slash Commands over Message
    # Commands for all developers!
    # Note the "ADMIN" at the beginning of the description. I rant about this later in the Rep cog, I can guarantee
    # that. Peep there for all the tea.
    @commands.contexts(guild=True)  # A decorator which states that the command can only be used in a guild. Oh,
    # and because I don't say it anywhere else in these comments: Discord Servers are known as "Guilds" internally.
    # A leftover from when this app used to be more gamer-focused. Now it's gamer-focused... Again.
    # Don't worry about it.
    async def gate(self, inter, gate: bool):  # Defines a function, with the gate option being a boolean (True/False)
        # input from the user.
        await inter.response.defer()  # To prevent Interactions from timing out, this is sent first to give Mudbot
        # time to react, since Discord only gives bots 3 seconds to respond to Interactions without this.
        with open("server_config.json", "r+") as server_config:  # Opens a file on the host machine.
            data = json.load(server_config)  # Loads the aforementioned file as a JSON object.
            update = {"state": f"{str(gate)}"}  # Updates a line in the JSON object.
            data["server_config"][str(inter.guild.id)]["level_gate"].update(update)  # SUPER updates a line in the JSON
            # object.
            server_config.seek(0)  # Seeks to the beginning of the file; shit breaks if this isn't here. Trust me.
            json.dump(data, server_config, indent=4)  # ULTRA updates a line in the JSON object. No, but, for real.
            # This line commits the change to the file.
            server_config.truncate()  # Truncates any errant spaces in the file.
        embed = disnake.Embed(color=disnake.Color(0x3b9da5),
                              description=f"The level gate configuration has been set to {str(gate)}.",
                              title="Configuration updated.")  # Declares the beginning of and the first few arguments
        # to an Embed object.
        embed.set_author(icon_url=self.bot.user.avatar.url, name=self.bot.user.name)  # Sets the author of the embed
        # as the bot.
        embed.set_thumbnail(url=inter.guild.icon)  # Adds a pretty picture to the embed. This one's the guild icon.
        embed.set_footer(icon_url=self.bot.user.avatar.url, text=self.bot.user.name)  # Adds a footer to the embed.
        # This one has the bot's icon and name.
        await inter.response.edit_original_response(delete_after=300, embed=embed)  # Edits the deferred Interaction
        # with the output embed, then deletes it after 300 seconds (5 minutes).

    @commands.slash_command(description="ADMIN. Sets the level gate level.", name="level")
    @commands.contexts(guild=True)
    async def level(self, inter, level: int):  # Does a lot of the same as the above function, just with a number
        # instead of a boolean.
        await inter.response.defer()
        with open("server_config.json", "r+") as server_config:
            data = json.load(server_config)
            update = {"level": f"{str(level)}"}
            data["server_config"][str(inter.guild.id)]["level_gate"].update(update)
            server_config.seek(0)
            json.dump(data, server_config, indent=4)
            server_config.truncate()
        embed = disnake.Embed(color=disnake.Color(0x3b9da5),
                              description=f"The level gate configuration has been set to {str(level)}.",
                              title="Configuration updated.")
        embed.set_author(icon_url=self.bot.user.avatar.url, name=self.bot.user.name)
        embed.set_thumbnail(url=inter.guild.icon)
        embed.set_footer(icon_url=self.bot.user.avatar.url, text=self.bot.user.name)
        await inter.response.edit_original_response(delete_after=300, embed=embed)


def setup(bot):  # Sets up this above Class as a Cog within the bot.
    bot.add_cog(Admin(bot))
