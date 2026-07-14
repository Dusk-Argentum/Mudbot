from mudbot import VERSION  # Imports the VERSION variable from the main bot file.

import disnake
from disnake.ext import commands


class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(description="Shows a list of all commands.", name="help")  # Defines the existence of a
    # Slash Command, along with its description and name seen in the Discord client.
    @commands.contexts(guild=True)  # A decorator which declares that this command can only be used in guilds, not DMs
    # or Group DMs.
    async def help(self, inter):
        field_count = 0  # Starts a counter of the amount of fields in the message.
        admin = disnake.utils.get(inter.guild.roles, name="Admin")  # Retrieves a Role object from the Interaction's
        # guild named "Admin".
        mod = disnake.utils.get(inter.guild.roles, name="Nutty Moderator")
        rep = disnake.utils.get(inter.guild.roles, name="Nutty Rep")
        embed = disnake.Embed(color=disnake.Color(0x3b9da5), description="Click on a command to learn more.",
                              title="Mudbot: Commands")
        embed.set_author(icon_url=self.bot.user.avatar.url, name=self.bot.user.name)
        embed.set_thumbnail(url=self.bot.user.avatar.url)
        for cog in self.bot.cogs:  # This loop goes through all the Cogs in the bot and does everything below.
            cog_name = cog  # Sets the cog_name variable to the cog.
            if cog == "Admin" and admin not in inter.author.roles:
                continue
            if cog == "Events":  # If the name of the Cog is "Events", it does not list Commands from that Cog.
                continue  # The skipped Cogs do not have Commands in them, so this just speeds things up a little.
            elif cog == "Help":
                continue
            elif cog == "Owner" and inter.author.id != self.bot.owner_id:  # If the name of the Cog is "Owner",
                # and the user invoking the command is not the owner, it skips listing commands in this Cog.
                continue
            elif cog == "Rep":  # Same as the above Owner check, but for commands in the Rep Cog.
                if mod not in inter.author.roles:
                    if rep not in inter.author.roles:
                        continue
            elif cog == "Tasks":
                continue
            commands_list = []  # Defines an empty list for the Commands to be added to.
            for command in self.bot.get_cog(cog).get_slash_commands():  # Works through every Command in a given Cog.
                command = inter.guild.get_command_named(command.name)  # Gets the command name.
                commands_list.append(f"</{command.name}:{command.id}> | {command.description}")  # Adds to the
                # commands_list list with a Mention to the Command and its description.
                next_command = next(iter(self.bot.get_cog(cog).get_slash_commands()))  # Gets the next command after
                # the current one.
                command = inter.guild.get_command_named(next_command.name)
                next_command_append = f"</{command.name}:{command.id}> | {command.description}"
                if (len(str(commands_list)) + len(str(next_command_append))) > 1024:  # Abides by a Discord limitation;
                    # a field's description cannot be more than 1024 characters, so it builds a new field with the same
                    # name and commands after that one. Mostly just future-proofing.
                    embed.add_field(inline=False, name=f"{cog_name}", value=f"{'\n'.join(commands_list)}")
                    commands_list = []
                    field_count += 1  # Adds one to and then sets the field_count variable.
                    cog_name = ""
                    continue
            embed.add_field(inline=False, name=f"{cog_name}", value=f"{'\n'.join(commands_list)}")
        embed.set_footer(icon_url="https://cdn.discordapp.com/emojis/1288585929090400257.webp?size=160",
                         text=f"""Made by @dusk_argentum! | {VERSION}
Bot avatar by @pixel__toast on Twitter.""")  # Need it to be known that I intentionally didn't update the name of the
        # website. We all know what Twitter is.
        await inter.response.send_message(delete_after=300, embed=embed)


def setup(bot):
    bot.add_cog(Help(bot))
