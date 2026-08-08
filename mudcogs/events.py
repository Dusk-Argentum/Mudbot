import asyncio  # Imports asyncio for use in sleeping. Bot gets cranky if not given one second upon startup to wake up.

from datetime import datetime, timezone  # Imports the datetime module for use in gathering error timestamps.

import disnake
from disnake import InteractionResponded  # Imports the disnake exception for if an Interaction was already responded
# to. Why, yes, this one word comment IS a waste of a line!
from disnake.ext import commands
from disnake.ext.commands import CheckFailure, CommandInvokeError, MemberNotFound, MissingRole, MissingAnyRole, NotOwner
# Imports various exceptions for use in the handler below.

from mudcogs import tasks  # Imports the tasks module, so the bot can do those upon startup.


class Events(commands.Cog):  # Defines the class in which all functions in this cog are held.
    def __init__(self, bot):  # On initialization of this cog, sets the below variables to be inherited by functions.
        self.bot = bot

    @commands.Cog.listener()  # Defines a listener, which is basically just something that the bot is looking out for
    # while running.
    async def on_slash_command_error(self, inter, error):  # This one is listening for errors when a Slash Command is
        # run.
        raw_error = error  # Renames the error for use in later logging.
        if isinstance(error, CheckFailure):  # Functions in this block execute if the error passed is a CheckFailure,
            # which happens if a disnake check fails to pass.
            if inter.data.name in ["conductor", "spawner"] and "rolerequest" not in inter.channel.name:  # Functions in
                # this block execute if the command used is the conductor or spawner commands and the command is invoked
                # in a channel that does NOT have "rolerequest" in the name.
                error = "This command must be used in a role request ticket."  # Defines a user-readable error message.
        if isinstance(error, CommandInvokeError):  # Functions in this block execute on general command errors.
            error = "Incorrect invocation. Please re-examine the command in `/help`."
        if isinstance(error, MemberNotFound):  # Functions in this block execute if the provided member is invalid.
            error = "Member not found. Please make the user is a Member of the server."
        if isinstance(error, MissingRole):
            error = "You do not have permission to run this command."
        if isinstance(error, MissingAnyRole):  # Functions in this block execute if the user is lacking a specified role
            # as mentioned in a command's checks.
            error = "You do not have permission to run this command."
        if isinstance(error, NotOwner):  # Functions in this block execute if you're anyone but me.
            error = "You're not cool enough to run this command."
        channel = self.bot.get_channel(917980973306638346)  # Defines the channel variable as the error logging channel
        # on my testing guild.
        embed = disnake.Embed(color=disnake.Color(0x3b9da5), description="An exception was caught.", title="Error!")
        # Defines the start and first few arguments to an Embed.
        embed.set_author(icon_url=self.bot.user.avatar.url, name=self.bot.user.name)  # Sets the author of the Embed to
        # Mudbot.
        embed.set_thumbnail(url=self.bot.user.avatar.url)  # Sets the thumbnail image in the Embed to Mudbot's avatar.
        timestamp = int((datetime.strptime(str(datetime.now(timezone.utc).replace(microsecond=0, tzinfo=None)),
                                           "%Y-%m-%d %H:%M:%S") -
                         datetime.strptime("1970-01-01", "%Y-%m-%d")).total_seconds())  # Creates
        # a UNIX timestamp by subtracting the time at epoch from the current time and expresses it in seconds,
        # which allows for the creation of a Discord timestamp.
        value = f"""A command invoked by {inter.author.mention} (`{inter.author.id}`) on \
<t:{timestamp}:F> in {f"{inter.channel.mention} (`{inter.channel.id}`)" if
inter.channel.type == disnake.ChannelType.text else f"a DM with {inter.author.mention} (`{inter.author.id}`)"} \
caused the error detailed below."""  # Throws together a bunch of aforementioned text into a description of the error;
        # the command invoker, the time it was invoked, and the place it was invoked are all listed.
        embed.add_field(inline=False, name="Source:", value=value)  # Adds an embed field with the above value used
        # for its text.
        embed.add_field(inline=False, name="Raw Error:", value=str(raw_error))  # Adds an embed field with the raw error
        # type attached.
        embed.add_field(inline=False, name="Message Sent:", value=error)  # Adds an embed field which lets me know what
        # the user-friendly error was.
        embed.add_field(inline=False, name="Message Context:",
                        value=f"""`/{inter.application_command.name} {str(inter.filled_options)}`""")  # Adds an embed
        # field with the exact command invocation... Ish. This looked better in Message Commands.
        embed.set_footer(icon_url=self.bot.user.avatar.url, text=self.bot.user.name)  # Sets the embed footer and fills
        # it with information about the bot.
        await channel.send(embed=embed)  # Sends the embed in the error log channel.
        embed = disnake.Embed(color=disnake.Color(0x9c2c37), description=f"Error: {error}",
                              title="We're sorry; an error occurred!")  # The following lines build the user-end
        # error message.
        embed.set_author(icon_url=self.bot.user.avatar.url, name=self.bot.user.name)
        embed.set_thumbnail(url="https://64.media.tumblr.com/d4a0b44f54423c5ea426122a99477127/9a071b6ba8cc2ed5-c9/s75x75_c1/e2b4df00ac22b12bc1404b017ae344ed2eb7e189.pnj")
        embed.set_footer(icon_url=self.bot.user.avatar.url, text=f"Please try again later.")
        try:  # Tries to execute the below block.
            await inter.response.send_message(delete_after=300, embed=embed, ephemeral=True)  # Sends the embed as
            # an ephemeral message, which can only be seen by the user.
        except InteractionResponded:  # If the above attempt failed and the exception thrown was that the Interaction
            # had already been responded to (Discord Interactions can only be responded to once, technically), it
            # edits the existing message.
            await inter.edit_original_response(attachments=None, components=None, embed=embed)
            # Edits the existing response, if it exists, and clears all message parts except for the embed, which is the
            # recently-defined one.

    @commands.Cog.listener()
    async def on_ready(self):  # This listener is listening for when the bot logs in.
        await asyncio.sleep(1)  # Gives it a fucking second to get used to its bearings. I guess. Behaves weirdly if
        # this isn't here.
        try:
            tasks.Tasks.status_rotation.start(self)  # Starts the status rotation task.
        except RuntimeError:  # Unless it can't, in which case, it just doesn't.
            pass
        print(f"{self.bot.user.name} online. Awaiting SLASH commands :).")  # Prints a message in the console, informing
        # me of a successful login and startup sequence.


def setup(bot):  # Sets up this above Class as a Cog within the bot.
    bot.add_cog(Events(bot))
