import asyncio


import disnake
from disnake.ext import commands


import json


from mudbot import PREFIX


import os


import random  # Imports the random module for use in generating random numbers.


class Owner(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        return ctx.author.id == self.bot.owner_id

    @commands.command(aliases=["de"], brief="Echoes message.", help="Echoes message, deleting invocation.",
                      name="delete_echo", usage="delete_echo <message>")
    async def delete_echo(self, ctx, *args):
        await ctx.message.delete()
        await ctx.send(" ".join(args))

    @commands.command(aliases=["inv"], brief="Sends invite link.", help="Sends invite link.", name="invite",
                      usage="invite")
    async def invite(self, ctx):
        await ctx.send(str(os.environ.get("Mudbot_Invite")))

    @commands.command(aliases=["bye"], brief="Leaves the provided server.", help="""Leaves the provided server. \
Leaves the current server if none is provided. Accept only IDs.""", usage="leave (server_id)")
    async def leave(self, ctx, server: int = None):
        if server is None:
            server = self.bot.get_guild(ctx.guild.id)
        elif server is not None:
            server = self.bot.get_guild(server)
        await server.leave()

    @commands.command(aliases=["server_list"], brief="Lists servers the bot is on.",
                      help="Lists servers the bot is on.", name="list", usage="list")
    async def list(self, ctx):
        servers = []
        for server in self.bot.guilds:
            servers.append(f"{server.name} (`{server.id}`)\n")
            await asyncio.sleep(1)
        await ctx.author.send(servers)

    @commands.group(aliases=["stat"], brief="Commands for adjusting bot status.", case_insensitive=True,
                    help="""Commands for adjusting the bot's status, including toggling auto-rotation on/off \
and custom statuses.""", name="status", usage="status [subcommand] <argument>")
    async def status(self, ctx):
        if ctx.invoked_subcommand is not None:
            return
        embed = disnake.Embed(color=disnake.Color(0x3b9da5), description=ctx.command.help, title=f"{ctx.command.name}")
        embed.set_author(icon_url=self.bot.user.avatar.url, name=self.bot.user.name)
        embed.set_thumbnail(url=self.bot.user.avatar.url)
        arguments = []
        for argument in ctx.command.walk_commands():
            if argument.parent.name == "status":
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
        embed.set_footer(icon_url=self.bot.user.avatar.url, text=self.bot.user.name)
        await ctx.send(embed=embed)

    @status.command(aliases=["c", "s"], brief="Changes bot's status.", help="""Changes the bot's status to the given \
status.""", name="change", usage="status change (status)")
    async def change(self, ctx, *args):
        with open("bot_config.json", "r") as bot_config:
            data = json.load(bot_config)
        if len(args) == 0:  # Functions in this block execute if the arguments do not exist.
            status = (data["bot_config"]["status"]["statuses"]
                      [str(random.randint(1, len(data["bot_config"]["status"]["statuses"])))])
            await self.bot.change_presence(activity=disnake.Game(f"""{status} | {PREFIX}help"""))
            update = {"state": "True"}
            data["bot_config"]["status"].update(update)
            with open("bot_config.json", "w") as bot_config:
                bot_config.seek(0)
                json.dump(data, bot_config, indent=4)
                bot_config.truncate()
        elif len(args) > 0:  # Functions in this block execute if the arguments exist.
            update = {"state": "False"}
            data["bot_config"]["status"].update(update)
            with open("bot_config.json", "w") as bot_config:
                bot_config.seek(0)
                json.dump(data, bot_config, indent=4)
                bot_config.truncate()
            await self.bot.change_presence(status=disnake.Status.online, activity=disnake.Game(f" ".join(args)
                                                                                               + f" | {PREFIX}help"))

    @status.group(aliases=["st", "toggle"], brief="Enable or disable status rotation.", case_insensitive=True,
                  help="""Includes commands to toggle status rotation on/off or change its state.""", name="state",
                  usage="status state (argument)")
    async def state(self, ctx):
        if ctx.invoked_subcommand is None:
            with open("bot_config.json", "r+") as bot_config:
                data = json.load(bot_config)
                if data["bot_config"]["status"]["state"] == "True":
                    update = {"state": "False"}
                elif data["bot_config"]["status"]["state"] == "False":
                    update = {"state": "True"}
                state = data["bot_config"]["status"]["state"]
                data["bot_config"]["status"].update(update)
                bot_config.seek(0)
                json.dump(data, bot_config, indent=4)
                bot_config.truncate()
            await ctx.send(f"""Status rotation state was updated from {state} to \
{str(data["bot_config"]["status"]["state"])}.""")
        else:
            return

    @state.command(aliases=["disable"], brief="Disables status rotation.", help="""Disables status rotation.""",
                   name="off", usage="status state off")
    async def off(self, ctx):
        with open("bot_config.json", "r+") as bot_config:
            data = json.load(bot_config)
            if data["bot_config"]["status"]["state"] == "False":
                await ctx.send("Status already set to not rotate.")
                return
            elif data["bot_config"]["status"]["state"] == "True":
                update = {"state": "False"}
                data["bot_config"]["status"].update(update)
                bot_config.seek(0)
                json.dump(data, bot_config, indent=4)
                bot_config.truncate()
        await ctx.send("Status rotation is now off.")

    @state.command(aliases=["enable"], brief="Enables status rotation.", help="""Enables status rotation.""",
                   name="on", usage="status state on")
    async def on(self, ctx):
        with open("bot_config.json", "r+") as bot_config:
            data = json.load(bot_config)
            if data["bot_config"]["status"]["state"] == "True":
                await ctx.send("Status already set to rotate.")
                return
            elif data["bot_config"]["status"]["state"] == "False":
                update = {"state": "True"}
                data["bot_config"]["status"].update(update)
                bot_config.seek(0)
                json.dump(data, bot_config, indent=4)
                bot_config.truncate()
        await ctx.send("Status rotation is now on.")


def setup(bot):
    bot.add_cog(Owner(bot))
