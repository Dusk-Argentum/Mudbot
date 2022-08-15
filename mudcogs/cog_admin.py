import disnake
from disnake.ext import commands
from disnake.ext.commands import ChannelNotFound, MissingAnyRole  # Imports an exception handler.

import json  # Imports the json module for use in reading and writing JSON files.

import re  # Imports the regex module for use in extracting information.


class Admin(commands.Cog):  # Defines the Admin class and sets it as a cog.
    def __init__(self, bot):  # Sets the below variables upon initialization. I think. idk what this does tbh
        self.bot = bot

    async def cog_check(self, ctx):  # Defines a check that applies to every command in this cog.
        admin = disnake.utils.get(ctx.guild.roles, name="Admin")  # Gets the admin role by name.
        if admin not in ctx.author.roles:
            raise MissingAnyRole([1])
        return admin in ctx.author.roles  # Permits the command to execute if the admin role is in the author's roles.

    @commands.group(aliases=["ab", "autoban", "auto-ban"], brief="Adjust auto-ban settings.", case_insensitive=True,
                    help="Includes commands to toggle auto-ban on/off and adjust the threshold.", name="auto_ban",
                    usage="auto_ban [subcommand] <argument>")  # Defines a command.
    # Aliases are alternate names that also invoke the command, brief is a brief description of the command,
    # the case_insensitive argument allows the command to be run regardless of case, help is a verbose description
    # of what the command does, name defines the name of the command, and usage shows how the command is used.
    @commands.guild_only()  # Sets the command to only be usable in a guild context.
    async def auto_ban(self, ctx):  # Defines the function the command follows.
        if ctx.invoked_subcommand is not None:  # Functions in this block execute if the command has a subcommand
            # invoked as well. Only applies to command groups.
            return  # Stops processing of the command. In this case, it prevents the below code from running if
        # the command invoker invokes a subcommand.
        embed = disnake.Embed(color=disnake.Color(0x3b9da5), description=ctx.command.help, title=f"{ctx.command.name}")
        # Defines an embed. Color defines the color at the side of the embed, description defines the embed's
        # description, and title defines the embed's title.
        embed.set_author(icon_url=self.bot.user.display_avatar.url, name=self.bot.user.name)  # Sets the embed's author.
        # Icon_url defines the icon used in the author section, near the top of an embed, and name defines the name or
        # text.
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)  # Sets the embed's thumbnail. Url is the url of the image.
        arguments = []  # Defines an empty list, to be appended to.
        for argument in ctx.command.walk_commands():  # Loops for every thing in the list provided.
            if argument.parent.name == "auto_ban":  # Functions in this block execute if the argument's direct parent
                # is named "auto_ban".
                arguments.append(argument)  # Appends the argument to the end of the arguments list.
        arguments.sort(key=lambda argus: argus.name)  # Sorts the arguments list by the argument's name
        # alphabetically.
        for count, unused in enumerate(arguments):
            args = []
            if isinstance(arguments[count], commands.Group):  # Functions in this block execute if the thing selected
                # in the list of arguments (defined by the position it has in the list) is a group of commands.
                for arg in arguments[count].commands:
                    args.append(arg.name)
                args.sort()
            newline = "\n"  # Defines a variable as a newline for use later.
            embed.add_field(inline=False, name=f"""►`{arguments[count].name}` (Alias{"es" if
            len(arguments[count].aliases) > 1 else ""}: \
`{"`, `".join([str(alias) for alias in arguments[count].aliases])}`)""", value=f"""{arguments[count].help}\
{f'''{newline if len(arguments[count].commands) > 1 else ""}''' if isinstance(arguments[count], commands.Group) else
            ''''''}\
{f'''{f"►Argument{'s' if len(arguments[count].commands) > 1 else ''}"
 f": `{'`, `'.join(args)}`"}''' if
                            isinstance(arguments[count], commands.Group) else ''''''}""")  # This is ass.
            # I have come to a decision to leave this here. Everyone must know my sins.
            # This is a, uh, very bad way of simply listing all of a command's arguments and those command's arguments
            # direct arguments.
        embed.set_footer(icon_url=self.bot.user.display_avatar.url, text=self.bot.user.name)  # Sets the embed's footer.
        # Icon_url defines the url of the image in the footer, and the text defines the text.
        await ctx.send(embed=embed)  # Sends the message. In this instance, it sends the embed.

    @auto_ban.group(aliases=["s", "t", "toggle"], brief="Enable or disable auto-ban.", case_insensitive=True,
                    help="""Includes commands to toggle auto-ban on/off or change its state.""", name="state",
                    usage="auto_ban state (argument)")
    @commands.guild_only()
    async def state(self, ctx):
        if ctx.invoked_subcommand is None:
            with open("server_config.json", "r+") as server_config:  # Opens the server config file.
                data = json.load(server_config)  # Loads the JSON-formatted file as a json and defines the variable
                # that will be read and edited.
                if data["server_config"][str(ctx.guild.id)]["auto_punish"]["ban"]["state"] == "True":  # Functions in
                    # this block execute if the current guild's auto-ban function is set to True.
                    update = {"state": "False"}  # Updates the state to False.
                elif data["server_config"][str(ctx.guild.id)]["auto_punish"]["ban"]["state"] == "False":  # Vice versa.
                    update = {"state": "True"}
                state = data["server_config"][str(ctx.guild.id)]["auto_punish"]["ban"]["state"]  # Gets the existing
                # state.
                data["server_config"][str(ctx.guild.id)]["auto_punish"]["ban"].update(update)  # Updates the specified
                # JSON entry.
                server_config.seek(0)  # Moves the internal cursor to the beginning of the file.
                json.dump(data, server_config, indent=4)  # Writes the updated information to the file.
                server_config.truncate()  # Ensures that the file is properly formatted by stripping any unnecessary
                # whitespace created after updating the information with information that has less characters.
                # I prommy that makes sense.
            await ctx.send(f"""The auto-ban state was updated from {state} to \
{data["server_config"][str(ctx.guild.id)]["auto_punish"]["ban"]["state"]}.""")  # Informs the invoker.
        else:
            return

    @state.command(aliases=["disable"], brief="Disables auto-ban.", help="Disables auto-ban.", name="off",
                   usage="auto_ban state off")
    @commands.guild_only()
    async def off(self, ctx):
        with open("server_config.json", "r+") as server_config:
            data = json.load(server_config)
            if data["server_config"][str(ctx.guild.id)]["auto_punish"]["ban"]["state"] == "True":
                update = {"state": "False"}
            elif data["server_config"][str(ctx.guild.id)]["auto_punish"]["ban"]["state"] == "False":
                await ctx.send("Auto-ban is already disabled.")  # Does not change the state.
                return
            data["server_config"][str(ctx.guild.id)]["auto_punish"]["ban"].update(update)
            server_config.seek(0)
            json.dump(data, server_config, indent=4)
            server_config.truncate()
        await ctx.send("The auto-ban state was updated to False.")

    @state.command(aliases=["enable"], brief="Enables auto-ban.", help="Enables auto-ban.", name="on",
                   usage="auto_ban state on")
    @commands.guild_only()
    async def on(self, ctx):
        with open("server_config.json", "r+") as server_config:
            data = json.load(server_config)
            if data["server_config"][str(ctx.guild.id)]["auto_punish"]["ban"]["state"] == "False":
                update = {"state": "True"}
            elif data["server_config"][str(ctx.guild.id)]["auto_punish"]["ban"]["state"] == "True":
                await ctx.send("Auto-ban is already enabled.")
                return
            data["server_config"][str(ctx.guild.id)]["auto_punish"]["ban"].update(update)
            server_config.seek(0)
            json.dump(data, server_config, indent=4)
            server_config.truncate()
        await ctx.send("The auto-ban state was updated to True.")

    @auto_ban.command(aliases=["age"], brief="Sets auto-ban threshold.", help="""Sets the age threshold an account \
must meet without being auto-banned.""", name="threshold", usage="auto_ban threshold <threshold>")
    @commands.guild_only()
    async def threshold(self, ctx, threshold: str = "12h"):  # The threshold argument is set to a "12h" string by
        # default, which is what the threshold argument will be if none is provided.
        threshold = re.search(r"(^\d{1,2})(m$|h$|d$)", threshold, re.IGNORECASE)  # Searches the provided threshold
        # argument for a validly formatted argument. Returns None if not found.
        if threshold is None:  # Functions in this block execute if the threshold argument is not valid.
            await ctx.send("""Please use a valid duration in the format of (up to 2 digits)(**m**inutes/**h**ours/\
**d**ays), eg. "1h", "69d", "42m".""")  # I sure hope this makes sense to people reading it.
            return
        with open("server_config.json", "r+") as server_config:
            data = json.load(server_config)
            previous = data["server_config"][str(ctx.guild.id)]["auto_punish"]["ban"]["threshold"]
            update = {"threshold": threshold.group(1) + threshold.group(2)}
            data["server_config"][str(ctx.guild.id)]["auto_punish"]["ban"].update(update)
            server_config.seek(0)
            json.dump(data, server_config, indent=4)
            server_config.truncate()
        await ctx.send(f"The auto-ban threshold was updated from {previous} to \
{threshold.group(1)}{threshold.group(2)}.""")

    @commands.group(aliases=["ak", "autokick", "auto-kick"], brief="Adjust auto-kick settings.", case_insensitive=True,
                    help="Includes commands to toggle auto-kick on/off and adjust the threshold.", name="auto_kick",
                    usage="auto_kick [subcommand] <argument>")
    @commands.guild_only()
    async def auto_kick(self, ctx):
        if ctx.invoked_subcommand is not None:
            return
        embed = disnake.Embed(color=disnake.Color(0x3b9da5), description=ctx.command.help, title=f"{ctx.command.name}")
        embed.set_author(icon_url=self.bot.user.display_avatar.url, name=self.bot.user.name)
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        arguments = []
        for argument in ctx.command.walk_commands():
            if argument.parent.name == "auto_kick":
                arguments.append(argument)
        arguments.sort(key=lambda argus: argus.name)
        for count, argument in enumerate(arguments):
            newline = "\n"
            args = []
            if isinstance(arguments[count], commands.Group):
                for arg in arguments[count].commands:
                    args.append(arg.name)
                args.sort()
            embed.add_field(inline=False, name=f"""►`{arguments[count].name}` (Alias{"es" if
            len(arguments[count].aliases) > 1 else ""}: \
`{"`, `".join([str(alias) for alias in arguments[count].aliases])}`)""", value=f"""{arguments[count].help}\
{f'''{newline if len(arguments[count].commands) > 1 else ""}''' if isinstance(arguments[count], commands.Group) else
            ''''''}\
 {f'''{f"►Argument{'s' if len(arguments[count].commands) > 1 else ''}"
f": `{'`, `'.join(args)}`"}''' if
            isinstance(arguments[count], commands.Group) else ''''''}""")
        embed.set_footer(icon_url=self.bot.user.display_avatar.url, text=self.bot.user.name)
        await ctx.send(embed=embed)

    @auto_kick.group(aliases=["s", "t", "toggle"], brief="Enable or disable auto-kick.", case_insensitive=True,
                     help="""Includes commands to toggle auto-kick on/off or change its state.""", name="state",
                     usage="auto_kick state (argument)")
    @commands.guild_only()
    async def state_(self, ctx):  # This function includes an underscore at the end to avoid conflict with the other
        # function named "state" in this class (cog). Expect to see this again.
        if ctx.invoked_subcommand is None:
            with open("server_config.json", "r+") as server_config:
                data = json.load(server_config)
                if data["server_config"][str(ctx.guild.id)]["auto_punish"]["kick"]["state"] == "True":
                    update = {"state": "False"}
                elif data["server_config"][str(ctx.guild.id)]["auto_punish"]["kick"]["state"] == "False":
                    update = {"state": "True"}
                state = data["server_config"][str(ctx.guild.id)]["auto_punish"]["kick"]["state"]
                data["server_config"][str(ctx.guild.id)]["auto_punish"]["kick"].update(update)
                server_config.seek(0)
                json.dump(data, server_config, indent=4)
                server_config.truncate()
            await ctx.send(f"""The auto-kick state was updated from {state} to \
{data["server_config"][str(ctx.guild.id)]["auto_punish"]["kick"]["state"]}.""")
        else:
            return

    @state_.command(aliases=["disable"], brief="Disables auto-kick.", help="Disables auto-kick.", name="off",
                    usage="auto_kick state off")
    @commands.guild_only()
    async def off_(self, ctx):
        with open("server_config.json", "r+") as server_config:
            data = json.load(server_config)
            if data["server_config"][str(ctx.guild.id)]["auto_punish"]["kick"]["state"] == "True":
                update = {"state": "False"}
            elif data["server_config"][str(ctx.guild.id)]["auto_punish"]["kick"]["state"] == "False":
                await ctx.send("Auto-kick is already disabled.")
                return
            data["server_config"][str(ctx.guild.id)]["auto_punish"]["kick"].update(update)
            server_config.seek(0)
            json.dump(data, server_config, indent=4)
            server_config.truncate()
        await ctx.send("The auto-kick state was updated to False.")

    @state_.command(aliases=["enable"], brief="Enables auto-kick.", help="Enables auto-kick.", name="on",
                    usage="auto_kick state on")
    @commands.guild_only()
    async def on_(self, ctx):
        with open("server_config.json", "r+") as server_config:
            data = json.load(server_config)
            if data["server_config"][str(ctx.guild.id)]["auto_punish"]["kick"]["state"] == "False":
                update = {"state": "True"}
            elif data["server_config"][str(ctx.guild.id)]["auto_punish"]["kick"]["state"] == "True":
                await ctx.send("Auto-kick is already enabled.")
                return
            data["server_config"][str(ctx.guild.id)]["auto_punish"]["kick"].update(update)
            server_config.seek(0)
            json.dump(data, server_config, indent=4)
            server_config.truncate()
        await ctx.send("The auto-kick state was updated to True.")

    @auto_kick.command(aliases=["age"], brief="Sets auto-kick threshold.", help="""Sets the age threshold an account \
must exceed before being auto-kicked for failing to verify.""", name="threshold",
                       usage="auto_kick threshold <threshold>")
    @commands.guild_only()
    async def threshold_(self, ctx, threshold: str = "7d"):
        threshold = re.search(r"(^\d{1,2})(m$|h$|d$)", threshold, re.IGNORECASE)
        if threshold is None:
            await ctx.send("""Please use a valid duration in the format of (up to 2 digits)(**m**inutes/**h**ours/\
**d**ays), eg. "1h", "69d", "42m".""")
            return
        with open("server_config.json", "r+") as server_config:
            data = json.load(server_config)
            previous = data["server_config"][str(ctx.guild.id)]["auto_punish"]["kick"]["threshold"]
            update = {"threshold": threshold.group(1) + threshold.group(2)}
            data["server_config"][str(ctx.guild.id)]["auto_punish"]["kick"].update(update)
            server_config.seek(0)
            json.dump(data, server_config, indent=4)
            server_config.truncate()
        await ctx.send(f"""The auto-kick threshold was updated from {previous} to \
{threshold.group(1)}{threshold.group(2)}.""")

    @commands.group(aliases=["level"], brief="Commands for adjusting level-gating.", case_insensitive=True,
                    help="""Commands for adjusting level-gating settings, including the level and whether or not it \
is enabled.""", name="level_gate", usage="level_gate [subcommand] <argument>")
    @commands.guild_only()
    async def level_gate(self, ctx):
        if ctx.invoked_subcommand is not None:
            return
        embed = disnake.Embed(color=disnake.Color(0x3b9da5), description=ctx.command.help, title=f"{ctx.command.name}")
        embed.set_author(icon_url=self.bot.user.display_avatar.url, name=self.bot.user.name)
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        arguments = []
        for argument in ctx.command.walk_commands():
            if argument.parent.name == "level_gate":
                arguments.append(argument)
        arguments.sort(key=lambda argus: argus.name)
        for count, argument in enumerate(arguments):
            newline = "\n"
            args = []
            if isinstance(arguments[count], commands.Group):
                for arg in arguments[count].commands:
                    args.append(arg.name)
                args.sort()
            embed.add_field(inline=False, name=f"""►`{arguments[count].name}` (Alias{"es" if
            len(arguments[count].aliases) > 1 else ""}: \
`{"`, `".join([str(alias) for alias in arguments[count].aliases])}`)""", value=f"""{arguments[count].help}\
{f'''{newline if len(arguments[count].commands) > 1 else ""}''' if isinstance(arguments[count], commands.Group) else
            ''''''}\
{f'''{f"►Argument{'s' if len(arguments[count].commands) > 1 else ''}"
f": `{'`, `'.join(args)}`"}''' if
            isinstance(arguments[count], commands.Group) else ''''''}""")
        embed.set_footer(icon_url=self.bot.user.display_avatar.url, text=self.bot.user.name)
        await ctx.send(embed=embed)

    @level_gate.command(aliases=["l", "threshold"], brief="Sets the minimum level.", help="""Sets the minimum level \
a verifying member must have at least one class at or above in order to successfully verify.""", name="level",
                        usage="level_gate level <level>")
    @commands.guild_only()
    async def level(self, ctx, level: int = None):
        if level is None:
            await ctx.send("Please enter a valid level to gate users at.")
            return
        if level > 100:
            await ctx.send("We haven't quite gotten to 8.0 yet.")  # This will need to be changed in the future,
            # but it should suffice for now. No real way to grab the maximum level from the Lodestone or anything.
            return
        with open("server_config.json", "r+") as server_config:
            data = json.load(server_config)
            update = {"level": str(level)}
            data["server_config"][str(ctx.guild.id)]["level_gate"].update(update)
            server_config.seek(0)
            json.dump(data, server_config, indent=4)
            server_config.truncate()
        await ctx.send(f"The level gate has been updated to `{level}`.")

    @level_gate.group(aliases=["s", "t", "toggle"], brief="Enable or disable level gating.", case_insensitive=True,
                      help="""Includes commands to toggle the level gate on/off or change its state.""", name="state",
                      usage="level_gate state (argument)")
    @commands.guild_only()
    async def state__(self, ctx):
        if ctx.invoked_subcommand is None:
            with open("server_config.json", "r+") as server_config:
                data = json.load(server_config)
                if data["server_config"][str(ctx.guild.id)]["level_gate"]["state"] == "True":
                    update = {"state": "False"}
                elif data["server_config"][str(ctx.guild.id)]["level_gate"]["state"] == "False":
                    update = {"state": "True"}
                state = data["server_config"][str(ctx.guild.id)]["level_gate"]["state"]
                data["server_config"][str(ctx.guild.id)]["level_gate"].update(update)
                server_config.seek(0)
                json.dump(data, server_config, indent=4)
                server_config.truncate()
            await ctx.send(f"""The level gate state was updated from {state} to \
{data["server_config"][str(ctx.guild.id)]["level_gate"]["state"]}.""")
        else:
            return

    @state__.command(aliases=["disable"], brief="Sets the level gate state to off.", help="""Sets the bot \
to not gate lower-levelled characters from verifying.""", name="off", usage="level_gate state off")
    @commands.guild_only()
    async def off__(self, ctx):
        with open("server_config.json", "r+") as server_config:
            data = json.load(server_config)
            if data["server_config"][str(ctx.guild.id)]["level_gate"]["state"] == "False":
                await ctx.send("Level gating is already set to off.")
                return
            elif data["server_config"][str(ctx.guild.id)]["level_gate"]["state"] == "True":
                update = {"state": "False"}
                data["server_config"][str(ctx.guild.id)]["level_gate"].update(update)
                server_config.seek(0)
                json.dump(data, server_config, indent=4)
                server_config.truncate()
        await ctx.send("The level gating state was set to False.")

    @state__.command(aliases=["enable"], brief="Sets the level gate state to on.", help="""Sets the bot \
to gate lower-levelled characters from verifying.""", name="on", usage="level_gate state on")
    @commands.guild_only()
    async def on__(self, ctx):
        with open("server_config.json", "r+") as server_config:
            data = json.load(server_config)
            if data["server_config"][str(ctx.guild.id)]["level_gate"]["state"] == "True":
                await ctx.send("Level gating is already on.")
                return
            elif data["server_config"][str(ctx.guild.id)]["level_gate"]["state"] == "False":
                update = {"state": "True"}
                data["server_config"][str(ctx.guild.id)]["level_gate"].update(update)
                server_config.seek(0)
                json.dump(data, server_config, indent=4)
                server_config.truncate()
        await ctx.send("The level gate state was updated to True.")

    @commands.group(aliases=["miles"], brief="Commands for adjusting milestones.", case_insensitive=True,
                    help="""Commands for setting what channel milestone updates go to, whether they mention admins or \
the milestone achiever, whether or not the milestones functionality is enabled, and the threshold the milestone must \
achieve.
Milestones are always tied to Licensed Hunter.""", name="milestone", usage="milestone [subcommand] <argument>")
    # Congratulations to the longest command help.
    @commands.guild_only()
    async def milestone(self, ctx):
        if ctx.invoked_subcommand is not None:
            return
        embed = disnake.Embed(color=disnake.Color(0x3b9da5), description=ctx.command.help, title=f"{ctx.command.name}")
        embed.set_author(icon_url=self.bot.user.display_avatar.url, name=self.bot.user.name)
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        arguments = []
        for argument in ctx.command.walk_commands():
            if argument.parent.name == "milestone":
                arguments.append(argument)
        arguments.sort(key=lambda argus: argus.name)
        for count, argument in enumerate(arguments):
            newline = "\n"
            args = []
            if isinstance(arguments[count], commands.Group):
                for arg in arguments[count].commands:
                    args.append(arg.name)
                args.sort()
            embed.add_field(inline=False, name=f"""►`{arguments[count].name}` (Alias{"es" if
            len(arguments[count].aliases) > 1 else ""}: \
`{"`, `".join([str(alias) for alias in arguments[count].aliases])}`)""", value=f"""{arguments[count].help}\
{f'''{newline if len(arguments[count].commands) > 1 else ""}''' if isinstance(arguments[count], commands.Group) else
            ''''''}\
{f'''{f"►Argument{'s' if len(arguments[count].commands) > 1 else ''}"
f": `{'`, `'.join(args)}`"}''' if
            isinstance(arguments[count], commands.Group) else ''''''}""")
        embed.set_footer(icon_url=self.bot.user.display_avatar.url, text=self.bot.user.name)
        await ctx.send(embed=embed)

    @milestone.command(aliases=["chan"], brief="Sets the channel milestones are sent to.", help="""Sets the \
channel milestone updates are sent to. Supports #mentions and ID.""", name="channel",
                       usage="milestone channel <#channel>`/`<ID>")  # The usage is formatted oddly; when displayed,
    # the usage will show as `milestone channel <#channel>`/`<ID>`, where the / will not be in code formatting.
    # This is due to the way the help command displays information.
    @commands.guild_only()
    async def channel(self, ctx, channel: disnake.TextChannel = None):
        if channel is None:
            raise ChannelNotFound("None")  # Raises an in-built exception, which is then handled by the
        # on_command_error event in cog_events.
        with open("server_config.json", "r+") as server_config:
            data = json.load(server_config)
            previous = data["server_config"][str(ctx.guild.id)]["milestone_notify"]["channel"]
            update = {"channel": str(channel.id)}
            data["server_config"][str(ctx.guild.id)]["milestone_notify"].update(update)
            server_config.seek(0)
            json.dump(data, server_config, indent=4)
            server_config.truncate()
        await ctx.send(f"The milestone notification channel was updated from <#{previous}> to <#{channel.id}>.")

    @milestone.group(aliases=["admin", "admin_mention", "madmin"], brief="Sets whether or not admins are mentioned.",
                     case_insensitive=True, help="Sets whether or not admins are mentioned when a milestone is met.",
                     name="mention_admin", usage="milestone mention_admin <argument>")
    @commands.guild_only()
    async def mention_admin(self, ctx):
        if ctx.invoked_subcommand is not None:
            return
        await ctx.send("Please provide a state. Valid states: `off`, `on`.")

    @mention_admin.command(aliases=["disable"], brief="Sets the mention_admin state to off.", help="""Sets the bot \
to not mention admins when a milestone threshold is met.""", name="off", usage="milestone mention_admin off")
    @commands.guild_only()
    async def off___(self, ctx):
        with open("server_config.json", "r+") as server_config:
            data = json.load(server_config)
            if data["server_config"][str(ctx.guild.id)]["milestone_notify"]["mention_admin"] == "False":
                await ctx.send("Admins are already set to not be mentioned.")
                return
            elif data["server_config"][str(ctx.guild.id)]["milestone_notify"]["mention_admin"] == "True":
                update = {"mention_admin": "False"}
                data["server_config"][str(ctx.guild.id)]["milestone_notify"].update(update)
                server_config.seek(0)
                json.dump(data, server_config, indent=4)
                server_config.truncate()
        await ctx.send("The mention_admin state was set to False.")

    @mention_admin.command(aliases=["enable"], brief="Sets the mention_admin state to on.", help="""Sets the bot \
to mention admins when a milestone threshold is reached.""", name="on", usage="milestone mention_admin on")
    @commands.guild_only()
    async def on___(self, ctx):
        with open("server_config.json", "r+") as server_config:
            data = json.load(server_config)
            if data["server_config"][str(ctx.guild.id)]["milestone_notify"]["mention_admin"] == "True":
                await ctx.send("Admins are already set to be mentioned.")
                return
            elif data["server_config"][str(ctx.guild.id)]["milestone_notify"]["mention_admin"] == "False":
                update = {"mention_admin": "True"}
                data["server_config"][str(ctx.guild.id)]["milestone_notify"].update(update)
                server_config.seek(0)
                json.dump(data, server_config, indent=4)
                server_config.truncate()
        await ctx.send("The mention_admins state was set to True.")

    @milestone.group(aliases=["mstoner", "stoner", "stoner_mention"], brief="""Sets whether or not the person who met \
the milestone is mentioned.""", case_insensitive=True, help="""Sets whether or not the person who met the milestone is \
mentioned.""", name="mention_milestoner", usage="milestone mention_milestoner <argument>")
    # This is an odd name for this, but it fits, and is technically an English word. I think. The spell checker in my
    # IDE doesn't complain about it, at least.
    @commands.guild_only()
    async def mention_milestoner(self, ctx):
        if ctx.invoked_subcommand is not None:
            return
        await ctx.send("Please provide a state. Valid states: `off`, `on`.")

    @mention_milestoner.command(aliases=["disable"], brief="Sets the mention_milestoner state to off.", help="""Sets \
the bot to not mention the person who met the milestone when a milestone threshold is met.""", name="off",
                                usage="milestone mention_milestoner off")
    @commands.guild_only()
    async def off____(self, ctx):
        with open("server_config.json", "r+") as server_config:
            data = json.load(server_config)
            if data["server_config"][str(ctx.guild.id)]["milestone_notify"]["mention_milestoner"] == "False":
                await ctx.send("The person who met the milestone is already set to not be mentioned.")
                return
            elif data["server_config"][str(ctx.guild.id)]["milestone_notify"]["mention_milestoner"] == "True":
                update = {"mention_milestoner": "False"}
                data["server_config"][str(ctx.guild.id)]["milestone_notify"].update(update)
                server_config.seek(0)
                json.dump(data, server_config, indent=4)
                server_config.truncate()
        await ctx.send("The mention_milestoner state was set to False.")

    @mention_milestoner.command(aliases=["enable"], brief="Sets the mention_milestoner state to on.", help="""Sets \
the bot to mention the person who met the milestone when a milestone threshold is met.""", name="on",
                                usage="milestone mention_milestoner on")
    @commands.guild_only()
    async def on____(self, ctx):
        with open("server_config.json", "r+") as server_config:
            data = json.load(server_config)
            if data["server_config"][str(ctx.guild.id)]["milestone_notify"]["mention_milestoner"] == "True":
                await ctx.send("The person who met the milestone is already set to be mentioned.")
                return
            elif data["server_config"][str(ctx.guild.id)]["milestone_notify"]["mention_milestoner"] == "False":
                update = {"mention_milestoner": "True"}
                data["server_config"][str(ctx.guild.id)]["milestone_notify"].update(update)
                server_config.seek(0)
                json.dump(data, server_config, indent=4)
                server_config.truncate()
        await ctx.send("The mention_milestoner state was set to True.")

    @milestone.group(aliases=["s", "t", "toggle"], brief="Enable or disable milestones.", case_insensitive=True,
                     help="""Includes commands to toggle milestones on/off or change its state.""", name="state",
                     usage="milestone state (argument)")
    @commands.guild_only()
    async def state___(self, ctx):
        if ctx.invoked_subcommand is None:
            with open("server_config.json", "r+") as server_config:
                data = json.load(server_config)
                if data["server_config"][str(ctx.guild.id)]["milestone_notify"]["state"] == "True":
                    update = {"state": "False"}
                elif data["server_config"][str(ctx.guild.id)]["milestone_notify"]["state"] == "False":
                    update = {"state": "True"}
                state = data["server_config"][str(ctx.guild.id)]["milestone_notify"]["state"]
                data["server_config"][str(ctx.guild.id)]["milestone_notify"].update(update)
                server_config.seek(0)
                json.dump(data, server_config, indent=4)
                server_config.truncate()
            await ctx.send(f"""The milestones state was updated from {state} to \
{data["server_config"][str(ctx.guild.id)]["milestone_notify"]["state"]}.""")
        else:
            return

    @state___.command(aliases=["disable"], brief="Disables milestones.", help="Disables milestones.", name="off",
                      usage="milestone state off")
    @commands.guild_only()
    async def off_____(self, ctx):
        with open("server_config.json", "r+") as server_config:
            data = json.load(server_config)
            if data["server_config"][str(ctx.guild.id)]["milestone_notify"]["state"] == "True":
                update = {"state": "False"}
            elif data["server_config"][str(ctx.guild.id)]["milestone_notify"]["state"] == "False":
                await ctx.send("Milestones are already disabled.")
                return
            data["server_config"][str(ctx.guild.id)]["milestone_notify"].update(update)
            server_config.seek(0)
            json.dump(data, server_config, indent=4)
            server_config.truncate()
        await ctx.send("The milestones state was updated to False.")

    @state___.command(aliases=["enable"], brief="Enables milestones.", help="Enables milestones.", name="on",
                      usage="milestone state on")
    @commands.guild_only()
    async def on_____(self, ctx):
        with open("server_config.json", "r+") as server_config:
            data = json.load(server_config)
            if data["server_config"][str(ctx.guild.id)]["milestone_notify"]["state"] == "False":
                update = {"state": "True"}
            elif data["server_config"][str(ctx.guild.id)]["milestone_notify"]["state"] == "True":
                await ctx.send("Milestones are already enabled.")
                return
            data["server_config"][str(ctx.guild.id)]["milestone_notify"].update(update)
            server_config.seek(0)
            json.dump(data, server_config, indent=4)
            server_config.truncate()
        await ctx.send("The milestones state was updated to True.")

    @milestone.command(aliases=["amount"], brief="Sets milestone threshold.", help="""Sets the amount of Licensed \
Hunters that must be met for a milestone.""", name="threshold", usage="milestone threshold <threshold>")
    @commands.guild_only()
    async def threshold__(self, ctx, amount: int = None):
        if amount is None:
            await ctx.send("Please enter a valid number.")
            return
        with open("server_config.json", "r+") as server_config:
            data = json.load(server_config)
            update = {"threshold": str(amount)}
            data["server_config"][str(ctx.guild.id)]["milestone_notify"].update(update)
            server_config.seek(0)
            json.dump(data, server_config, indent=4)
            server_config.truncate()
        await ctx.send(f"The milestones threshold was set to `{amount}`.")
        # A lot of this whole cog was copy-pasting and refitting just basic JSON editing stuff.


def setup(bot):  # Defines the cog and adds it to the bot.
    bot.add_cog(Admin(bot))
