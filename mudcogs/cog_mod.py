import json
from datetime import datetime, timedelta, timezone


import disnake
from disnake import Forbidden, HTTPException, NotFound
from disnake.ext import commands
from disnake.ext.commands import BotMissingPermissions, MemberNotFound, MissingAnyRole, UserNotFound


import re


from typing import Union  # Imports the Union submodule from typing for use in argument unity.


class Mod(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        mod = disnake.utils.get(ctx.guild.roles, name="Nutty Moderator")
        if mod not in ctx.author.roles:
            raise MissingAnyRole([1])
        return mod in ctx.author.roles

    @commands.command(aliases=["b", "b&"], brief="Bans a member.", help="""Bans a member from the server. Accepts \
@mention and ID.""", name="ban", usage="ban <@mention>`/`<ID> <reason>")
    @commands.guild_only()
    async def ban(self, ctx, user: Union[disnake.Member, disnake.User] = None, *, reason: str = None):
        # The Union type checks if the user provided is a member or a user, in that order. Users not on the server
        # are known as users, while users on the server are known as members.
        if user is None:
            raise UserNotFound("user")
        bans = await ctx.guild.bans()  # Gets the list of all bans in the server.
        for ban in bans:  # Functions in this block check to see if the target is already banned.
            if user.id == ban.user.id:
                await ctx.send("That user is already banned.")
                return
            else:
                continue
        if reason is None:  # Bans require a reason due to the intensity of the punishment.
            await ctx.send("Please specify a reason for the ban.")
            return
        moderator = disnake.utils.get(ctx.guild.roles, name="Nutty Moderator")
        admin = disnake.utils.get(ctx.guild.roles, name="Admin")
        if isinstance(user, disnake.Member) and (moderator in user.roles and admin not in ctx.author.roles):
            # Functions in this block execute if the target is a mod and the invoker is not an admin.
            await ctx.send(f"You cannot punish a fellow {moderator.name}.")
            # You technically still can't ban fellow moderators with this even if you have the proper permissions.
            # Because Discord?
            # Maybe I'll try and find a workaround for this, but really low priority. I mean, how often do you need
            # to ban moderators anyway? :)
            return
        try:
            await ctx.guild.ban(user, delete_message_days=1, reason=f"{ctx.author.id}: {reason}")
        except Forbidden:
            raise BotMissingPermissions(missing_permissions=["ban"])
        except HTTPException:
            await ctx.send("Due to a Discord limitation, please keep your reason below 490 characters.")
            return
        await ctx.message.add_reaction("👍")

    @commands.command(aliases=["k"], brief="Kicks a member.", help="""Kicks a member from the server. Accepts \
@mention and ID.""", name="kick", usage="kick <mention>`/`<ID> (reason)")
    @commands.guild_only()
    async def kick(self, ctx, member: disnake.Member = None, *, reason: str = "Unspecified reason."):
        if member is None:
            raise MemberNotFound("member")
        moderator = disnake.utils.get(ctx.guild.roles, name="Nutty Moderator")
        admin = disnake.utils.get(ctx.guild.roles, name="Admin")
        if moderator in member.roles and admin not in ctx.author.roles:
            await ctx.send(f"You cannot punish a fellow {moderator.name}.")
            return
        try:
            await ctx.guild.kick(member, reason=f"{ctx.author.id}: {reason}")
        except Forbidden:
            raise BotMissingPermissions(missing_permissions=["kick"])
        except HTTPException:
            await ctx.send("Due to a Discord limitation, please keep your reason below 490 characters.")
            return
        await ctx.message.add_reaction("👍")

    @commands.command(aliases=["mu", "stfu"], brief="Mutes a member.", help="""Adds the Muted role to a member. \
Accepts @mention and ID.""", name="mute", usage="mute <@mention>`/`<ID> (reason)")
    @commands.guild_only()
    async def mute(self, ctx, member: disnake.Member = None, *, reason: str = "Unspecified reason."):
        if member is None:
            raise MemberNotFound("member")
        moderator = disnake.utils.get(ctx.guild.roles, name="Nutty Moderator")
        admin = disnake.utils.get(ctx.guild.roles, name="Admin")
        if moderator in member.roles and admin not in ctx.author.roles:
            await ctx.send(f"You cannot punish a fellow {moderator.name}.")
            return
        muted = disnake.utils.get(ctx.guild.roles, name="Muted")
        if muted in member.roles:
            await ctx.send("That member is already muted.")
            return
        try:
            await member.add_roles(muted, reason=f"{ctx.author.id}: {reason}")
        except Forbidden:
            raise BotMissingPermissions(missing_permissions=["manage_roles"])
        except HTTPException:
            await ctx.send("Due to a Discord limitation, please keep your reason below 490 characters.")
            return
        await ctx.message.add_reaction("👍")

    @commands.command(aliases=["tb", "tempban"], brief="Temporarily bans a member.", help="""Temporarily bans a member \
for the specified duration. Supports @mention and ID.""", name="temp_ban", usage="""temp_ban <@mention>`/`<ID> \
<duration>` (e.g. "1h") `<reason>""")
    @commands.guild_only()
    async def temp_ban(self, ctx, user: Union[disnake.Member, disnake.User], duration: str = "1h", *,
                       reason: str = None):
        if user is None:
            raise UserNotFound("user")
        bans = await ctx.guild.bans()
        for ban in bans:
            if user.id == ban.user.id:
                await ctx.send("That user is already banned.")
                return
            else:
                continue
        if reason is None:
            await ctx.send("Please specify a reason for the temp-ban.")
            return
        moderator = disnake.utils.get(ctx.guild.roles, name="Nutty Moderator")
        admin = disnake.utils.get(ctx.guild.roles, name="Admin")
        if isinstance(user, disnake.Member) and (moderator in user.roles and admin not in ctx.author.roles):
            await ctx.send(f"You cannot punish a fellow {moderator.name}.")
            return
        duration = re.search(r"(^\d{1,2})(m$|h$|d$)", duration, re.IGNORECASE)
        if duration is None:
            await ctx.send("""Please use a valid duration in the format of (up to 2 digits)(**m**inutes/**h**ours/\
**d**ays), eg. "1h", "69d", "42m".""")
            return
        if reason is None:
            await ctx.send("Please specify a reason for the temp. ban.")
            return
        if duration.group(2).lower() == "m":  # Functions in the following blocks do math to get the proper amount
            # of seconds.
            duration = int(duration.group(1)) * 60
        elif duration.group(2).lower() == "h":
            duration = int(duration.group(1)) * 3600
        elif duration.group(2).lower() == "d":
            duration = int(duration.group(1)) * 86400
        timestamp = int(((datetime.strptime(str(datetime.now(timezone.utc)).split(".")[0], "%Y-%m-%d %H:%M:%S") +
                          timedelta(seconds=duration)) - datetime.strptime("1970-01-01 00:00:00", "%Y-%m-%d %H:%M:%S"))
                        .total_seconds())
        # The above long, unwieldy statement gets the amount of seconds that have passed since epoch for use in
        # Discord's timestamp mentions.
        try:
            await ctx.guild.ban(user, reason=f"{ctx.author.id}: {reason} (Until <t:{timestamp}>)")
        except Forbidden:
            raise BotMissingPermissions(missing_permissions=["ban"])
        except HTTPException:
            await ctx.send("Due to a Discord limitation, please keep your reason below 475 characters.")
            return
        expiration = datetime.strptime(str(datetime.now(timezone.utc) + timedelta(seconds=duration)).partition(".")[0],
                                       "%Y-%m-%d %H:%M:%S")
        entry = {
            user.id: {
                "expiration": str(expiration)
            }
        }
        with open("temporary_punishments.json", "r+") as temp_punish:
            data = json.load(temp_punish)
            data["temporary_punishments"]["bans"].update(entry)
            temp_punish.seek(0)
            json.dump(data, temp_punish, indent=4)
        await ctx.message.add_reaction("👍")

    @commands.command(aliases=["tm", "tempmute", "tempstfu", "temp_stfu"], brief="Temporarily mutes a member.",
                      help="""Temporarily mutes a member for the specified duration. Supports @mention and ID.""",
                      name="temp_mute", usage="""temp_mute <@mention>`/`<ID> <duration>` (e.g. "1h") `(reason)""")
    @commands.guild_only()
    async def temp_mute(self, ctx, member: disnake.Member, duration: str = "1h",
                        reason: str = "Unspecified reason."):
        if member is None:
            raise MemberNotFound("member")
        moderator = disnake.utils.get(ctx.guild.roles, name="Nutty Moderator")
        admin = disnake.utils.get(ctx.guild.roles, name="Admin")
        if isinstance(member, disnake.Member) and (moderator in member.roles and admin not in ctx.author.roles):
            await ctx.send(f"You cannot punish a fellow {moderator.name}.")
            return
        muted = disnake.utils.get(ctx.guild.roles, name="Muted")
        if muted in member.roles:
            await ctx.send("That member is already muted.")
            return
        duration = re.search(r"(^\d{1,2})(m$|h$|d$)", duration, re.IGNORECASE)
        if duration is None:
            await ctx.send("""Please use a valid duration in the format of (up to 2 digits)(**m**inutes/**h**ours/\
**d**ays), eg. "1h", "69d", "42m".""")
            return
        if duration.group(2).lower() == "m":
            duration = int(duration.group(1)) * 60
        elif duration.group(2).lower() == "h":
            duration = int(duration.group(1)) * 3600
        elif duration.group(2).lower() == "d":
            duration = int(duration.group(1)) * 86400
        timestamp = int(((datetime.strptime(str(datetime.now(timezone.utc)).split(".")[0], "%Y-%m-%d %H:%M:%S") +
                         timedelta(seconds=duration)) - datetime.strptime("1970-01-01 00:00:00", "%Y-%m-%d %H:%M:%S"))
                        .total_seconds())
        try:
            await member.add_roles(muted, reason=f"{ctx.author.id}: {reason} (Until <t:{timestamp}>)")
        except Forbidden:
            raise BotMissingPermissions(missing_permissions=["manage_roles"])
        except HTTPException:
            await ctx.send("Due to a Discord limitation, please keep your reason below 475 characters.")
            return
        expiration = datetime.strptime(str(datetime.now(timezone.utc) + timedelta(seconds=duration)).partition(".")[0],
                                       "%Y-%m-%d %H:%M:%S")
        entry = {
            member.id: {
                "expiration": str(expiration)
            }
        }
        with open("temporary_punishments.json", "r+") as temp_punish:
            data = json.load(temp_punish)
            data["temporary_punishments"]["mutes"].update(entry)
            temp_punish.seek(0)
            json.dump(data, temp_punish, indent=4)
        await ctx.message.add_reaction("👍")

    @commands.command(aliases=["ub"], brief="Unbans a member.", help="Unbans a member. Supports @mention and ID.",
                      name="unban", usage="unban <@mention>`/`<ID> <reason>")
    @commands.guild_only()
    async def unban(self, ctx, user: Union[disnake.Member, disnake.User], *, reason: str = None):
        if user is None:
            raise UserNotFound("user")
        try:  # Functions in this block check to see if the provided user is banned.
            await ctx.guild.fetch_ban(user)
        except Forbidden:
            raise BotMissingPermissions
        except NotFound:
            await ctx.send("That user is not banned.")
            return
        moderator = disnake.utils.get(ctx.guild.roles, name="Nutty Moderator")
        admin = disnake.utils.get(ctx.guild.roles, name="Admin")
        if isinstance(user, disnake.Member) and (moderator in user.roles and admin not in ctx.author.roles):
            await ctx.send(f"You cannot un-punish a fellow {moderator.name}.")  # Go ahead and unban a moderator who is
            # not currently banned... I guess...
            return
        if reason is None:
            await ctx.send("Please specify a reason for the unban.")
            return
        try:
            await ctx.guild.unban(user, reason=f"{ctx.author.id}: {reason}")
        except Forbidden:
            raise BotMissingPermissions
        except HTTPException:
            await ctx.send("Due to a Discord limitation, please keep your reason below 490 characters.")
            return
        with open("temporary_punishments.json", "r+") as temp_punish:
            data = json.load(temp_punish)
            for entry in data["temporary_punishments"]["bans"].keys():
                if str(user.id) in entry:
                    del data["temporary_punishments"]["bans"][entry]
                    temp_punish.seek(0)
                    json.dump(data, temp_punish, indent=4)
                    temp_punish.truncate()
                    break
                else:
                    continue
        await ctx.message.add_reaction("👍")

    @commands.command(aliases=["um", "unstfu"], brief="Unmutes a member.", help="""Unmutes a member. Supports \
@mention and ID.""", name="unmute", usage="unmute <@mention>`/`<ID> (reason)")
    @commands.guild_only()
    async def unmute(self, ctx, member: disnake.Member, *, reason: str = "Unspecified reason."):
        if member is None:
            raise MemberNotFound("member")
        muted = disnake.utils.get(ctx.guild.roles, name="Muted")
        if muted not in member.roles:
            await ctx.send("That member is not muted.")
            return
        moderator = disnake.utils.get(ctx.guild.roles, name="Nutty Moderator")
        admin = disnake.utils.get(ctx.guild.roles, name="Admin")
        if isinstance(member, disnake.Member) and (moderator in member.roles and admin not in ctx.author.roles):
            await ctx.send(f"You cannot un-punish a fellow {moderator.name}.")
            return
        try:
            await member.remove_roles(muted, reason=f"{ctx.author.id}: {reason}")
        except Forbidden:
            raise BotMissingPermissions
        except HTTPException:
            await ctx.send("Due to a Discord limitation, please keep your reason below 490 characters.")
            return
        with open("temporary_punishments.json", "r+") as temp_punish:
            data = json.load(temp_punish)
            for entry in data["temporary_punishments"]["mutes"].keys():
                if str(member.id) in entry:
                    del data["temporary_punishments"]["mutes"][entry]
                    temp_punish.seek(0)
                    json.dump(data, temp_punish, indent=4)
                    temp_punish.truncate()
                    break
                else:
                    continue
        await ctx.message.add_reaction("👍")  # TODO: A lookup command, search by lodestone name/id, give basic info,
        # a lodestone link, and a confirmation of whether or not that user is in the database OR Discord


def setup(bot):
    bot.add_cog(Mod(bot))
