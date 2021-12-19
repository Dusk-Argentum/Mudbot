from datetime import datetime, timedelta, timezone

import disnake
from disnake import HTTPException, Forbidden
from disnake.ext import commands, tasks
from disnake.ext.commands import BotMissingPermissions

import json

from mudbot import GUILD, PREFIX

import random

import re


def is_allowed_channel():  # This defines a custom check called is_allowed_channel. Used in a couple of commands.
    async def predicate(ctx):  # Defines the predicate that must be met.
        if ctx.command.name not in ["spawner", "conductor"]:  # Functions in this block execute if the command invoked
            # is not one of the roles added via role request tickets.
            with open("server_config.json", "r") as server_config:
                data = json.load(server_config)
            for count, channel in enumerate(data["server_config"][str(ctx.guild.id)]["allowed_channels"]
                                            [ctx.command.name], start=1):
                if str(ctx.channel.id) == (data["server_config"][str(ctx.guild.id)]["allowed_channels"]
                                           [ctx.command.name][str(count)]):
                    return True
                else:
                    continue
            else:
                return False
        elif ctx.command.name in ["spawner", "conductor"]:  # Functions in this block execute if the command invoked
            # is a role-request role.
            if "rolerequest" in ctx.channel.name:
                return True
            else:
                return False
    return commands.check(predicate)


class MudTasks(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @tasks.loop(minutes=5)  # Defines a task that executes automatically and the time between tasks.
    async def auto_kick_unverified(self):  # Defines the task that automatically kicks people who have failed to verify
        # within a set time period.
        guild = self.bot.get_guild(GUILD)
        with open("server_config.json", "r") as server_config:
            data = json.load(server_config)
        channel = disnake.utils.get(guild.channels, name="get-registered-here")
        state = data["server_config"][str(guild.id)]["auto_punish"]["kick"]["state"]
        threshold = data["server_config"][str(guild.id)]["auto_punish"]["kick"]["threshold"]
        threshold = re.search(r"(^\d{1,2})(m$|h$|d$)", threshold)
        number = ""
        word = ""
        if threshold.group(2).lower() == "m":
            number = str(threshold.group(1))
            threshold = int(threshold.group(1)) * 60
            if threshold != 1:
                word = "minutes"
            elif threshold == 1:
                word = "minute"
        elif threshold.group(2).lower() == "h":
            number = str(threshold.group(1))
            threshold = int(threshold.group(1)) * 3600
            if threshold != 1:
                word = "hours"
            elif threshold == 1:
                word = "hour"
        elif threshold.group(2).lower() == "d":
            number = str(threshold.group(1))
            threshold = int(threshold.group(1)) * 86400
            if threshold != 1:
                word = "days"
            elif threshold == 1:
                word = "day"
        for member in channel.members:
            age = int(str((datetime.strptime(str(datetime.now(timezone.utc)).split(".")[0],
                                             "%Y-%m-%d %H:%M:%S") - datetime.strptime
                                            (str(member.joined_at).split(".")[0],
                                             "%Y-%m-%d %H:%M:%S")).total_seconds()).split(".")[0])
            if len(member.roles) == 1 and age > threshold:  # Functions in this block execute if the members has
                # no roles (the only role they have is @everyone role, which is the one role) and they have been
                # in the Discord for longer than the threshold.
                reason = f"""You were kicked from the {guild.name} Discord for failing to verify your character within \
{number} {word} of joining.
You are welcome to join again! Be sure to follow the directions at the top of the #get-registered-here channel.
http://discord.gg/aetherhunts"""
                embed = disnake.Embed(description=reason, color=disnake.Color(0xf06807),
                                      title=f"You were kicked from {guild.name}.")
                embed.set_author(icon_url=self.bot.user.avatar.url, name=self.bot.user.name)
                embed.set_thumbnail(url=guild.banner.url)
                embed.set_footer(icon_url=guild.icon.url, text=guild.name)
                try:
                    await member.send(embed=embed)
                except (Forbidden, HTTPException):
                    pass
                await guild.kick(member, reason=reason)
            else:
                continue

    @tasks.loop(minutes=1)
    async def check_temp_bans(self):
        guild = self.bot.get_guild(GUILD)
        with open("temporary_punishments.json", "r") as temp_punish:
            data = json.load(temp_punish)
        for user, time in list(data["temporary_punishments"]["bans"].items()):
            expiration = datetime.strptime(str(data["temporary_punishments"]["bans"][str(user)]["expiration"]),
                                           "%Y-%m-%d %H:%M:%S")
            if expiration < datetime.strptime(str(datetime.now(timezone.utc)).split(".")[0], "%Y-%m-%d %H:%M:%S"):
                del data["temporary_punishments"]["bans"][str(user)]
                user = await self.bot.fetch_user(int(user))
                try:
                    await guild.unban(user, reason="Removed temporary ban.")
                except Forbidden:
                    raise BotMissingPermissions(["unban"])
                except HTTPException:
                    pass
        else:
            with open("temporary_punishments.json", "w") as temp_punish:
                temp_punish.seek(0)
                json.dump(data, temp_punish, indent=4)
                temp_punish.truncate()

    @tasks.loop(minutes=1)
    async def check_temp_mutes(self):
        guild = self.bot.get_guild(GUILD)
        with open("temporary_punishments.json", "r") as temp_punish:
            data = json.load(temp_punish)
        for user, time in list(data["temporary_punishments"]["mutes"].items()):
            expiration = datetime.strptime(str(data["temporary_punishments"]["mutes"][str(user)]["expiration"]),
                                           "%Y-%m-%d %H:%M:%S")
            if expiration < datetime.strptime(str(datetime.now(timezone.utc)).split(".")[0], "%Y-%m-%d %H:%M:%S"):
                del data["temporary_punishments"]["mutes"][str(user)]
                user = guild.get_member(int(user))
                if user is None:
                    continue
                elif user is not None:
                    muted = disnake.utils.get(guild.roles, name="Muted")
                    try:
                        await user.remove_roles(muted, reason="Removed temporary mute.")
                    except Forbidden:
                        raise BotMissingPermissions(["role_update"])
                    except HTTPException:
                        pass
        else:
            with open("temporary_punishments.json", "w") as temp_punish:
                temp_punish.seek(0)
                json.dump(data, temp_punish, indent=4)
                temp_punish.truncate()

    @tasks.loop(minutes=5)
    async def status_rotation(self):  # Defines the task which rotates the status every so often.
        with open("bot_config.json", "r") as bot_config:
            data = json.load(bot_config)
        if data["bot_config"]["status"]["state"] == "False":
            return
        status = (data["bot_config"]["status"]["statuses"]
                  [str(random.randint(1, len(data["bot_config"]["status"]["statuses"])))])  # Pulls a random status.
        await self.bot.change_presence(activity=disnake.Game(f"""{status} | {PREFIX}help"""))  # Changes the Activity
        # to whatever the random status pulled is.

    @tasks.loop(minutes=1)
    async def viewer_removal(self):
        guild = self.bot.get_guild(GUILD)
        with open("licensed_viewers.json", "r") as licensed_viewers:
            data = json.load(licensed_viewers)
        channel = disnake.utils.get(guild.channels, name="get-registered-here")
        viewer = disnake.utils.get(guild.roles, name="Licensed Viewer")
        for member in channel.members:
            if viewer in member.roles:
                if str(member.id) in list(data["licensed_viewers"]):
                    if datetime.strptime(str(data["licensed_viewers"][str(member.id)]["time"]), "%Y-%m-%d %H:%M:%S")\
                        < datetime.strptime(str(datetime.now(timezone.utc) - timedelta(minutes=5)).split(".")[0],
                                            "%Y-%m-%d %H:%M:%S"):
                        await member.remove_roles(viewer)
                        del data["licensed_viewers"][str(member.id)]
                        continue
                elif str(member.id) not in list(data["licensed_viewers"]):
                    await member.remove_roles(viewer)
                    continue
        with open("licensed_viewers.json", "r+") as licensed_viewers:
            licensed_viewers.seek(0)
            json.dump(data, licensed_viewers, indent=4)
            licensed_viewers.truncate()
            for member in list(data["licensed_viewers"]):
                member = guild.get_member(int(member))
                if member is None:
                    del data["licensed_viewers"][str(member)]
                    continue
            licensed_viewers.seek(0)
            json.dump(data, licensed_viewers, indent=4)
            licensed_viewers.truncate()


def setup(bot):
    bot.add_cog(MudTasks(bot))
