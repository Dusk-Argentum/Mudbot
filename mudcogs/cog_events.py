import asyncio  # Imports asyncio, used for sleeping/waiting.

from datetime import datetime, timedelta, timezone  # Imports datetime, useful for logging and doing math with times.

import disnake
from disnake import HTTPException
from disnake.ext import commands
from disnake.ext.commands import BotMissingPermissions, ChannelNotFound, CheckFailure, CommandInvokeError, \
    CommandNotFound, MemberNotFound, MissingAnyRole, NoPrivateMessage, NotOwner, UnexpectedQuoteError, UserNotFound
# Imports a bunch of exceptions.


import json

from mudbot import GUILD, PREFIX  # Imports the GUILD and PREFIX global variables from the main bot file.
from mudcogs import cog_tasks  # Imports the cog_tasks file.

import re


class MudEvents(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()  # Defines a listener, which listens for a specific event and executes code when detected.
    async def on_command_error(self, ctx, error):  # Functions in this block execute when a command errors.
        if ctx.author.id == self.bot.owner_id:  # Functions in this block execute if the command invoker is the bot's
            # owner.
            await ctx.send(error)  # Sends the unedited error text to the channel.
        raw_error = error
        if isinstance(error, BotMissingPermissions):  # Functions in this block execute if the bot is missing the
            # permissions required to execute a function.
            error = "I do not have permission to enact this command."
        if isinstance(error, ChannelNotFound):  # Functions in this block execute if the bot tries to grab a channel
            # that is invalid.
            error = """Channel not found. Please make sure to #mention the channel, or use its Discord ID.
Example: <#628080650427039764> | `628080650427039764`"""
        if isinstance(error, CheckFailure):  # Functions in this block execute if a check (which prevents a command
            # from progressing if certain prerequisites are not met) fails.
            if ctx.command.name in ["minions"]:  # Functions in this block execute if the command invoked is gated to
                # specific channels. Currently, only minions does this.
                with open("server_config.json", "r") as server_config:
                    data = json.load(server_config)
                channels = []
                for count, unused in enumerate(data["server_config"][str(ctx.guild.id)]["allowed_channels"]
                                               [ctx.command.name], start=1):
                    channels.append(data["server_config"][str(ctx.guild.id)]["allowed_channels"][ctx.command.name]
                                    [str(count)])
                    # Makes a list of channels where the command can be used.
                error = f"""The command `{ctx.command.name}` cannot be used here.
Valid channels: <#{">, <#".join(channels)}>."""
            elif ctx.command.name in ["conductor", "spawner"] and "rolerequest" not in ctx.channel.name:
                error = "This command must be used in a role request ticket."
        if isinstance(error, CommandInvokeError):  # Functions in this block execute if there is an unhandled
            # exception which causes the command to execute improperly.
            error = f"Incorrect invocation. Please re-examine the command in `{PREFIX}help`."
        if isinstance(error, CommandNotFound):  # Functions in this block execute if the invoker tries to run
            # a command that does not exist.
            error = f"Command not found. Please view `{PREFIX}help` for valid commands."
        if isinstance(error, MemberNotFound):  # Functions in this block execute if the provided member is invalid.
            error = """Member not found. Please make sure to @mention the member, or use their Discord ID.
Example: <@97153790897045504> | `97153790897045504`"""
        if isinstance(error, MissingAnyRole):  # Functions in this block execute if the invoker is missing
            # a certain role.
            error = "You do not have permission to run this command."
        if isinstance(error, NoPrivateMessage):  # Functions in this block execute if the invoker tries to invoke
            # a command in a private message.
            error = "You cannot run this command in a private message."
        if isinstance(error, NotOwner):  # Functions in this block execute if the invoker is cringe.
            error = "You're not cool enough to run this command."
        if isinstance(error, UnexpectedQuoteError):
            if ctx.command.name == "link":
                await ctx.send(f"""You have an invalid quote. Please **copy and paste** the below text to verify.
`{ctx.message.content.replace("‘", "'")}`""")
                return
            error = "Unexpected quote. Please use `'` instead of `‘`."
        if isinstance(error, UserNotFound):  # Functions in this block execute if the provided user is invalid.
            error = """User not found. Please make sure to @mention the user, or use their Discord ID.
Example: <@97153790897045504> | `97153790897045504`"""
        channel = self.bot.get_channel(917980973306638346)  # Grabs the error reporting channel for Mudbot on
        # my private server.
        embed = disnake.Embed(color=disnake.Color(0x3b9da5), description="An exception was caught.", title="Error!")
        # Functions below define the various aspects of an embed and their content.
        embed.set_author(icon_url=self.bot.user.avatar.url, name=self.bot.user.name)
        embed.set_thumbnail(url=self.bot.user.avatar.url)
        timestamp = int((datetime.strptime(str(datetime.now(timezone.utc).replace(microsecond=0, tzinfo=None)),
                                           "%Y-%m-%d %H:%M:%S") -
                         datetime.strptime("1970-01-01", "%Y-%m-%d")).total_seconds())
        value = f"""A command {f"(`{PREFIX}{ctx.command.name}`)" if ctx.command is not None else ""} invoked by \
{ctx.author.mention} (`{ctx.author.id}`) on <t:{timestamp}:F> in {f"{ctx.channel.mention} (`{ctx.channel.id}`)" if
        ctx.channel.type == disnake.ChannelType.text else f"a DM with {ctx.author.mention} (`{ctx.author.id}`)"} \
caused the error detailed below."""
        embed.add_field(inline=False, name="Source:", value=value)
        embed.add_field(inline=False, name="Raw Error:", value=str(raw_error))
        embed.add_field(inline=False, name="Message Sent:", value=error)
        embed.add_field(inline=False, name="Message Content:", value=f"`{ctx.message.content}`")
        embed.set_footer(icon_url=self.bot.user.avatar.url, text=self.bot.user.name)
        await channel.send(embed=embed)
        await ctx.send(f"Error: {error}")  # Sends the error text.

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):  # Functions in this block execute if a ban is heard.
        if guild.id != GUILD:  # Functions in this block execute if the guild that the event took place in is not
            # the guild that the bot should be listening to.
            return  # Essentially, just stops processing if the guild isn't AH.
        auto_ban = None  # Defines a None variable to be edited later.
        channel = None  # Defines a None variable to be edited later.
        entry = None  # Guess what?
        await asyncio.sleep(1)  # Waits one second to ensure that the audit log entry exists. Slash commands executed
        # from other bots have this weird delay. idk. Don't use slash commands.
        async for entry in guild.audit_logs(action=disnake.AuditLogAction.ban):  # Loops for every entry in the guild's
            # audit logs that is a ban.
            if entry.target.id == user.id and entry.reason is not None and "Your account is too new" in entry.reason \
                    and entry.user.id == self.bot.user.id:  # Functions in this block execute if the user was banned
                # for being too new.
                channel = disnake.utils.get(guild.channels, name="auto-actioned-log")  # Gets the appropriate channel.
                auto_ban = 1
                break
            elif entry.target.id == user.id:  # Functions in this block execute if the audit log entry obtained is the
                # one that pertains to the user. Otherwise, grabs the most recent one, and we don't want that.
                channel = disnake.utils.get(guild.channels, name="actioned-log")
                auto_ban = 0
                break
            else:
                continue
        embed = disnake.Embed(color=disnake.Color(0xf02a07),
                              title=f"Member{' automatically ' if auto_ban == 1 else ' '}banned.")
        try:
            embed.set_author(icon_url=entry.user.avatar.url, name=entry.user.name)
        except AttributeError:
            embed.set_author(name=entry.user.name)
        try:
            embed.set_thumbnail(url=entry.target.avatar.url)
        except AttributeError:
            pass
        embed.add_field(name="Responsible Nutty Moderator:", value=f"""{entry.user.mention}
{entry.user}
(`{entry.user.id}`)""")
        embed.add_field(name="Action Taken On:", value=f"""{entry.target.mention}
{entry.target}
(`{entry.target.id}`)""")
        timestamp = int((datetime.strptime(str(entry.created_at.replace(microsecond=0, tzinfo=None)),
                                           "%Y-%m-%d %H:%M:%S") -
                         datetime.strptime("1970-01-01", "%Y-%m-%d")).total_seconds())
        embed.add_field(inline=False, name="Time of Action:", value=f"<t:{str(timestamp)}> (<t:{str(timestamp)}:R>)")
        embed.add_field(inline=False, name="Reason:",
                        value=entry.reason if entry.reason is not None else "No reason specified.")
        embed.set_footer(icon_url=guild.icon.url, text=guild.name)
        await channel.send(embed=embed)

    @commands.Cog.listener()  # If this doesn't work again, just make it temporary ban for threshold time.
    async def on_member_join(self, member):
        guild = member.guild
        if guild.id != GUILD:
            return
        with open("server_config.json", "r") as server_config:
            data = json.load(server_config)
        state = data["server_config"][str(guild.id)]["auto_punish"]["ban"]["state"]
        threshold = data["server_config"][str(guild.id)]["auto_punish"]["ban"]["threshold"]
        if state == "False":
            return
        threshold = re.search(r"(^\d{1,2})(m$|h$|d$)", threshold)
        if threshold.group(2).lower() == "m":
            threshold = int(threshold.group(1)) * 60
        elif threshold.group(2).lower() == "h":
            threshold = int(threshold.group(1)) * 3600
        elif threshold.group(2).lower() == "d":
            threshold = int(threshold.group(1)) * 86400
        age = int(str((datetime.strptime(str((datetime.now(timezone.utc)).replace(microsecond=0, tzinfo=None)),
                                         "%Y-%m-%d %H:%M:%S") -
                       datetime.strptime(str(member.created_at.replace(microsecond=0, tzinfo=None)),
                                         "%Y-%m-%d %H:%M:%S")).total_seconds()).split(".")[0])
        if age < threshold:
            async for entry in guild.audit_logs(action=disnake.AuditLogAction.unban):
                if entry.target.id == member.id:
                    return
                else:
                    continue
            embed = disnake.Embed(color=disnake.Color(0xf02a07), description="""Your account is too new to join this \
Discord. Please visit [our ban appeal page](https://unban.aetherhunts.net/) to appeal.
Unban appeals for new accounts will be accepted once a moderator is able to view your appeal.""",
                                  title="Sorry, you're too new!")
            embed.set_author(icon_url=self.bot.user.avatar.url, name=self.bot.user.name)
            embed.set_thumbnail(url=guild.banner.url)
            embed.set_footer(icon_url=guild.icon.url, text=guild.name)
            try:
                await member.send(embed=embed)
            except HTTPException:
                pass
            await member.guild.ban(member, reason=f"""Your account is too new to join this Discord! Please visit \
[our ban appeal page](https://unban.aetherhunts.net/) to appeal.""")

    @commands.Cog.listener()
    async def on_member_remove(self, member):  # Functions in this block execute when a member leaves.
        # What I wouldn't give for an on_member_kick listener so I didn't have to filter out normal leaves.
        guild = member.guild
        if guild.id != GUILD:
            return
        auto_kick = None
        channel = None
        entry = None
        await asyncio.sleep(1)
        time_filter = datetime.strptime(str(datetime.now(timezone.utc).replace(microsecond=0, tzinfo=None) -
                                            timedelta(seconds=5)), "%Y-%m-%d %H:%M:%S")
        async for entry in guild.audit_logs(action=disnake.AuditLogAction.kick):
            created_at = datetime.strptime(str(entry.created_at.replace(microsecond=0, tzinfo=None)),
                                           "%Y-%m-%d %H:%M:%S")
            if entry.target.id == member.id and entry.reason is not None \
                    and "for failing to verify your character" in entry.reason and entry.user.id == self.bot.user.id \
                    and created_at > time_filter:  # Functions in this block execute if the user was auto-kicked
                # for failing to verify within the threshold.
                channel = disnake.utils.get(guild.channels, name="auto-actioned-log")
                auto_kick = 1
                break
            elif entry.target.id == member.id and created_at > time_filter:
                channel = disnake.utils.get(guild.channels, name="actioned-log")
                auto_kick = 0
                break
            elif created_at < time_filter:
                return
            else:
                continue
        else:
            return
        embed = disnake.Embed(color=disnake.Color(0xf59a38),
                              title=f"Member{' automatically ' if auto_kick == 1 else ' '}kicked.")
        try:
            embed.set_author(icon_url=entry.user.avatar.url, name=entry.user.name)
        except AttributeError:
            embed.set_author(name=entry.user.name)
        try:
            embed.set_thumbnail(url=entry.target.avatar.url)
        except AttributeError:
            pass
        embed.add_field(name="Responsible Nutty Moderator:", value=f"""{entry.user.mention}
{entry.user}
(`{entry.user.id}`)""")
        embed.add_field(name="Action Taken On:", value=f"""{entry.target.mention}
{entry.target}
(`{entry.target.id}`)""")
        timestamp = int((datetime.strptime(str(entry.created_at.replace(microsecond=0, tzinfo=None)),
                                           "%Y-%m-%d %H:%M:%S") -
                         datetime.strptime("1970-01-01", "%Y-%m-%d")).total_seconds())
        embed.add_field(inline=False, name="Time of Action:", value=f"<t:{str(timestamp)}> (<t:{str(timestamp)}:R>)")
        embed.add_field(inline=False, name="Reason:",
                        value=entry.reason if entry.reason is not None else "No reason specified.")
        embed.set_footer(icon_url=guild.icon.url, text=guild.name)
        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_unban(self, guild, user):  # Functions in this block execute when the bot hears an unban.
        if guild.id != GUILD:
            return
        channel = None
        entry = None
        await asyncio.sleep(1)
        async for entry in guild.audit_logs(action=disnake.AuditLogAction.unban):
            if entry.target.id == user.id and entry.reason is not None and "Removed temporary ban" in entry.reason:
                channel = disnake.utils.get(guild.channels, name="auto-actioned-log")
                break
            elif entry.target.id == user.id:
                channel = disnake.utils.get(guild.channels, name="actioned-log")
                break
            else:
                continue
        embed = disnake.Embed(color=disnake.Color(0xebaba0), title="User unbanned.")
        try:
            embed.set_author(icon_url=entry.user.avatar.url, name=entry.user.name)
        except AttributeError:
            embed.set_author(name=entry.user.name)
        try:
            embed.set_thumbnail(url=entry.target.avatar.url)
        except AttributeError:
            pass
        embed.add_field(name="Responsible Nutty Moderator:", value=f"""{entry.user.mention}
{entry.user}
(`{entry.user.id}`)""")
        embed.add_field(name="Action Taken On:", value=f"""{entry.target.mention}
{entry.target}
(`{entry.target.id}`)""")
        timestamp = int((datetime.strptime(str(entry.created_at.replace(microsecond=0, tzinfo=None)),
                                           "%Y-%m-%d %H:%M:%S") -
                         datetime.strptime("1970-01-01", "%Y-%m-%d")).total_seconds())
        embed.add_field(inline=False, name="Time of Action:", value=f"<t:{str(timestamp)}> (<t:{str(timestamp)}:R>)")
        embed.add_field(inline=False, name="Reason:",
                        value=entry.reason if entry.reason is not None else "No reason specified.")
        embed.set_footer(icon_url=guild.icon.url, text=guild.name)
        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_update(self, before, after):  # Functions in this block execute when the bot hears a member
        # update. Requires Members privileged intent.
        guild = before.guild
        if guild.id != GUILD:
            return
        muted = disnake.utils.get(guild.roles, name="Muted")
        if muted not in before.roles and muted not in after.roles:
            return
        elif muted in before.roles and muted in after.roles:
            return
        entry = None
        state = None
        await asyncio.sleep(1)
        async for entry in guild.audit_logs(action=disnake.AuditLogAction.member_role_update):
            if entry.target.id == before.id and entry.target.id == after.id:
                if muted in before.roles and muted not in after.roles:
                    state = 0
                    if entry.reason is not None and "Removed temporary mute" in entry.reason:
                        state = 2
                    break
                elif muted not in before.roles and muted in after.roles:
                    state = 1
                    break
            else:
                continue
        title = ""
        channel = disnake.utils.get(guild.channels, name="actioned-log")
        if state == 0:
            title = "Member unmuted."
        elif state == 1:
            title = "Member muted."
        elif state == 2:
            channel = disnake.utils.get(guild.channels, name="auto-actioned-log")
            title = "Member unmuted."
        embed = disnake.Embed(color=disnake.Color(0x69727a), title=title)
        try:
            embed.set_author(icon_url=entry.user.avatar.url, name=entry.user.name)
        except AttributeError:
            embed.set_author(name=entry.user.name)
        try:
            embed.set_thumbnail(url=entry.target.avatar.url)
        except AttributeError:
            pass
        embed.add_field(name="Responsible Nutty Moderator:", value=f"""{entry.user.mention}
{entry.user}
(`{entry.user.id}`)""")
        embed.add_field(name="Action Taken On:", value=f"""{entry.target.mention}
{entry.target}
(`{entry.target.id}`)""")
        timestamp = int((datetime.strptime(str(entry.created_at.replace(microsecond=0, tzinfo=None)),
                                           "%Y-%m-%d %H:%M:%S") -
                         datetime.strptime("1970-01-01", "%Y-%m-%d")).total_seconds())
        embed.add_field(inline=False, name="Time of Action:", value=f"<t:{str(timestamp)}> (<t:{str(timestamp)}:R>)")
        embed.add_field(inline=False, name="Reason:",
                        value=entry.reason if entry.reason is not None else "No reason specified.")
        embed.set_footer(icon_url=guild.icon.url, text=guild.name)  # If auto then that channel else actioned
        await channel.send(embed=embed)

    @commands.Cog.listener("on_member_update")
    async def on_member_verify_milestone(self, before, after):  # Functions in this block execute if the
        # on_member_update listener hears an update that involves the Licensed Hunter role.
        guild = before.guild
        if guild.id != GUILD:
            return
        with open("server_config.json", "r") as server_config:
            data = json.load(server_config)
        if data["server_config"][str(guild.id)]["milestone_notify"]["state"] == "False":
            return
        hunter = disnake.utils.get(guild.roles, name="Licensed Hunter")
        if hunter in before.roles and hunter in after.roles:
            return
        if len(hunter.members) == int(data["server_config"][str(guild.id)]["milestone_notify"]["threshold"]) \
                and hunter not in before.roles and hunter in after.roles:
            admin = disnake.utils.get(guild.roles, name="Admin")
            channel = disnake.utils.get(guild.channels, id=int(data["server_config"][str(guild.id)]["milestone_notify"]
                                                               ["channel"]))
            mention_admin = data["server_config"][str(guild.id)]["milestone_notify"]["mention_admin"]
            mention_milestoner = data["server_config"][str(guild.id)]["milestone_notify"]["mention_milestoner"]
            threshold = data["server_config"][str(guild.id)]["milestone_notify"]["threshold"]
            try:
                await channel.send(f"""{f"{admin.mention}, " if mention_admin == "True" else ""}\
{f"{before.mention}" if mention_milestoner == "True" else f"{before.user}"} is our {threshold}\
{"st" if threshold.endswith("1") else ""}{"nd" if threshold.endswith("2") else ""}\
{"rd" if threshold.endswith("3") else ""}\
{"th" if threshold.endswith(("0", "4", "5", "6", "7", "8", "9")) else ""} Licensed Hunter!""")
            except BotMissingPermissions:
                channel = disnake.utils.get(guild.channels, id=740603224826052608)
                await channel.send("Could not send milestone update.")
            data["server_config"][str(guild.id)]["milestone_notify"]["state"] = "False"
            with open("server_config.json", "w") as server_config:
                server_config.seek(0)
                json.dump(data, server_config, indent=4)
                server_config.truncate()

    @commands.Cog.listener("on_member_update")
    async def on_member_verify_viewer(self, before, after):  # Basically the same as above, but adds Licensed Viewer.
        guild = before.guild
        if guild.id != GUILD:
            return
        hunter = disnake.utils.get(guild.roles, name="Licensed Hunter")
        if hunter in before.roles and hunter in after.roles:
            return
        if hunter not in before.roles and hunter in after.roles:
            viewer = disnake.utils.get(guild.roles, name="Licensed Viewer")
            await after.add_roles(viewer)
            with open("licensed_viewers.json", "r+") as licensed_viewers:
                data = json.load(licensed_viewers)
                new_entry = {
                    str(before.id): {
                        "time": str(datetime.now(timezone.utc)).split(".")[0]
                    }
                }
                data["licensed_viewers"].update(new_entry)
                licensed_viewers.seek(0)
                json.dump(data, licensed_viewers, indent=4)
                licensed_viewers.truncate()

    @commands.Cog.listener()
    async def on_ready(self):  # Functions in this block execute when the bot is finished starting up.
        await asyncio.sleep(1)
        try:
            cog_tasks.MudTasks.auto_kick_unverified.start(self)  # Executes the auto-kick task.
        except RuntimeError:
            pass
        try:
            cog_tasks.MudTasks.check_temp_bans.start(self)  # Executes the task that checks whether or not temp-bans are
            # in the past.
        except RuntimeError:
            pass
        try:
            cog_tasks.MudTasks.check_temp_mutes.start(self)  # Same as above, but for mutes.
        except RuntimeError:
            pass
        try:
            cog_tasks.MudTasks.status_rotation.start(self)  # Executes the status rotation task.
        except RuntimeError:
            pass
        try:
            cog_tasks.MudTasks.viewer_removal.start(self)  # Executes the viewer removal task.
        except RuntimeError:
            pass
        print(f"{self.bot.user.name} online. Awaiting commands.")  # Let's the person viewing the console know
        # that the bot started up successfully.


def setup(bot):
    bot.add_cog(MudEvents(bot))
