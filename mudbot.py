import os  # The os module. Used in Mudbot to call up environmental variables, which help obscure sensitive
# information.

import discord  # The Discord module. Used in Mudbot to do Discord things. Rest in peace.
from discord import HTTPException, Forbidden, NotFound  # Error handling imports.
from discord.ext import commands, tasks  # Imports the commands and tasks submodules, for use in commands and tasks.
from discord.ext.commands import CheckFailure, CommandInvokeError, CommandNotFound, MemberNotFound  # Error handling imports.
from discord.ext.commands import guild_only, NoPrivateMessage, has_role, has_any_role, MissingRole, UserNotFound
from discord.ext.commands import MissingAnyRole


import random  # The random module. Used in Mudbot to generate random numbers when need be.


import re  # The regex module. Extremely useful in gathering and paring down information from documents
# and other text strings.


import pyxivapi  # Imports pyxivapi. For linking. And maybe other stuff, down the line.
from pyxivapi.exceptions import XIVAPIForbidden, XIVAPIBadRequest, XIVAPINotFound, XIVAPIServiceUnavailable
from pyxivapi.exceptions import XIVAPIInvalidLanguage, XIVAPIInvalidIndex, XIVAPIInvalidColumns, XIVAPIInvalidFilter
from pyxivapi.exceptions import XIVAPIInvalidWorlds, XIVAPIInvalidDatacenter, XIVAPIError  # Pyxivapi's error handling.


import asyncio  # A pyxivapi dependency. Also used for sleeping when need be.
import aiohttp  # A web handler. Useful in grabbing information from the internet, eg. the Lodestone.


import json  # Json is used to keep track of imported character information and the like.


from datetime import datetime, timezone  # For use in getting times.


PREFIX = "+"  # This defines the prefix for Mudbot. Commands MUST start with this character to be processed and run.
DESCRIPTION = "A bot for use in the Aether Hunts Discord server. Made by Dusk Argentum#6530."
# This defines Mudbot's description.
TOKEN = os.environ.get("Mudbot_TOKEN")  # This defines the unique token used by Mudbot to log in to Discord.
# Stored in environmental variables for obscurity's sake.
XIVAPI_TOKEN = os.environ.get("Mudbot_XIVAPI")  # This defines the unique token used by Mudbot to log in to XIVAPI.


SHOULD_NOTIFY_MILESTONE = 1
SHOULD_STATUS_CHANGE = 1  # A global variable that defines whether or not the bot's "Playing" status should change
# at any given time.
VERSION = "1.1.0BETA"  # Defines the version number, for use in internal tracking.


intents = discord.Intents.default()  # Gives the bot the explicit permission to use the default intents.
intents.members = True  # Gives the bot explicit permission to use the Members "privileged Intent", which grants
# the bot the ability to view the member list.
intents.bans = True  # Gives the bot explicit permission to receive information on ban and unban events.


bot = commands.Bot(command_prefix=commands.when_mentioned_or(PREFIX), description=DESCRIPTION, pm_help=False,
                   case_insensitive=True, intents=intents)  # Defines the bot as a bot.


bot.remove_command("help")  # Removes the in-built help command in favor of a custom one.


# ^ EVENTS: These execute at varying times depending on their conditions.


@bot.event  # This defines an event, which listens for the condition specified, and then executes.
async def on_command_error(ctx, error):  # This event executes when the bot hears that specified exceptions are caught.
    if isinstance(error, CommandNotFound):  # This executes if a command is not found.
        error = f"Command not found. View `+help` for valid commands."
    elif isinstance(error, CommandInvokeError):  # This executes if a command is used incorrectly, or in circumstances
        # where a command cannot finish executing properly and there is no specific handling for the error the command
        # invokes.
        error = f"Incorrect invocation. Please re-examine the command in `+help`."
    elif isinstance(error, MemberNotFound):
        if ctx.invoked_with == "info":  # Functions in this block execute if `info` is being used improperly.
            error = f"""Member not found.
Correct usage: `+info member_mention`, eg. `+info <@!97153790897045504>`.
To grab a member's Discord ID, be sure to enable Developer Mode in your Discord settings, then simply right-click \
them and click "Copy ID"."""
        else:  # Functions in this block execute if the command being invoked is not `info`.
            return  # Stops processing the event.
    elif isinstance(error, MissingAnyRole):  # This executes if a command is being used by someone who does not have
        # the roles required to run it.
        error = "You don't have any of the roles required to run this command."
    await ctx.message.channel.send(f"Error: {error}")  # Sends the error message in the channel where the command was
    # invoked.
    return


@bot.event
async def on_member_ban(guild, user):  # This event executes when the bot hears a ban.
    autoban = 0  # Defines whether or not the ban heard was an autoban or not.
    channel = bot.get_channel(654603610134675456)  # Defines the channel that the bot will send the log to.
    if guild.id != channel.guild.id:  # Functions in this block will execute if the ID of the guild heard from the event
        # and the guild of the defined channel are not the same.
        return  # Stops processing the event. Essentially, this means that Mudbot will not log bans from servers
    # that are not Aether Hunts.

    def predicate(entry):  # Defines the predicate to search for, and what the variable that the information returned
        # will be defined as.
        return entry.target.id == user.id and entry.action == discord.AuditLogAction.ban  # Defines the conditions
    # that the information returned must meet before being able to be returned.

    entry = await guild.audit_logs().find(predicate)  # Searches the audit log for the first entry that meets the
    # conditions defined in the predicate.
    if entry.user.id == 204255221017214977 and "Your account is too new" in entry.reason:  # Functions in this block
        # will execute if the creator of the ban is Mudbot and the string "Your account is too new" in the ban reason.
        channel = bot.get_channel(881170467292082196)  # Re-defines the channel that the bot will send the log to
        # to the auto actions log.
        autoban = 1  # Defines the ban as an automated ban.
    timestamp = int((entry.created_at - datetime.fromisoformat("1970-01-01")).total_seconds())  # Defines the amount
    # of seconds that have passed since epoch.
    embed = discord.Embed(title=f"""{"Member banned." if autoban == 0 else "Member automatically banned."}""",
                          color=discord.Color(0xf02a07))  # Defines an embed and its basic parameters. The title will be
    # different depending on whether or not the ban heard was an autoban or not.
    embed.set_author(name=f"{entry.user.name}", icon_url=f"{entry.user.avatar_url}")  # Sets the embed's author as
    # the person who initiated the ban.
    embed.set_thumbnail(url=f"{entry.target.avatar_url}")  # Sets the embed's thumbnail as the same as the avatar of
    # the banned user.
    embed.add_field(name="Responsible Nutty Moderator:", value=f"""{entry.user.mention}
{entry.user}
({entry.user.id})""", inline=True)  # Sets a field informing who initiated the ban.
    embed.add_field(name="Action Taken On:", value=f"""{entry.target.mention}
{entry.target}
({entry.target.id})""", inline=True)  # Sets a field informing who was the target of the ban.
    embed.add_field(name="Time of Action:", value=f"<t:{str(timestamp)}>", inline=False)  # Sets a field giving
    # a timestamp mention to the time of the action.
    embed.add_field(name="Reason:",
                    value=f"""{entry.reason if entry.reason is not None else "No reason specified."}""",
                    inline=False)  # Sets a field informing the reason for the ban, or saying "No reason specified."
    # if no reason was given.
    embed.set_footer(text=f"{guild.name}", icon_url=f"{bot.user.avatar_url}")
    await channel.send(embed=embed)
    return


@bot.event
async def on_member_join(member):  # This event executes when the bot hears a join.
    channel = bot.get_channel(881170467292082196)
    guild = member.guild
    if guild.id != channel.guild.id:
        return
    with open("auto_punish_info.json", "r") as auto_punish_info:  # Opens the auto_punish_info json, for use in
        # determining whether the autoban is on or off and the age threshold new accounts must meet.
        data = json.load(auto_punish_info)  # Loads the json's data as a json.
        should_auto_punish = data["auto_punish_info"]["ban"]["enabled"]  # Loads the data from the auto_punish_info
        # json on whether the autoban is on or off.
        account_age_threshold = data["auto_punish_info"]["ban"]["threshold"]  # Loads the data from the auto_punish_info
        # json on what the account age threshold is.
        auto_punish_info.close()  # Closes the json.
    if should_auto_punish != "true":  # Functions in this block execute if should_auto_punish is anything but "true".
        return
    account_age_threshold = re.search(r"(^\d{1,2})(m$|h$|d$)", str(account_age_threshold), re.IGNORECASE)  # Searches
    # the account_age_threshold for the age threshold.
    account_age_threshold_number = int(account_age_threshold.group(1))  # Defines the account_age_threshold number
    # as the first group collected during the regex search above.
    account_age_threshold_letter = str(account_age_threshold.group(2))  # Defines the account_age_threshold letter as
    # the second group collected during the regex search above.
    if account_age_threshold_letter == "m":  # Functions in this block execute if the letter is "m" for minutes.
        account_age_threshold = account_age_threshold_number * 60  # Multiplies the number by the amount of seconds in
        # one minute.
    elif account_age_threshold_letter == "h":  # Functions in this block execute if the letter is "h" for hours.
        account_age_threshold = account_age_threshold_number * 3600  # Multiplies the number by the amount of seconds in
        # one hour.
    elif account_age_threshold_letter == "d":  # Functions in this block execute if the letter is "d" for days.
        account_age_threshold = account_age_threshold_number * 86400  # Multiplies the number by the amount of seconds
        # in one day.
    account_creation_time = datetime.strptime(str(member.created_at).partition(".")[0], "%Y-%m-%d %H:%M:%S")  # Gets
    # the date and time that the member who joined was created at, removes milliseconds, and converts the result
    # into a datetime object for use later.
    account_age = (str((datetime.strptime(str(datetime.now(timezone.utc)).partition(".")[0],
                   "%Y-%m-%d %H:%M:%S") - account_creation_time).total_seconds()).partition(".")[0])  # Subtracts
    # the above account creation time from the current date and time, removing milliseconds and timezone information
    # (the account creation time Discord returns is UTC by default) from the current date and time, for a definitive
    # account age in seconds.
    if int(account_age) < account_age_threshold:  # Functions in this block execute if the account's age in seconds is
        # less than the account age threshold, which is also in seconds.

        def predicate(entry):  # This is similar to the predicate from on_member_ban, except it searches for an unban.
            return member.id == entry.target.id and entry.action == discord.AuditLogAction.unban

        entry = await member.guild.audit_logs().find(predicate)
        if entry is None:  # Functions in this block execute if there are no unbans found for this member.
            # Used to prevent the bot from autobanning people who successfully appealed and try to rejoin with an
            # account under the age threshold.
            embed = discord.Embed(title=f"Sorry, you're too new!", description="""Your account is too new to join \
this Discord! Please DM <@67089121339777024> (Satori#0240) or visit \
[our ban appeal page](https://unban.aetherhunts.net/) to appeal.""", color=discord.Color(0xf02a07))
            embed.set_author(name=f"{guild.name}", icon_url=f"{guild.icon_url}")
            embed.set_thumbnail(url=f"{guild.banner_url}")
            embed.set_footer(text=f"{guild.name}", icon_url=f"{bot.user.avatar_url}")
            await member.send(embed=embed)
            await member.guild.ban(member, reason=f"""Your account is too new to join this Discord! Please DM
<@67089121339777024> (Satori#0240) or visit [our ban appeal page](https://unban.aetherhunts.net/) to appeal.""")  # Bans
            # the member.
            return
        return  # This second return is here to stop processing if there is an entry found.


@bot.event
async def on_member_remove(member):  # This event triggers when the bot hears that a member left a server. Since there
    # is no defined "on_member_kick" event, this is the one we use.
    autokick = 0  # This defines the default value for whether the kick was an autokick or not.
    channel = bot.get_channel(654603610134675456)
    guild = member.guild
    if guild.id != channel.guild.id:
        return

    def predicate(entry):  # Similar to previous predicates, this one instead searches the audit log for kicks.
        return entry.target.id == member.id and entry.action == discord.AuditLogAction.kick

    entry = await guild.audit_logs().find(predicate)
    if entry is None:  # Functions in this block execute if there is no kick entry found for that member ever.
        return
    entry_creation_time = datetime.strptime(str(entry.created_at).partition(".")[0], "%Y-%m-%d %H:%M:%S")  # Similarly
    # to the defining of the member's account creation time from on_member_join, this instead uses the creation time of
    # the audit log entry.
    entry_age = str((datetime.strptime(str(datetime.now(timezone.utc)).partition(".")[0],
                                       "%Y-%m-%d %H:%M:%S") - entry_creation_time).total_seconds()).partition(".")[0]
    # Similarly to the calculation of the member's account age from on_member_join, this instead calculates the age of
    # the audit log entry!
    if int(entry_age) > 2:  # Functions in this block execute if the entry's age is greater than 2 seconds. This is
        # mainly used to prevent members who had been kicked before from falsely triggering a kick log entry.
        return
    if entry.user.id == 732151283947012187 and "failing to verify your character" in entry.reason:  # Functions in this
        # block execute if Mudbot was the one who kicked the member before, and "failing to verify your character" is
        # in their kick reason.
        channel = bot.get_channel(881170467292082196)  # Re-defines the channel as the channel the channel that the bot
        # logs automated actions in.
        autokick = 1  # Defines the kick as an automated kick.
    timestamp = int((entry.created_at - datetime.fromisoformat("1970-01-01")).total_seconds())  # Defines the amount
    # of seconds since epoch.
    embed = discord.Embed(title=f"""{"Member kicked." if autokick == 0 else "Member automatically kicked."}""",
                          color=discord.Color(0xf59a38))  # Defines the embed and some of its parameters. The title will
    # be different depending on if the kick was automated or not.
    embed.set_author(name=f"{entry.user.name}", icon_url=f"{entry.user.avatar_url}")
    embed.set_thumbnail(url=f"{entry.target.avatar_url}")
    embed.add_field(name=f"Responsible Nutty Moderator:", value=f"""{entry.user.mention}
{entry.user}
({entry.user.id})""", inline=True)
    embed.add_field(name=f"Action Taken On:", value=f"""{entry.target.mention}
{entry.target}
({entry.target.id})""", inline=True)
    embed.add_field(name=f"Time of Action:", value=f"""<t:{str(timestamp)}>""", inline=False)
    embed.add_field(name=f"Reason:",
                    value=f"""{entry.reason if entry.reason is not None else "No reason specified."}""",
                    inline=False)
    embed.set_footer(text=f"{guild.name}", icon_url=f"{bot.user.avatar_url}")
    await channel.send(embed=embed)
    return


@bot.event
async def on_member_unban(guild, user):  # This event triggers when the bot hears an unban.
    channel = bot.get_channel(654603610134675456)  # Much of this is similar to earlier events, so will not be commented
    # unless there is something majorly different.
    if guild.id != channel.guild.id:
        return

    def predicate(entry):
        return entry.target.id == user.id and entry.action == discord.AuditLogAction.unban

    entry = await guild.audit_logs().find(predicate)
    timestamp = int((entry.created_at - datetime.fromisoformat("1970-01-01")).total_seconds())
    embed = discord.Embed(title="User unbanned.", color=discord.Color(0xebaba0))
    embed.set_author(name=f"{entry.user.name}", icon_url=f"{entry.user.avatar_url}")
    embed.set_thumbnail(url=f"{entry.target.avatar_url}")
    embed.add_field(name="Responsible Nutty Moderator:", value=f"""{entry.user.mention}
{entry.user}
({entry.user.id})""", inline=True)
    embed.add_field(name="Action Taken On:", value=f"""{entry.target.mention}
{entry.target}
({entry.target.id})""", inline=True)
    embed.add_field(name="Time of Action:", value=f"""<t:{str(timestamp)}>""", inline=False)
    embed.add_field(name="Reason:",
                    value=f"""{entry.reason if entry.reason is not None else "No reason specified."}""",
                    inline=False)
    embed.set_footer(text=f"{guild.name}", icon_url=f"{bot.user.avatar_url}")
    await channel.send(embed=embed)
    return


@bot.event
async def on_member_update(before, after):  # This event triggers when the bot hears a status update, an activity
    # update, a nickname update, or a role update. In this instance, we use it for roles.
    channel = bot.get_channel(654603610134675456)
    guild = before.guild
    if guild.id != channel.guild.id:
        return
    muted_search = "<Role id=733203653585928232 name='Muted'>"  # Defines the text to search for in the update.
    if muted_search not in str(before.roles) and muted_search not in str(after.roles):  # Functions in this block
        # execute if the muted role is neither in the before state nor the after state of the update. This is used
        # to prevent this event from processing any further for any events that are not related to the Muted role.
        return

    def predicate(entry):  # Similar to previous predicates, this one instead searches for a role update.
        return before.id == after.id and entry.action == discord.AuditLogAction.member_role_update

    entry = await before.guild.audit_logs().find(predicate)
    if muted_search in str(before.roles) and muted_search not in str(after.roles):  # Functions in this block execute if
        # a user no longer has the muted role. This prevents the event from triggering if the Muted role is in both the
        # before state and after state.
        timestamp = int((entry.created_at - datetime.fromisoformat("1970-01-01")).total_seconds())
        embed = discord.Embed(title="Member unmuted.", color=discord.Color(0xb8dbc2))
        embed.set_author(name=f"{entry.user.name}", icon_url=f"{entry.user.avatar_url}")
        embed.set_thumbnail(url=f"{entry.target.avatar_url}")
        embed.add_field(name="Responsible Nutty Moderator:", value=f"""{entry.user.mention}
{entry.user}
({entry.user.id})""", inline=True)
        embed.add_field(name=f"Action Taken On:", value=f"""{entry.target.mention}
{entry.target}
({entry.target.id})""", inline=True)
        embed.add_field(name=f"Time of Action:", value=f"""<t:{str(timestamp)}>""", inline=False)
        embed.add_field(name=f"Reason:",
                        value=f"""{entry.reason if entry.reason is not None else "No reason specified."}""",
                        inline=False)
        embed.set_footer(text=f"{guild.name}", icon_url=f"{bot.user.avatar_url}")
        await channel.send(embed=embed)
        return
    elif muted_search in str(after.roles) and muted_search not in str(before.roles):  # The inverse of the above block.
        timestamp = int((entry.created_at - datetime.fromisoformat("1970-01-01")).total_seconds())
        embed = discord.Embed(title=f"Member muted.", color=discord.Color(0x69727a))
        embed.set_author(name=f"{entry.user.name}", icon_url=f"{entry.user.avatar_url}")
        embed.set_thumbnail(url=f"{entry.target.avatar_url}")
        embed.add_field(name=f"Responsible Nutty Moderator:", value=f"""{entry.user.mention}
{entry.user}
({entry.user.id})""", inline=True)
        embed.add_field(name=f"Action Taken On:", value=f"""{entry.target.mention}
{entry.target}
({entry.target.id})""", inline=True)
        embed.add_field(name="Time of Action:", value=f"""<t:{str(timestamp)}>""", inline=False)
        embed.add_field(name="Reason:",
                        value=f"""{entry.reason if entry.reason is not None else "No reason specified."}""",
                        inline=False)
        embed.set_footer(text=f"{guild.name}", icon_url=f"{bot.user.avatar_url}")
        await channel.send(embed=embed)
        return


@bot.event
async def on_ready():  # This event executes when the bot hears a successful connection established. Essentially,
    # this runs on bot startup.
    await bot.change_presence(status=discord.Status.online, activity=discord.Game("w/ hunters! | +help"))  # The reason
    # this is one of the few instances of + being used instead of PREFIX is mainly so I can test the bot on the Mudbot
    # token without confusing people about the bot's prefix.
    # The above changes the bot's presence (status) to the specified "game" when starting up.
    autokick_unverified.start()  # This sets the autokick_unverified background task in motion.
    status_rotation.start()  # This sets the status_rotation background task in motion.
    print("Mudbot online. Awaiting commands!")  # Prints to the console that the bot is ready to be used.
    return


@bot.listen(name="on_member_update")  # This declares that the bot must listen for events of the specified type.
# bot.listen is used because the on_member_update event is already being used, and multiple of those cannot exist.
# This essentially serves the same function. This will likely be commented out or removed at a later date.
async def milestone_listener(before, after):
    channel = bot.get_channel(740603224826052608)
    guild = before.guild
    global SHOULD_NOTIFY_MILESTONE  # Imports the SHOULD_NOTIFY_MILESTONE global variable for reading and editing.
    if guild.id != channel.guild.id:
        return
    licensed_hunter_role = discord.utils.get(guild.roles, name="Licensed Hunter")  # Defines the Licensed Hunter role.
    licensed_hunter_role_count = len(licensed_hunter_role.members)  # Defines the length of the list of the people
    # who have the Licensed Hunter role. Essentially, this counts the people who have that role.
    if licensed_hunter_role_count == 33333 and\
            str(licensed_hunter_role) not in str(before.roles) and str(licensed_hunter_role) in str(after.roles) and\
            SHOULD_NOTIFY_MILESTONE == 1:  # Functions in this block execute if the amount of Licensed Hunters is 33333,
        # the Licensed Hunter role is not in the before state's roles, the Licensed Hunter role is in the after state's
        # roles, and the SHOULD_NOTIFY_MILESTONE global variable is 1.
        await channel.send(f"""{after.mention} is our 33,333rd Licensed Hunter!
<@97153790897045504> <@241067525771624448>""")  # Sends a message to the channel informing the people who are being
        # pinged the name of the 33333rd, Licensed Hunter.
        SHOULD_NOTIFY_MILESTONE = 0  # Sets the SHOULD_NOTIFY_MILESTONE global variable to 0 so no additional pings
        # happen.
        return
    return


# ^ BACKGROUND TASKS:  These tasks execute in the background constantly.


@tasks.loop(seconds=300.0)  # Sets the task to loop every 300 seconds, or 5 minutes.
async def autokick_unverified():  # Defines the autokick_unverified task.
    with open("auto_punish_info.json", "r") as auto_punish_info:  # Opens the auto_punish_info file.
        data = json.load(auto_punish_info)  # Defines the data of the auto_punish_info json.
        should_auto_punish = data["auto_punish_info"]["kick"]["enabled"]  # Reads the data of the specified key.
        auto_punish_info.close()  # Closes the file.
    if should_auto_punish != "true":  # Functions in this block execute if should_auto_punish is not true.
        return
    guild = bot.get_guild(542602456132091904)  # Defines Aether Hunts.
    channel = bot.get_channel(738670827490377800)  # Defines the get_registered_here channel.
    owner = bot.get_user(bot.owner_id)  # Hehe, that's me! That's Dusk!
    for member in channel.members:  # Functions in this block execute for every member in the get_registered_here
        # channel.
        member_duration_raw = datetime.now() - member.joined_at  # Gets the raw amount of time a member has been
        # on the server.
        member_duration_seconds_raw = member_duration_raw.total_seconds()  # Turns the raw amount of time into
        # seconds.
        member_duration_seconds = (str(member_duration_seconds_raw).split(".")[0])  # Gets the final product of how
        # long a member has been on the server for comparison as a number by removing microseconds.
        if len(member.roles) == 1 and int(member_duration_seconds) > 604800:  # Functions in this block only
            # execute if a member has no roles (a member with 0 roles has 1 role, apparently) and they
            # have been on the server for more than 604800 seconds, which is one week.
            reason = """You were kicked from the Aether Hunts Discord for failing to verify your character within \
one week of joining.
You are welcome to join again! Be sure to follow the directions at the top of the #get-registered-here channel.
http://discord.gg/aetherhunts"""  # Defines the reason for kicking, which is logged and also sent to the receiving
            # user so they know why they were kicked and how to rejoin.
            try:  # Functions in this block are attempted to execute...
                await member.send(f"{reason}")  # Sends the reason for the kick to the user.
            except Forbidden:  # If, for some reason, the user cannot receive any messages from Mudbot,
                # either this exception or the next will catch, but they both pass on anyway. This is not the case
                # further on.
                pass
            except HTTPException:
                pass
            try:
                await guild.kick(member, reason=reason)  # Kicks the user, giving the reason which is set in the
                # audit log.
            except Forbidden:  # If, for some reason, the user cannot be kicked, functions in this block or the
                # next execute, letting the owner know. This should never happen. I don't know why I made it a
                # try-except block.
                await owner.send(f"""I failed an automatic unverified kick! I attempted to kick {member} \
({member.id}) and failed. Error: FORBIDDEN.""")
                return
            except HTTPException:
                await owner.send(f"""I failed an automatic unverified kick! I attempted to kick {member} \
({member.id}) and failed. Error: HTTPException.""")
                return
            continue  # Loops back to the top of the "these functions happen to every member in the channel" loop.
        elif len(member.roles) == 1 and int(member_duration_seconds) < 604800:  # Functions in this block
            # execute if a member in the channel has no roles but has been here for less than a week.
            continue
        elif len(member.roles) > 1:  # Functions in this block execute if a member has more than zero roles
            # in the channel. Fun fact: I initially tried this with "elif roles greater than or equal to two", but
            # it didn't work. "greater than or equal to two" and "greater than one" mean the same fucking thing.
            continue
    return  # Once the function has looped for every member of the channel, stops doing the loop until the task is
    # called again in 5 minutes.


@tasks.loop(seconds=150.0)  # Defines a task which loops (or is supposed to...) every 150 seconds (2 1/2 minutes).
async def status_rotation():  # Defines the status_rotation event.
    while SHOULD_STATUS_CHANGE == 1:  # Functions in this block loop by default (as the SHOULD_STATUS_CHANGE global
        # is automatically defined to be 1).
        status = []  # Sets an empty variable to be filled later.
        random_status = random.choice(["w/ hunters!",
                                       "Bog in!",
                                       "Flush out!"])  # Randomly chooses between these statuses.
        await asyncio.sleep(150)  # Sleeps for 2 1/2 minutes, because I can't get the seconds thing to work right.
        await bot.change_presence(status=discord.Status.online, activity=discord.Game(f"{str(random_status)} | +help"))
        # Change's the bot's status to the randomly chosen status, and appends the command that is used to invoke the
        # help message after any of them.


@status_rotation.before_loop  # Defines a task to be undertaken before a status_rotation loop starts.
async def before_status_rotation():
    if SHOULD_STATUS_CHANGE == 0:  # Does not change the status if the SHOULD_STATUS_CHANGE global variable is 0.
        return
    elif SHOULD_STATUS_CHANGE == 1:  # Does change the status if the SHOULD_STATUS_CHANGE global variable is 1.
        # This is the default behavior.
        pass


# ! TESTING GROUND: Any commands here are in-progress and being tested. Use is forbidden.


# HELP COMMAND: This is the block where the help command is, which lists all commands and their arguments.


@bot.group(pass_context=True, name="help_", aliases=["cmds", "commands", "h", "help"], case_insensitive=True)  # Defines
# the help command group and any of its aliases.
async def help_(ctx):
    """Shows a list of all commands, and whether or not a command has subcommands."""
    if ctx.invoked_subcommand is None:  # Functions in this block execute if no subcommands are invoked, eg. !help
        random_color = random.randint(1, 16777215)  # Generates a random color.
        embed = discord.Embed(title="Mudbot Commands", color=discord.Color(int(random_color)))  # Defines the beginning
        # of the embed, as well as setting its color to the random color generated above.
        embed.add_field(name="Hunting", value=f"""`{PREFIX}fate [fate]` [Alias: `{PREFIX}f`]
Sends the information for the specified `fate` when invoked.

`{PREFIX}minions [area]` [Alias: `{PREFIX}m`]
Sends the map for `area`'s minions when invoked.""", inline=False)  # Lists all of the Hunting module's commands and
        # their invocation examples.
        embed.add_field(name="Verification", value=f"""`{PREFIX}id_link [lodestone_id]` [Alias: `{PREFIX}id`]
Links, via ID, your FFXIV character to your Discord name. This process may take up to one minute.

`{PREFIX}info` [Alias: `{PREFIX}i`]
Shows your character information. Mention another user to view theirs.

`{PREFIX}link [first_name] [last_name] [world_name]` [Alias: `{PREFIX}l`]
Links your FFXIV character to your Discord name. This process may take up to one minute.

`{PREFIX}unlink` [Alias: `{PREFIX}ul`]
Deletes the current user's character information from the database.""", inline=False)  # Lists all of the Verification
        # module's commands and their invocation examples.
        embed.set_footer(text=f"""To have the bot's help PM'd to you, put -pm after the command (eg. {PREFIX}help -pm) |
Current version: {VERSION} |
Made by Dusk Argentum#6530. |
Profile picture by Toast! Find them at https://twitter.com/pixel__toast""")  # Sets the footer.
        await ctx.send(embed=embed)  # Sends the defined embed.
        return
    else:  # Functions in this block execute if a subcommand is passed.
        pass  # Moves along.


@help_.command(pass_context=True, name="-pm")  # This is invoked if the -pm subcommand is issued, eg. !help -pm.
async def pm(ctx):  # Everything else is the same.
    """PMs the help message to the invoker."""
    random_color = random.randint(1, 16777215)
    embed = discord.Embed(title="Mudbot Commands", color=discord.Color(int(random_color)))
    embed.add_field(name="Hunting", value=f"""`{PREFIX}fate [fate]` [Alias: `{PREFIX}f`]
Sends the information for the specified `fate` when invoked.

`{PREFIX}minions [area]` [Alias: `{PREFIX}m`]
Sends the map for `area`'s minions when invoked.""", inline=False)  # Lists all of the Hunting module's commands and
    # their invocation examples.
    embed.add_field(name="Verification", value=f"""`{PREFIX}id_link [lodestone_id]` [Alias: `{PREFIX}id`]
Links, via ID, your FFXIV character to your Discord name. This process may take up to one minute.

`{PREFIX}info` [Alias: `{PREFIX}i`]
Shows your character information. Mention another user to view theirs.

`{PREFIX}link [first_name] [last_name] [world_name]` [Alias: `{PREFIX}l`]
Links your FFXIV character to your Discord name. This process may take up to one minute.

`{PREFIX}unlink` [Alias: `{PREFIX}ul`]
Deletes the current user's character information from the database.""", inline=False)
    embed.set_footer(text=f"""To have the bot's help PM'd to you, put -pm after the command (eg. {PREFIX}help -pm) |
Current version: {VERSION} |
Made by Dusk Argentum#6530. |
Profile picture by Toast! Find them at https://twitter.com/pixel__toast""")  # Sets the footer.
    await ctx.send(embed=embed)
    return


# HUNT COMMANDS: These commands help generally facilitate The Hunt.


FATE_AUTHOR_ICON_URL = "http://ffxiv.gamerescape.com/w/images/1/11/Map65_Icon.png"  # Defines the URL for the
# FATE icon for use in the set_author icon_url argument.
FATE_COLOR = 0xff00fb  # Defines the color for the embed for use in the discord.Embed color argument.
FATE_FOOTER_ICON_URL = "https://i.imgur.com/z2e4PYk.png"  # Defines the URL for the RetahGaming icon for use in the
# set_footer icon_url argument.


@bot.group(name=f"fate", aliases=[f"f"], case_insensitive=True)  # Defines the fate command.
async def fate(ctx):
    """Sends the information for `fate` when invoked."""
    if ctx.invoked_subcommand is None:
        embed = discord.Embed(title=f"FATEs", description=f"""Whether it be a renowned beast from Final Fantasy's \
lore, or a creature from myths and legends, Final Fantasy XIV is host to a number of FATEs that can be undertaken \
by players of varying strengths and experience levels to achieve great rewards. These aforementioned FATEs are \
listed below.
For more information on a specific FATE, use `{PREFIX}fate`, followed by the name of the creature fought within, eg. \
`{PREFIX}fate ixion`.""", color=FATE_COLOR)  # The flavor
        # is unnecessary, but I'm keeping it. My bot, my rules, I wrote it myself.
        embed.set_author(name=f"FATE Information", icon_url=FATE_AUTHOR_ICON_URL)  # Sets the "author" and the icon
        # of the author to be a custom name and icon.
        embed.set_thumbnail(url=FATE_AUTHOR_ICON_URL)  # Sets the thumbnail to be a typical FATE icon.
        embed.add_field(name=f"A Realm Reborn (2.0)", value=f"""[Behemoth](https://ffxiv.gamerescape.com/wiki/Behemoth) \
| [He Taketh It With His Eyes](https://ffxiv.gamerescape.com/wiki/He_Taketh_It_with_His_Eyes) \
| `{PREFIX}fate behemoth`
[Odin](https://ffxiv.gamerescape.com/wiki/Odin) \
| [Steel Reign](https://ffxiv.gamerescape.com/wiki/Steel_Reign) \
| `{PREFIX}fate odin`""", inline=False)  # Defines the field of ARR FATEs.
        embed.add_field(name=f"Heavensward (3.0)", value=f"""[Coeurlregina](https://ffxiv.gamerescape.com/wiki/Coeurlregina) \
| [Coeurls Chase Boys Chase Coeurls](https://ffxiv.gamerescape.com/wiki/Coeurls_Chase_Boys_Chase_Coeurls) \
| `{PREFIX}fate coeurl`
[Proto Ultima](https://ffxiv.gamerescape.com/wiki/Prey_Online) \
| [Prey Online](https://ffxiv.gamerescape.com/wiki/Prey_Online) \
| `{PREFIX}fate ultima`""", inline=False)  # Defines the field of HW FATEs.
        embed.add_field(name=f"Stormblood (4.0)", value=f"""[Tamamo Gozen](https://ffxiv.gamerescape.com/wiki/Tamamo_Gozen) \
| [Foxy Lady](https://ffxiv.gamerescape.com/wiki/Foxy_Lady) \
| `{PREFIX}fate foxy`
[Ixion](https://ffxiv.gamerescape.com/wiki/Ixion) \
| [A Horse Outside](https://ffxiv.gamerescape.com/wiki/A_Horse_Outside) \
| `{PREFIX}fate ixion`""", inline=False)  # Defines the field of SB FATEs.
        embed.add_field(name=f"Shadowbringers (5.0)", value=f"""[Archaeotania](https://ffxiv.gamerescape.com/wiki/Archaeotania) \
| [The Head, The Tail, The Whole Damned Thing](https://ffxiv.gamerescape.com/wiki/The_Head,_the_Tail,_the_Whole_Damned_Thing) \
| `{PREFIX}fate arch`
[Formidable](https://ffxiv.gamerescape.com/wiki/Formidable) \
| [A Finale Most Formidable](https://ffxiv.gamerescape.com/wiki/A_Finale_Most_Formidable) \
| `{PREFIX}fate formidable`""", inline=False)  # Defines the field of ShB FATEs.
        embed.set_footer(text=f"Maps courtesy of RetahGaming.com", icon_url=FATE_FOOTER_ICON_URL)  # Sets the footer
        # crediting Retah and using their site icon.
        await ctx.send(embed=embed)
        return
    else:
        pass


@fate.command(name=f"archaeotania", aliases=[f"arch", f"archae"])
# A lot of the comments for the embeds would be the same, so I'm not doing them. Just read the fate command's comments.
async def archaeotania(ctx):
    embed = discord.Embed(title=f"The Tempest | Level 80 FATE", description=f"""Drawn by the scent of sanguine \
coral, Archaeotania finally shows itself. The time has come to end its reign of terror once and for all.""",
                          color=FATE_COLOR)
    embed.set_author(name=f"The Head, The Tail, The Whole Damned Thing", icon_url=FATE_AUTHOR_ICON_URL)
    embed.set_thumbnail(url=f"https://i.imgur.com/H5jaoaf.png")
    embed.add_field(name=f"Spawn Timer", value=f"Every 24-48 Hours", inline=True)
    embed.add_field(name=f"Rewards", value=f"""**Gold** | 6x [Archaeotania's Horn](https://ffxiv.gamerescape.com/wiki/Archaeotania%27s_Horn)
**Silver** | 4x [Archaeotania's Horn](https://ffxiv.gamerescape.com/wiki/Archaeotania%27s_Horn)
**Bronze** | 2x [Archaeotania's Horn](https://ffxiv.gamerescape.com/wiki/Archaeotania%27s_Horn)""", inline=True)
    embed.add_field(name=f"Preceding FATEs", value=f"""**Stage 1** | [Where Has the Dagon](https://ffxiv.gamerescape.com/wiki/Where_Has_the_Dagon)
**Stage 2** | [Ondo of Blood](https://ffxiv.gamerescape.com/wiki/Ondo_of_Blood)
**Stage 3** | [Lookin' Back on the Track](https://ffxiv.gamerescape.com/wiki/Lookin%27_Back_on_the_Track)
**Stage 4** | [Coral Support](https://ffxiv.gamerescape.com/wiki/Coral_Support)
**Stage 5** | [Low Coral Fiber](https://ffxiv.gamerescape.com/wiki/Low_Coral_Fiber)
**Stage 6** | [Nothing Like a Trappin' Life](https://ffxiv.gamerescape.com/wiki/Nothing_Like_a_Trappin%27_Life)""",
                    inline=False)
    embed.set_image(url=f"https://www.retahgaming.com/ffxiv/images/shfull/archaeotania.gif")
    embed.set_footer(text=f"Map courtesy of RetahGaming.com", icon_url=FATE_FOOTER_ICON_URL)
    await ctx.send(embed=embed)
    return


@fate.group(name=f"behemoth", aliases=[f"behe"])
async def behemoth(ctx):
    embed = discord.Embed(title=f"Coerthas Central Highlands | Level 50 FATE", description=f"""The behemoth has \
taken flight back to its dominion. Make chase and finish the legendary beast once and for all.""", color=FATE_COLOR)
    embed.set_author(name=f"He Taketh It With His Eyes", icon_url=FATE_AUTHOR_ICON_URL)
    embed.set_thumbnail(url=f"https://i.imgur.com/avNA34m.png")
    embed.add_field(name=f"Spawn Timer", value=f"Every 24-72 Hours", inline=True)
    embed.add_field(name=f"Rewards", value=f"""**Gold** | 5x [Behemoth Horn](https://ffxiv.gamerescape.com/wiki/Behemoth_Horn)
**Silver** | 1x [Behemoth Horn](https://ffxiv.gamerescape.com/wiki/Behemoth_Horn)""", inline=True)
    embed.add_field(name=f"Preceding FATE", value=f"[Behold Now Behemoth](https://ffxiv.gamerescape.com/wiki/Behold_Now_Behemoth)",
                    inline=False)
    embed.set_image(url=f"https://www.retahgaming.com/ffxiv/images/arrfull/behemoth.gif")
    embed.set_footer(text=f"Map courtesy of RetahGaming.com", icon_url=FATE_FOOTER_ICON_URL)
    await ctx.send(embed=embed)
    return


@fate.group(name=f"coeurlregina", aliases=[f"coeurl"])
async def coeurlregina(ctx):
    embed = discord.Embed(title=f"The Dravanian Forelands | Level 60 FATE", description=f"""Her main offensive a \
tactical failure, Coeurlregina has sounded the retreat. However, if allowed the luxury of escape, it will only be a \
matter of time before the wicked beast is conspiring another assault. Make chase, and end the queen's reign here and \
now.""", color=FATE_COLOR)
    embed.set_author(name=f"Coeurls Chase Boys Chase Coeurls", icon_url=FATE_AUTHOR_ICON_URL)
    embed.set_thumbnail(url="https://i.imgur.com/hAxM2wM.png")
    embed.add_field(name=f"Spawn Timer", value=f"""**Stage 1** | 24-48 Hours after Stage 3 (or failure)
**Stage 2** | 2-12 Hours after Stage 1
**Stage 3** | 4 Hours after Stage 2""", inline=True)
    embed.add_field(name=f"Rewards", value=f"""**Stage 1** | 1x [Coeurlregina Horn](https://ffxiv.gamerescape.com/wiki/Coeurlregina_Horn)
**Stage 2** | 3x [Coeurlregina Horn](https://ffxiv.gamerescape.com/wiki/Coeurlregina_Horn)
**Stage 3** | 5x [Coeurlregina Horn](https://ffxiv.gamerescape.com/wiki/Coeurlregina_Horn)""", inline=True)
    embed.add_field(name=f"Weather", value=f"<:RoyalLevin:873825058718625833> Royal Levin", inline=True)
    embed.add_field(name=f"Preceding FATEs", value=f"""**Stage 1** | [Long Live the Coeurl](https://ffxiv.gamerescape.com/wiki/Long_Live_the_Coeurl)
**Stage 2** | [Coeurls Chase Boys](https://ffxiv.gamerescape.com/wiki/Coeurls_Chase_Boys)""", inline=False)
    embed.set_image(url=f"https://www.retahgaming.com/ffxiv/images/hwfull/coeurlregina.gif")
    embed.set_footer(text=f"Map courtesy of RetahGaming.com", icon_url=FATE_FOOTER_ICON_URL)
    await ctx.send(embed=embed)
    return


@fate.group(name=f"formidable", aliases=[f"formid", f"form"])
async def formidable(ctx):
    embed = discord.Embed(title=f"Kholusia | Level 80 FATE", description=f"""It appears that the Goggs have been \
secretly engineering a massive new automaton capable of thwacking and throttling on a scale heretofore unheard of. Put \
an end to the malevolent machina by doing a little thwacking and/or throttling of your own.""", color=FATE_COLOR)
    embed.set_author(name=f"A Finale Most Formidable", icon_url=FATE_AUTHOR_ICON_URL)
    embed.set_thumbnail(url=f"https://i.imgur.com/3l2iaGB.png")
    embed.add_field(name=f"Spawn Timer", value=f"Every 24-48 Hours", inline=True)
    embed.add_field(name=f"Rewards", value=f"""**Gold** | 6x [Formidable Cog](https://ffxiv.gamerescape.com/wiki/Formidable_Cog)
**Silver** | 4x [Formidable Cog](https://ffxiv.gamerescape.com/wiki/Formidable_Cog)
**Bronze** | 2x [Formidable Cog](https://ffxiv.gamerescape.com/wiki/Formidable_Cog)""", inline=True)
    embed.add_field(name=f"Preceding FATEs", value=f"""**Stage 1a** | [Ironbeard Builders - Resist](https://ffxiv.gamerescape.com/wiki/Ironbeard_Builders_-_Resist)
**└►Stage 1b** | [Ironbeard Builders - Revolt](https://ffxiv.gamerescape.com/wiki/Ironbeard_Builders_-_Revolt)
**└►Stage 1c** | [Ironbeard Builders - Rebuilt](https://ffxiv.gamerescape.com/wiki/Ironbeard_Builders_-_Rebuilt)
**Stage 2a** | [Foes Most Formidable](https://ffxiv.gamerescape.com/wiki/Foes_Most_Formidable)
**└►Stage 2b** | [A Family Most Formidable](https://ffxiv.gamerescape.com/wiki/A_Family_Most_Formidable)""",
                    inline=False)
    embed.set_image(url=f"https://www.retahgaming.com/ffxiv/images/shfull/formidable.gif")
    embed.set_footer(text=f"Map courtesy of RetahGaming.com", icon_url=FATE_FOOTER_ICON_URL)
    await ctx.send(embed=embed)
    return


@fate.command(name=f"foxy", aliases=[f"foxylady", f"tamamogozen"])
async def foxy(ctx):
    embed = discord.Embed(title=f"Yanxia | Level 70 FATE", description=f"""Upon capture by a wicked Hingan onmyoji, \
the nine-tailed fox spirit slumbering deep within the young maiden Mikuzume awakens. Now, the only way to stop the \
legendary Tamamo Gozen is with an excessive display of force.""", color=FATE_COLOR)
    embed.set_author(name=f"Foxy Lady", icon_url=FATE_AUTHOR_ICON_URL)
    embed.set_thumbnail(url="https://i.imgur.com/2c2f5hm.png")
    embed.add_field(name=f"Spawn Timer", value=f"Every 12-48 Hours", inline=True)
    embed.add_field(name=f"Rewards", value=f"""**Gold** | 15 [Sassho-seki Fragment](https://ffxiv.gamerescape.com/wiki/Sassho-seki_Fragment)
**Silver** | 6x [Sassho-seki Fragment](https://ffxiv.gamerescape.com/wiki/Sassho-seki_Fragment)""", inline=True)
    embed.add_field(name=f"Preceding FATEs", value=f"""**Stage 1a** | [More to Offer](https://ffxiv.gamerescape.com/wiki/More_to_Offer)
**└►Stage 1b** | [Freedom Flies](https://ffxiv.gamerescape.com/wiki/Freedom_Flies)
**Stage 2** | [Outfoxed](https://ffxiv.gamerescape.com/wiki/Outfoxed)""", inline=False)
    embed.set_image(url=f"https://www.retahgaming.com/ffxiv/images/sbfull/foxylady.gif")
    embed.set_footer(text="Map courtesy of RetahGaming.com", icon_url=FATE_FOOTER_ICON_URL)
    await ctx.send(embed=embed)
    return


@fate.command(name=f"ixion", aliases=[f"ix"])
async def ixion(ctx):
    embed = discord.Embed(title=f"The Lochs | Level 70 FATE", description=f"""It is said on a mighty levinbolt \
doth the warsteed Ixion ride─thunder, the rumbling of his hooves as they pound the very heavens. Ware the coming \
storm, for hell descendeth.""", color=FATE_COLOR)
    embed.set_author(name=f"A Horse Outside", icon_url=FATE_AUTHOR_ICON_URL)
    embed.set_thumbnail(url=f"https://i.imgur.com/E6gPeQF.png")
    embed.add_field(name=f"Spawn Timer", value=f"Every 18-36 Hours", inline=True)
    embed.add_field(name=f"Rewards", value=f"""**Gold** | 6x [Ixion Horn](https://ffxiv.gamerescape.com/wiki/Ixion_Horn)
**Silver** | 3x [Ixion Horn](https://ffxiv.gamerescape.com/wiki/Ixion_Horn)""", inline=True)
    embed.add_field(name=f"Weather", value=f"<:Quicklevin:873820437254135838> Quicklevin", inline=True)
    embed.set_image(url=f"https://www.retahgaming.com/ffxiv/images/sbfull/ixion.gif")
    embed.set_footer(text=f"Map courtesy of RetahGaming.com", icon_url=FATE_FOOTER_ICON_URL)
    await ctx.send(embed=embed)
    return


@fate.command(name=f"odin", aliases=[f"od"])
async def odin(ctx):
    embed = discord.Embed(title=f"The Black Shroud | Level 50 FATE", description=f"""Atop his mighty steed, clad in \
armor darker than the void, the elder primal Odin has returned to Eorzea to exact his brutal judgment upon the \
realm.""", color=FATE_COLOR)
    embed.set_author(name=f"Steel Reign", icon_url=FATE_AUTHOR_ICON_URL)
    embed.set_thumbnail(url=f"https://i.imgur.com/bRTLdKO.png")
    embed.add_field(name=f"Spawn Timer", value=f"Every 24-72 Hours", inline=True)
    embed.add_field(name=f"Rewards", value=f"""**Gold** | 5x [Odin's Mantle](https://ffxiv.gamerescape.com/wiki/Odin%27s_Mantle)
**Silver** | 1x [Odin's Mantle](https://ffxiv.gamerescape.com/wiki/Odin%27s_Mantle)""", inline=True)
    embed.add_field(name=f"Weather", value=f"""<:Tension:873826604063813633> Tension""", inline=True)
    embed.set_image(url=f"https://www.retahgaming.com/ffxiv/images/arrfull/odin.gif")
    embed.set_footer(text=f"Map courtesy of RetahGaming.com", icon_url=FATE_FOOTER_ICON_URL)
    await ctx.send(embed=embed)
    return


@fate.command(name=f"ultima", aliases=[f"proto-ultima"])
async def ultima(ctx):
    embed = discord.Embed(title=f"Azys Lla | Level 59 FATE", description=f"""After five millennia offline, Proto \
Ultima has restored auxiliary power and begun a full systems check. To recharge its main power cells, the Allagan \
killing machine has deployed several aether collectors guarded by some of the most frightening of the fallen \
empire's godless creations.""", color=FATE_COLOR)
    embed.set_author(name=f"Prey Online", icon_url=FATE_AUTHOR_ICON_URL)
    embed.add_field(name=f"Spawn Timer", value=f"Every 34-48 Hours", inline=True)
    embed.add_field(name=f"Rewards", value=f"""**Gold** | 3x [Proto Ultima Exoplating](https://ffxiv.gamerescape.com/wiki/Proto_Ultima_Exoplating)
**Silver** | 2x [Proto Ultima Exoplating](https://ffxiv.gamerescape.com/wiki/Proto_Ultima_Exoplating)
**Bronze** | 1x [Proto Ultima Exoplating](https://ffxiv.gamerescape.com/wiki/Proto_Ultima_Exoplating)""", inline=True)
    embed.add_field(name=f"Weather", value=f"<:Hyperelectricity:873819536477028372> Hyperelectricity", inline=True)
    embed.set_image(url=f"https://www.retahgaming.com/ffxiv/images/hwfull/preyonline.gif")
    embed.set_footer(text=f"Map courtesy of RetahGaming.com", icon_url=FATE_FOOTER_ICON_URL)
    await ctx.send(embed=embed)
    return


@bot.group(pass_context=True, name="minions", aliases=["m"], case_insensitive=True)  # This defines a group of commands, so that subcommands
# can be used.
async def minions(ctx):
    """Sends the map for `area`'s minions when invoked."""
    if ctx.invoked_subcommand is None:  # Functions in this block execute if there is no invoked subcommand. In this
        # case, if no area is mentioned when running the command.
        await ctx.send("""Please enter a valid area! Valid areas:
`Amh Araeng` (`AA`), `Il Mheg` (`IL`),
`Kholusia` (`KH`), `Lakeland` (`LL`),
`Rak'Tika` (`RT`), `Tempest` (`TM`)""")
        return
    else:
        return


@minions.command(pass_context=True, name="amh araeng", aliases=["aa", "amharaeng"])  # This defines a subcommand of
# the minions command.
async def amh_araeng(ctx):  # Functions in this block execute if the invoked subcommand of the minions command is
    # Amh Araeng.
    """Sends the map for Amh Araeng's minions when invoked."""
    allowed_channels = [int("732488105981902858"), int("579740817896374284")]  # Defines a list of allowed channels
    # that the command can be executed in.
    if ctx.guild.id == 542602456132091904:  # Functions in this block execute if the guild the command is invoked on is
        # Aether Hunts.
        if ctx.channel.id in allowed_channels:  # Allows the command to complete running if the command is invoked
            # in one of the channels in allowed_channels.
            pass
        elif ctx.channel.id not in allowed_channels:  # Stops the command from running if the channel is not in
            # allowed_channels.
            await ctx.send("This command cannot be invoked here! Please invoke it in <#579740817896374284>.")
            return
    elif ctx.guild.id != 542602456132091904:  # Functions in this block execute if the guild the command is invoked on
        # is not Aether Hunts, for testing purposes.
        pass
    embed = discord.Embed(title="The minions of an extraordinarily powerful mark are on the hunt for prey.",
                          color=discord.Color(0xd93070))  # Defines an embed, and the parts of the embed are defined
    # below.
    embed.add_field(name="Minions:", value="""`X-14, Y-32` | `X-13, Y-12`
`X-30, Y-10` | `X-30, Y-25`""", inline=False)
    embed.add_field(name="Forgiven Rebellion:", value="`X-27, Y-35`", inline=False)
    embed.add_field(name="Called By:", value=f"{ctx.author.mention}")
    embed.add_field(name="World:", value="Please see previous post for world name.", inline=False)
    embed.add_field(name="Map:",
                    value="** **", inline=False)
    embed.set_image(url="https://www.retahgaming.com/ffxiv/images/shfull/ahmssfull.jpg")
    embed.set_footer(text="""Map courtesy of: Retah Sosshaa of Midgardsormr
https://www.retahgaming.com/ffxiv/forgivenrebellion.html""")
    embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/740603224826052608/740754471575093369/Minion.png")
    await ctx.send(content="""<:minion:610656093680697366> <:minion:610656093680697366> \
<@&570459958123167745> <:minion:610656093680697366> <:minion:610656093680697366>""", embed=embed)  # This program
    # should not have been tainted by Minions...
    return


@minions.command(pass_context=True, name="il mheg", aliases=["il", "ilmheg"])  # The above comments for Amh Araeng
# all apply to the below functions.
async def il_mheg(ctx):
    """Sends the map for Il Mheg's minions when invoked."""
    allowed_channels = [int("732488105981902858"), int("579740817896374284")]
    if ctx.guild.id == 542602456132091904:
        if ctx.channel.id in allowed_channels:
            pass
        elif ctx.channel.id not in allowed_channels:
            await ctx.send("This command cannot be invoked here! Please invoke it in <#579740817896374284>.")
            return
    elif ctx.guild.id != 542602456132091904:
        pass
    embed = discord.Embed(title="The minions of an extraordinarily powerful mark are on the hunt for prey.",
                          color=discord.Color(0xd93070))
    embed.add_field(name="Minions:", value="""`X-06, Y-30` | `X-32, Y-11`
`X-25, Y-22` | `X-24, Y-37`""", inline=False)
    embed.add_field(name="Forgiven Rebellion:", value="`X-13, Y-23`", inline=False)
    embed.add_field(name="Called By:", value=f"{ctx.author.mention}")
    embed.add_field(name="World:", value="Please see previous post for world name.", inline=False)
    embed.add_field(name="Map:", value="** **", inline=False)
    embed.set_image(url="https://www.retahgaming.com/ffxiv/images/shfull/mhegssfull.jpg")
    embed.set_footer(text="""Map courtesy of: Retah Sosshaa of Midgardsormr
https://www.retahgaming.com/ffxiv/forgivenrebellion.html""")
    embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/740603224826052608/740754471575093369/Minion.png")
    await ctx.send(content="""<:minion:610656093680697366> <:minion:610656093680697366> \
<@&570459958123167745> <:minion:610656093680697366> <:minion:610656093680697366>""", embed=embed)
    return


@minions.command(pass_context=True, name="kholusia", aliases=["kh", "kho", "khol"])
async def kholusia(ctx):
    """Sends the map for Kholusia's minions when invoked."""
    allowed_channels = [int("732488105981902858"), int("579740817896374284")]
    if ctx.guild.id == 542602456132091904:
        if ctx.channel.id in allowed_channels:
            pass
        elif ctx.channel.id not in allowed_channels:
            await ctx.send("This command cannot be invoked here! Please invoke it in <#579740817896374284>.")
            return
    elif ctx.guild.id != 542602456132091904:
        pass
    embed = discord.Embed(title="The minions of an extraordinarily powerful mark are on the hunt for prey.",
                          color=discord.Color(0xd93070))
    embed.add_field(name="Minions:", value="""`X-08, Y-29` | `X-12, Y-15`
`X-23, Y-15` | `X-33, Y-32`""", inline=False)
    embed.add_field(name="Forgiven Rebellion:", value="`X-24, Y-37`", inline=False)
    embed.add_field(name="Called By:", value=f"{ctx.author.mention}")
    embed.add_field(name="World:", value="Please see previous post for world name.", inline=False)
    embed.add_field(name="Map:", value="** **", inline=False)
    embed.set_image(url="https://www.retahgaming.com/ffxiv/images/shfull/kholusiassfull.jpg")
    embed.set_footer(text="""Map courtesy of: Retah Sosshaa of Midgardsormr
https://www.retahgaming.com/ffxiv/forgivenrebellion.html""")
    embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/740603224826052608/740754471575093369/Minion.png")
    await ctx.send(content="""<:minion:610656093680697366> <:minion:610656093680697366> \
<@&570459958123167745> <:minion:610656093680697366> <:minion:610656093680697366>""", embed=embed)
    return


@minions.command(pass_context=True, name="lakeland", aliases=["ll", "lake"])
async def lakeland(ctx):
    """Sends the map for Lakeland's minions when invoked."""
    allowed_channels = [int("732488105981902858"), int("579740817896374284")]
    if ctx.guild.id == 542602456132091904:
        if ctx.channel.id in allowed_channels:
            pass
        elif ctx.channel.id not in allowed_channels:
            await ctx.send("This command cannot be invoked here! Please invoke it in <#579740817896374284>.")
            return
    elif ctx.guild.id != 542602456132091904:
        pass
    embed = discord.Embed(title="The minions of an extraordinarily powerful mark are on the hunt for prey.",
                          color=discord.Color(0xd93070))
    embed.add_field(name="Minions:", value="""`X-10, Y-25` | `X-13, Y-10`
`X-33, Y-12` | `X-30, Y-36`""", inline=False)
    embed.add_field(name="Forgiven Rebellion:", value="`X-23, Y-22`", inline=False)
    embed.add_field(name="Called By:", value=f"{ctx.author.mention}")
    embed.add_field(name="World:", value="Please see previous post for world name.", inline=False)
    embed.add_field(name="Map:", value="** **", inline=False)
    embed.set_image(url="https://www.retahgaming.com/ffxiv/images/shfull/lakelandssfull.jpg")
    embed.set_footer(text="""Map courtesy of: Retah Sosshaa of Midgardsormr
https://www.retahgaming.com/ffxiv/forgivenrebellion.html""")
    embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/740603224826052608/740754471575093369/Minion.png")
    await ctx.send(content="""<:minion:610656093680697366> <:minion:610656093680697366> \
<@&570459958123167745> <:minion:610656093680697366> <:minion:610656093680697366>""", embed=embed)
    return


@minions.command(pass_context=True, name="rak'tika", aliases=["rt", "rak"])
async def rak_tika(ctx):
    """Sends the map for Rak'Tika's minions when invoked."""
    allowed_channels = [int("732488105981902858"), int("579740817896374284")]
    if ctx.guild.id == 542602456132091904:
        if ctx.channel.id in allowed_channels:
            pass
        elif ctx.channel.id not in allowed_channels:
            await ctx.send("This command cannot be invoked here! Please invoke it in <#579740817896374284>.")
            return
    elif ctx.guild.id != 542602456132091904:
        pass
    embed = discord.Embed(title="The minions of an extraordinarily powerful mark are on the hunt for prey.",
                          color=discord.Color(0xd93070))
    embed.add_field(name="Minions:", value="""`X-15, Y-36` | `X-08, Y-22`
`X-19, Y-22` | `X-30, Y-13`""", inline=False)
    embed.add_field(name="Forgiven Rebellion:", value="`X-24, Y-37`", inline=False)
    embed.add_field(name="Called By:", value=f"{ctx.author.mention}")
    embed.add_field(name="World:", value="Please see previous post for world name.", inline=False)
    embed.add_field(name="Map:", value="** **", inline=False)
    embed.set_image(url="https://www.retahgaming.com/ffxiv/images/shfull/greatwoodssfull.jpg")
    embed.set_footer(text="""Map courtesy of: Retah Sosshaa of Midgardsormr
https://www.retahgaming.com/ffxiv/forgivenrebellion.html""")
    embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/740603224826052608/740754471575093369/Minion.png")
    await ctx.send(content="""<:minion:610656093680697366> <:minion:610656093680697366> \
<@&570459958123167745> <:minion:610656093680697366> <:minion:610656093680697366>""", embed=embed)
    return


@minions.command(pass_context=True, name="tempest", aliases=["tm", "tmp"])
async def tempest(ctx):
    """Sends the map for Tempest's minions when invoked."""
    allowed_channels = [int("732488105981902858"), int("579740817896374284")]
    if ctx.guild.id == 542602456132091904:
        if ctx.channel.id in allowed_channels:
            pass
        elif ctx.channel.id not in allowed_channels:
            await ctx.send("This command cannot be invoked here! Please invoke it in <#579740817896374284>.")
            return
    elif ctx.guild.id != 542602456132091904:
        pass
    embed = discord.Embed(title="The minions of an extraordinarily powerful mark are on the hunt for prey.",
                          color=discord.Color(0xd93070))
    embed.add_field(name="Minions:", value="""`X-08, Y-07` | `X-26, Y-09`
`X-38, Y-14` | `X-34, Y-30`""", inline=False)
    embed.add_field(name="Forgiven Rebellion:", value="`X-13, Y-22`", inline=False)
    embed.add_field(name="Called By:", value=f"{ctx.author.mention}")
    embed.add_field(name="World:", value="Please see previous post for world name.", inline=False)
    embed.add_field(name="Map:", value="** **", inline=False)
    embed.set_image(url="https://www.retahgaming.com/ffxiv/images/shfull/tempestssfull.jpg")
    embed.set_footer(text="""Map courtesy of: Retah Sosshaa of Midgardsormr
https://www.retahgaming.com/ffxiv/forgivenrebellion.html""")
    embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/740603224826052608/740754471575093369/Minion.png")
    await ctx.send(content="""<:minion:610656093680697366> <:minion:610656093680697366> \
<@&570459958123167745> <:minion:610656093680697366> <:minion:610656093680697366>""", embed=embed)
    return


# ! GATED COMMANDS: These commands can only be run by specific people or people with specific roles.
# Commands that apply to multiple roles are listed in the lowest required role.


# OWNER ONLY:


@bot.command(pass_context=True, name="delete_echo", aliases=["de"])  # Defines the delete_echo command.
async def delete_echo(ctx, *args):
    """OWNER ONLY. Echoes back what the owner says while deleting the invocation."""
    if ctx.author.id != 97153790897045504:  # This block stops the command from executing the the invoker's id
        # does not match the owner's.
        return
    elif ctx.author.id == 97153790897045504:
        await ctx.send(" ".join(args))
        await ctx.message.delete()
        return


@bot.command(pass_context=True, name="invite")  # Defines the invite command.
async def invite(ctx):
    """OWNER ONLY. Sends the owner an invite link for Mudbot."""
    invite = os.environ.get("Mudbot_Invite")  # Gets the Mudbot invite link from the system's environmental variables.
    if ctx.author.id != 97153790897045504:
        return
    elif ctx.author.id == 97153790897045504:
        await ctx.author.send(f"{invite}")
        await ctx.message.delete()
        return


@bot.command(pass_context=True, name="leave")  # Defines the leave command.
async def leave(ctx, server: int = None):
    """OWNER ONLY. Leaves the provided server."""
    if ctx.author.id != 97153790897045504:
        return
    elif ctx.author.id == 97153790897045504:
        if server is None:  # Functions in this block execute if there is nothing passed to the server argument.
            server_to_leave = bot.get_guild(ctx.guild.id)
            await server_to_leave.leave()
            await ctx.author.send("I have left the server.")
            return
        elif server is not None:  # Functions in this block execute if there is a server id passed to the argument.
            server_to_leave = bot.get_guild(server)
            await ctx.author.send(f"I have left {server_to_leave.name} ({server}).")
            await server_to_leave.leave()
            return


@bot.command(pass_context=True, name="status", aliases=["s"])  # Defines the status command.
async def status(ctx, *, activity: str = None):
    """OWNER ONLY. Changes the bot's status."""
    if ctx.author.id != 97153790897045504:
        return
    elif ctx.author.id == 97153790897045504:
        global SHOULD_STATUS_CHANGE  # Imports the SHOULD_STATUS_CHANGE global variable. Only necessary because
        # this command possibly edits the variable.
        if activity is None:  # Functions in this block execute if there is nothing passed to the activity argument.
            if SHOULD_STATUS_CHANGE == 0:
                SHOULD_STATUS_CHANGE = 1  # Sets the status_rotation task in motion again once it loops to checking.
                pass
            elif SHOULD_STATUS_CHANGE == 1:  # Essentially error handling.
                pass
            status_rotation.start()  # Starts the status_rotation task again.
            return
        elif activity is not None:  # Functions in this block execute if there is something passed to the argument.
            if SHOULD_STATUS_CHANGE == 0:  # Essentially error handling.
                pass
            elif SHOULD_STATUS_CHANGE == 1:
                SHOULD_STATUS_CHANGE = 0  # Informs the status_rotation task that it should not execute.
                pass
            status_rotation.cancel()  # Stops the status_rotation task in its tracks.
            await bot.change_presence(status=discord.Status.online, activity=discord.Game(f"{activity} | +help"))
            # Sets the status as whatever was within the activity argument.
            return


@bot.command(pass_context=True, name="server_list", aliases=["sl"])  # Defines the server_list command.
async def server_list(ctx):
    """OWNER ONLY. Gets the list of all servers the bot is connected to, for the reason of leaving unauthorized servers."""
    if ctx.author.id != 97153790897045504:
        return
    elif ctx.author.id == 97153790897045504:
        for guild in bot.guilds:  # This block loops, and sends each server's name and ID to the command invoker
            # in separate messages, while waiting 1 second between each for rate-limiting reasons.
            await ctx.author.send(f"{guild.name} ({guild.id})")
            await asyncio.sleep(1)
        return
    # I foresee this becoming a possible point of contention, so let me be clear: The reason this command exists
    # is so that I know if the bot is on a server it should not be on. It does not send me any additional information
    # beyond the server's name and id. No individual identifying information is sent.


# ADMIN ONLY:


@bot.group(name="autoban", aliases=["ab"], case_insensitive=True)  # This defines the autoban command group.
@has_role(551968333008732169)
async def autoban(ctx):
    if ctx.invoked_subcommand is None:
        await ctx.send("No argument specified. Acceptable arguments: `on`, `off`, `threshold`.")
        return
    else:
        pass


@autoban.command(name="on", aliases=["y", "1", "enabled", "true", "yes"])
@has_role(551968333008732169)
async def on(ctx):
    with open("auto_punish_info.json", "r+") as auto_punish_info:  # Opens the auto_punish_info file.
        data = json.load(auto_punish_info)  # Loads the json of the auto_punish_info file.
        status_update = {"enabled": "true"}  # Updates the status.
        data["auto_punish_info"]["ban"].update(status_update)  # Updates the JSON object.
        auto_punish_info.seek(0)  # Goes back to the top of the file.
        json.dump(data, auto_punish_info, indent=2)  # Writes the update to the auto_punish_info file.
        auto_punish_info.truncate()  # Things break if this doesn't exist and the file contents have more or less
        # characters than before.
        auto_punish_info.close()  # Closes the auto_punish_info file.
    await ctx.message.add_reaction("👍")
    return


@autoban.command(name="off", aliases=["n", "0", "disabled", "false", "no"])  # The rest of the autoban/autokick toggle
# commands are essentially as the one above.
@has_role(551968333008732169)
async def off(ctx):
    with open("auto_punish_info.json", "r+") as auto_punish_info:
        data = json.load(auto_punish_info)
        status_update = {"enabled": "false"}
        data["auto_punish_info"]["ban"].update(status_update)
        auto_punish_info.seek(0)
        json.dump(data, auto_punish_info, indent=2)
        auto_punish_info.truncate()
        auto_punish_info.close()
    await ctx.message.add_reaction("👍")
    return


@autoban.command(name="threshold", aliases=["age"])
@has_role(551968333008732169)
async def threshold(ctx, threshold: str = None):
    threshold_check = re.search(r"(^\d{1,2})(m$|h$|d$)", threshold, re.IGNORECASE)
    if threshold_check is None:
        await ctx.send(f"""Invalid threshold. Please supply a threshold by putting an amount of minutes, hours, or days.
Example: `{PREFIX}autoban threshold 12h` for 12 hours or `{PREFIX}autoban threshold 1d` for 1 day. \
Supports up to two digits.""")
        return
    with open("auto_punish_info.json", "r+") as auto_punish_info:
        data = json.load(auto_punish_info)
        threshold_update = {"threshold": f"{threshold}"}
        data["auto_punish_info"]["ban"].update(threshold_update)  # Updates the JSON object.
        auto_punish_info.seek(0)
        json.dump(data, auto_punish_info, indent=2)  # Writes the update to the complaint log.
        auto_punish_info.truncate()
        auto_punish_info.close()
    await ctx.message.add_reaction("👍")
    return


@bot.group(name="autokick", aliases=["ak"], case_insensitive=True)
@has_role(551968333008732169)
async def autokick(ctx):
    if ctx.invoked_subcommand is None:
        await ctx.send("No argument specified. Acceptable arguments: `on`, `off`")
        return
    else:
        pass


@autokick.command(name="on", aliases=["y", "1", "enabled", "true", "yes"])
@has_role(551968333008732169)
async def on(ctx):
    with open("auto_punish_info.json", "r+") as auto_punish_info:
        data = json.load(auto_punish_info)
        status_update = {"enabled": "true"}
        data["auto_punish_info"]["kick"].update(status_update)  # Updates the JSON object.
        auto_punish_info.seek(0)
        json.dump(data, auto_punish_info, indent=2)  # Writes the update to the complaint log.
        auto_punish_info.truncate()
        auto_punish_info.close()
    await ctx.message.add_reaction("👍")
    return


@autokick.command(name="off", aliases=["n", "0", "disabled", "false", "no"])
@has_role(551968333008732169)
async def off(ctx):
    with open("auto_punish_info.json", "r+") as auto_punish_info:
        data = json.load(auto_punish_info)
        status_update = {"enabled": "false"}
        data["auto_punish_info"]["kick"].update(status_update)  # Updates the JSON object.
        auto_punish_info.seek(0)
        json.dump(data, auto_punish_info, indent=2)  # Writes the update to the complaint log.
        auto_punish_info.truncate()
        auto_punish_info.close()
    await ctx.message.add_reaction("👍")
    return


# MODERATOR ONLY:


# REP ONLY:


@bot.command(name="conductor", aliases=["con"])  # Defines the conductor command.
@guild_only()  # Checks to ensure the command is only run in a guild.
@has_any_role(569959138583511082, 551977968503881748)  # Checks to ensure the invoker has one of these roles.
async def conductor(ctx, member: discord.Member = None):
    if member is None:  # Functions in this block execute if the invoker fails to mention a member.
        await ctx.send(f"""Command failed. Please mention the member you would like to give the Conductor role to.
Example: `{PREFIX}conductor @Dusk Argentum#6530`""")
        return
    conductor_role = discord.utils.get(ctx.guild.roles, name="Conductor")  # Defines the conductor role.
    await member.add_roles(conductor_role)  # Gives the member the conductor role.
    await ctx.message.add_reaction("👍")
    return


@bot.command(name=f"early_pull", aliases=[f"ep", f"early"])  # This defines the `early_pull` command.
@guild_only()  # This command can only be run within a guild.
@has_any_role(569959138583511082, 551977968503881748)  # This command can only be run by members who have this role.
async def early_pull(ctx):  # This command was requested by the Aether Hunts mod team in response to the vast
    # number of complaints about early pullers following patch 5.5.
    with open("complaint_log.json", "r+") as complaint_log:  # Opens the complaint log.
        current_time = datetime.now(timezone.utc)  # Defines the current time.
        data = json.load(complaint_log)  # Loads the complaint log.
        last_complaint_raw = data["complaint_log"]["last_complaint"]  # Gets the string of the time of the last
        # complaint.
        last_complaint_delta = datetime.strptime(last_complaint_raw, "%Y-%m-%d %H:%M:%S%z")  # Transforms the time
        # string into a usable datetime object for difference calculation.
        longest_duration_raw = data["complaint_log"]["longest_duration"]  # Gets the string of the longest duration.
        # The longest duration is stored in seconds for reasons.
        current_duration_raw = (current_time - last_complaint_delta)  # Finds the difference between the current time
        # and the last complaint time in order to find out the duration of the time between the two.
        current_duration_in_seconds_raw = current_duration_raw.total_seconds()  # Converts the above duration into
        # seconds.
        current_duration_in_seconds_cut = (str(current_duration_in_seconds_raw).split(".")[0])  # We don't need
        # milliseconds or microseconds or whatever the fuck those are in this house.
        if int(current_duration_in_seconds_cut) > int(longest_duration_raw):  # Functions in this block execute
            # if the current duration is longer than the stored longest duration.
            longest_duration_raw = str(current_duration_in_seconds_cut)  # Sets the longest duration to the current
            # duration.
            longest_duration_update = {"longest_duration": f"{longest_duration_raw}"}  # Defines the JSON object
            # to commit to the complaint log JSON.
            data["complaint_log"].update(longest_duration_update)  # Updates the JSON object.
            complaint_log.seek(0)
            json.dump(data, complaint_log, indent=2)  # Writes the update to the complaint log.
            complaint_log.truncate()
        elif int(current_duration_in_seconds_cut) < int(longest_duration_raw):  # Functions in this block execute if
            # the current duration is shorter than the stored longest duration.
            pass
        last_complaint_update = ({"last_complaint": f"""{datetime.now(timezone.utc).strftime(
"%Y-%m-%d %H:%M:%S%z")}"""})  # Defines the update of the JSON object of the last complaint time to the current
        # time in a specific format because reasons.
        data["complaint_log"].update(last_complaint_update)  # Updates the JSON object.
        complaint_log.seek(0)
        json.dump(data, complaint_log, indent=2)  # Writes the update to the complaint log.
        complaint_log.truncate()
        complaint_log.close()  # Closes the complaint log.
    longest_duration_days_total = divmod(int(longest_duration_raw), 86400)[0]  # Gets the total amount of days that
    # the amount of seconds in the longest duration has by dividing the amount of seconds by the amount of seconds
    # in a day.
    longest_duration_days_remainder = divmod(int(longest_duration_raw), 86400)[1]  # Does the same thing as the above
    # except this is the remainder amount, needed for calculating the smaller time fragments.
    longest_duration_hours_total = divmod(int(longest_duration_days_remainder), 3600)[0]  # Same as for days.
    longest_duration_hours_remainder = divmod(int(longest_duration_days_remainder), 3600)[1]  # Same as for days.
    longest_duration_minutes_total = divmod(int(longest_duration_hours_remainder), 60)[0]
    longest_duration_minutes_remainder = divmod(int(longest_duration_hours_remainder), 60)[1]
    longest_duration_seconds_total = divmod(int(longest_duration_minutes_remainder), 1)[0]  # Seconds remainder
    # is not required because fuck milliseconds.
    current_duration_days_search = re.search(r"(\d{1,9}) day", str(current_duration_raw), re.IGNORECASE)  # Searches
    # the raw current duration for an amount of days.
    if current_duration_days_search is not None:  # Functions in this block execute if the current duration is over a
        # day, because of the way the difference was returned when finding the difference between the current time
        # and the last complaint time.
        current_duration_days = str(current_duration_days_search.group(1))
        pass
    else:
        current_duration_days = "0"  # Sets the current duration days to 0 because things break if I don't do this.
        pass
    current_duration_hours_search = re.search(r"(\d{1,2}):", str(current_duration_raw), re.IGNORECASE)  # Same as
    # days but for hours.
    current_duration_hours = str(current_duration_hours_search.group(1))
    current_duration_minutes_search = re.search(r":(\d{2}):", str(current_duration_raw), re.IGNORECASE)
    current_duration_minutes = str(current_duration_minutes_search.group(1))
    current_duration_seconds_search = re.search(r":(\d{2})\.", str(current_duration_raw), re.IGNORECASE)
    current_duration_seconds = str(current_duration_seconds_search.group(1))
    embed = discord.Embed(title="Early pull complaint detected!", color=discord.Color(0x2bcc96),
                          description="""Please remember that Aether Hunts cannot control whether people pull \
marks early. Sometimes it is done by accident, and sometimes it is done by users beyond the Aether Hunts mod team's \
jurisdiction. Regardless, please be advised that there will be additional S Rank marks in the future.""")  # Defines
    # the embed for sending and some of its attributes.
    embed.add_field(name="Durations:", value=f"""We have gone \
{str(current_duration_days)} \
{"days" if int(current_duration_days) > 1 or int(current_duration_days) == 0 else "day"}, \
{str(current_duration_hours)} \
{"hours" if int(current_duration_hours) > 1 or int(current_duration_hours) == 0 else "hour"}, \
{str(current_duration_minutes)} \
{"minutes" if int(current_duration_minutes) > 1 or int(current_duration_minutes) == 0 else "minute"}, and \
{str(current_duration_seconds)} \
{"seconds" if int(current_duration_seconds) > 1 or int(current_duration_seconds) == 0 else "seconds"} \
without any logged complaints about early pullers.
The longest we have ever gone without any logged complaints about early pullers is \
{str(longest_duration_days_total)} \
{"days" if int(longest_duration_days_total) > 1 or int(longest_duration_days_total) == 0 else "day"}, \
{str(longest_duration_hours_total)} \
{"hours" if int(longest_duration_hours_total) > 1 or int(longest_duration_hours_total) == 0 else "hour"}, \
{str(longest_duration_minutes_total)} \
{"minutes" if int(longest_duration_minutes_total) > 1 or int(longest_duration_minutes_total) == 0 else "minute"}, \
and {str(longest_duration_seconds_total)} \
{"seconds" if int(longest_duration_seconds_total) > 1 or int(longest_duration_seconds_total) == 0 else "second"}.""")
    # This is so much more jank and longer than it needs to be probably, but I like descriptive variables and am
    # super dumb.
    await ctx.send(embed=embed)  # Sends it.
    return


@bot.command(name="spawner", aliases=["spawn"])  # This is essentially the same as conductor, so it will not be
# commented.
@guild_only()
@has_any_role(569959138583511082, 551977968503881748)
async def conductor(ctx, member: discord.Member = None):
    if member is None:
        await ctx.send(f"""Command failed. Please mention the member you would like to give the Spawner role to.
Example: `{PREFIX}conductor @Dusk Argentum#6530`""")
        return
    spawner_role = discord.utils.get(ctx.guild.roles, name="Spawner")
    await member.add_roles(spawner_role)
    await ctx.message.add_reaction("👍")
    return


# VERIFICATION:


@bot.command(pass_context=True, name="id_link", aliases=["id", "link2", "l2"])  # A more specific linking command,
# for ensuring, ABSOLUTELY, that the character that the user intends to link is the character that is linked.
async def id_link(ctx, character_id: int = None):  # Many of the comments that would be in this command are identical
    # to the comments that are in the linking command. Just view those. If there's any differences, I will note.
    """Links, via ID, your FFXIV character to your Discord name. This process may take up to one minute."""
    if_is_admin = re.search(r"name='Admin'", str(ctx.author.roles), re.IGNORECASE)
    if ctx.guild is None:
        await ctx.author.send("This command cannot be run in a DM! Please run it in the server.")
        return
    elif ctx.guild is not None:
        pass
    if character_id is None:
        await ctx.send(f"""Could not complete operation! \
One or more arguments were missing, incomplete, or incorrect.
Proper use: `{PREFIX}id_link character_id_number`, ex. `{PREFIX}id_link 22568447`.
You can find your character's ID by searching for your character on the Lodestone!""")  # I'm hoping this is descriptive
        # enough to help people find their characters' IDs...
        return
    else:
        async with aiohttp.ClientSession(timeout=120) as session:
            session = aiohttp.ClientSession()
            wait = await ctx.send("""Please wait while I search for your character... This could take up to one \
full minute, if either Discord or the Lodestone are having issues.""")
            client = pyxivapi.XIVAPIClient(session=session, api_key=XIVAPI_TOKEN)
            is_search_finished = 0
            character_search = []
            try:
                async with ctx.typing():
                    character_search = await client.character_by_id(lodestone_id=character_id,
                                                                    extended=False,
                                                                    include_freecompany=False)  # Searches the
                    # lodestone for a character with the given ID. Extra information is not included; it is not
                    # necessary for verification.
            except XIVAPIForbidden:
                await ctx.send("""Sorry! I ran into an error. Please try again. If you keep seeing this, report it!
Debug information:
`ERROR: XIVAPI FORBIDDEN`""")
                return
            except XIVAPIBadRequest:
                await ctx.send("""Sorry! I ran into an error. Please try again. If you keep seeing this, report it!
Debug information:
`ERROR: XIVAPI BAD REQUEST`""")
                return
            except XIVAPINotFound:
                await ctx.send("""I could not find that character. Please make sure you are using the correct ID!
You can find your character's ID by searching for them on the Lodestone and opening their profile, or by visiting
https://na.finalfantasyxiv.com/lodestone/my/ and clicking your character's name near the top, in the blue banner.
If you believe you've seen this message in error, please feel free to try again.""")  # This error message is different
                # because this is the exception that is thrown when an invalid character ID is used. Apparently.
                return
            except XIVAPIServiceUnavailable:
                await ctx.send("""Sorry! I ran into an error. Please try again. If you keep seeing this, report it!
Debug information:
`ERROR: XIVAPI SERVICE UNAVAILABLE`""")
                return
            except XIVAPIInvalidLanguage:
                await ctx.send("""Sorry! I ran into an error. Please try again. If you keep seeing this, report it!
Debug information:
`ERROR: XIVAPI INVALID LANGUAGE`""")
                return
            except XIVAPIInvalidIndex:
                await ctx.send("""Sorry! I ran into an error. Please try again. If you keep seeing this, report it!
Debug information:
`ERROR: XIVAPI INVALID INDEX`""")
                return
            except XIVAPIInvalidColumns:
                await ctx.send("""Sorry! I ran into an error. Please try again. If you keep seeing this, report it!
Debug information:
`ERROR: XIVAPI INVALID COLUMNS`""")
                return
            except XIVAPIInvalidFilter:
                await ctx.send("""Sorry! I ran into an error. Please try again. If you keep seeing this, report it!
Debug information:
`ERROR: XIVAPI INVALID FILTER`""")
                return
            except XIVAPIInvalidWorlds:
                await ctx.send("""Sorry! I ran into an error. Please try again. If you keep seeing this, report it!
Debug information:
`ERROR: XIVAPI INVALID WORLDS`""")
                return
            except XIVAPIInvalidDatacenter:
                await ctx.send("""Sorry! I ran into an error. Please try again. If you keep seeing this, report it!
Debug information:
`ERROR: XIVAPI INVALID DATACENTER`""")
                return
            except XIVAPIError:
                await ctx.send("""Sorry! I ran into an error. Please try again. If you keep seeing this, report it!
Debug information:
`ERROR: XIVAPI GENERAL ERROR`""")
                return
            finally:
                await session.close()
                character_id_search = re.search(r"(\'ID\': )(\d{7,10})", str(character_search), re.IGNORECASE)
                # The Regex here is a little different, because, apparently, every piece of gear worn by the character
                # needs to have its own unique ID. Silly game developers. Minimum of 7 digits SHOULD prevent any overlap
                # while still including any characters that have weirdly low IDs, for some reason. If those even exist.
                character_name_search = re.search(r"""(\'Name\': ['\"])([a-z\-\']{1,15})\s([a-z\-\']{1,15})(['\"], \'Nameday\')""",
                                                  str(character_search), re.IGNORECASE)
                character_world_search = re.search(r"(\'Server\': \')([a-z]{4,12})", str(character_search),
                                                   re.IGNORECASE)
                character_dc_search = re.search(r"(\'DC\': \')([a-z]{4,9})(\')", str(character_search), re.IGNORECASE)
                # The Regex here is a little different, because the search_by_id function returns a sensible output for
                # the DC information.
                character_avatar_search = re.search(r"(\'Avatar\': \')(\S{20,})(\')",
                                                    str(character_search), re.IGNORECASE)  # Same for this.
                character_id = int(character_id_search.group(2))
                character_first_name = str(character_name_search.group(2))
                character_last_name = str(character_name_search.group(3))
                character_world_name = str(character_world_search.group(2))
                character_dc_name = str(character_dc_search.group(2))
                character_avatar_url = str(character_avatar_search.group(2))
                # print(str(character_search))
                # print(str(character_id))
                # print(str(character_first_name))
                # print(str(character_last_name))
                # print(str(character_world_name))
                # print(str(character_dc_name))
                # print(str(character_avatar_url))
                # These are all commented out because I got tired of rewriting them when I needed to debug something.
                if character_first_name == "Dusk" and character_last_name == "Argentum":
                    if ctx.author.id != 97153790897045504 and ctx.author.id != 218530229730148352:
                        embed = discord.Embed(title="Whoops!", description=f"""Please be sure to read the verification \
instructions more clearly. You have attempted to verify as the example character.
Proper usage:
`{PREFIX}id_link YOUR_ID_HERE`
Your character ID can be found by visiting https://na.finalfantasyxiv.com/lodestone/my/ and clicking your character's \
name near the top, in the blue banner.""", color=discord.Color(0xff0000))
                        await ctx.send(embed=embed)
                        await wait.delete()
                        return
                    else:
                        pass
                if character_world_name not in str(ctx.guild.roles):
                    await ctx.guild.create_role(name=f"{character_world_name}")
                    pass
                elif character_world_name in str(ctx.guild.roles):
                    pass
                if character_dc_name not in str(ctx.guild.roles):
                    await ctx.guild.create_role(name=f"{character_dc_name}")
                    pass
                elif character_dc_name in str(ctx.guild.roles):
                    pass
                with open("characters.json", "r+") as character_database:
                    data = json.load(character_database)
                    is_in_database = re.search(rf"{ctx.author.id}", str(data))
                    if is_in_database is None:
                        character = {
                            f"{ctx.author.id}": {
                                "character_id": f"{character_id}",
                                "character_first_name": f"{character_first_name}",
                                "character_last_name": f"{character_last_name}",
                                "character_world_name": f"{character_world_name}",
                                "character_dc_name": f"{character_dc_name}",
                                "character_avatar_url": f"{character_avatar_url}"
                            }
                        }
                        with open("characters.json", "r+") as character__database:
                            await wait.delete()
                            data_ = json.load(character__database)
                            data_["character_info"].update(character)
                            character__database.seek(0)
                            json.dump(data_, character__database, indent=2)
                            character__database.close()
                            world_role = discord.utils.get(ctx.guild.roles, name=f"{character_world_name}")
                            dc_role = discord.utils.get(ctx.guild.roles, name=f"{character_dc_name}")
                            licensed_hunter_role = discord.utils.get(ctx.guild.roles, name="Licensed Hunter")
                            licensed_viewer_role = discord.utils.get(ctx.guild.roles, name="Licensed Viewer")
                            check_for_deprecated_world = re.search(r"""(\'Adamantoise\'|\'Aegis\'|\'Alexander\'|
\'Anima\'|\'Asura\'|\'Bahamut\'|\'Balmung\'|\'Behemoth\'|\'Belias\'|\'Brynhildr\'|\'Cactuar\'|\'Carbuncle\'|
\'Cerberus\'|\'Chocobo\'|\'Coeurl\'|\'Diabolos\'|\'Durandal\'|\'Excalibur\'|Exodus\'|\'Faerie\'|\'Famfrit\'|\'Fenrir\'|
\'Garuda\'|\'Gilgamesh\'|\'Goblin\'|\'Gungnir\'|\'Hades\'|\'Hyperion\'|\'Ifrit\'|\'Ixion\'|\'Jenova\'|\'Kujata\'|
\'Lamia\'|\'Leviathan\'|\'Lich\'|\'Louisoix\'|\'Malboro\'|\'Mandragora\'|\'Mateus\'|\'Masamune\'|\'Midgardsormr\'|
\'Moogle\'|\'Odin\'|\'Omega\'|\'Pandaemonium\'|\'Phoenix\'|\'Ragnarok\'|\'Ramuh\'|\'Ridill\'|\'Sargatanas\'|\'Shinryu\'|
\'Shiva\'|\'Siren\'|\'Spriggan\'|\'Tiamat\'|\'Titan\'|\'Tonberry\'|\'Twintania\'|\'Typhon\'|\'Ultima\'|\'Ultros\'|
\'Unicorn\'|\'Valefor\'|\'Yojimbo\'|\'Zalera\'|\'Zeromus\'|\'Zodiark\')""", str(ctx.author.roles),
                                                                   re.IGNORECASE)
                            if check_for_deprecated_world is not None:
                                deprecated_world = str(check_for_deprecated_world.group(1))
                                deprecated_world_name = deprecated_world.strip("'")
                                deprecated_world_role = discord.utils.get(ctx.guild.roles,
                                                                          name=f"{deprecated_world_name}")
                                await ctx.author.remove_roles(deprecated_world_role)
                                pass
                            elif check_for_deprecated_world is None:
                                pass
                            await ctx.author.add_roles(world_role)
                            await ctx.author.add_roles(dc_role)
                            if character_dc_name == "Aether":
                                await ctx.author.add_roles(licensed_hunter_role)
                                pass
                            else:
                                pass
                            if ctx.author.id == ctx.guild.owner_id:
                                pass
                            elif ctx.author.id != ctx.guild.owner_id:
                                if if_is_admin is not None:
                                    pass
                                else:
                                    await ctx.author.edit(nick=f"{character_first_name} {character_last_name}")
                                    pass
                            if character_dc_name == "Aether":
                                embed = discord.Embed(title="Verification complete!", description="""Please feel free \
to peruse the React Roles category and use <#865129809452728351> to pick up roles for anything you are interested in. \
Welcome to Aether Hunts!""", color=discord.Color(0x00cc00))
                                embed.add_field(name="Roles Granted:",
                                                value=f"""<@&{licensed_hunter_role.id}>
<@&{world_role.id}>\n<@&{dc_role.id}>""")
                                await ctx.author.add_roles(licensed_viewer_role)
                                pass
                            elif character_dc_name == "Crystal":
                                embed = discord.Embed(title="Verification complete!", description="""Unfortunately, \
you have registered a character not from Aether, making our Discord useless to you. Please re-attempt \
the linking process with a character from Aether, or consider joining the Crystal Hunts Discord, which caters to \
players from the Crystal Datacenter!""",
                                                      color=discord.Color(0xcf7602))
                                embed.add_field(name="Crystal Hunts Discord Link:", value="https://discord.gg/S8fKQvh",
                                                inline=False)
                                embed.add_field(name="Roles Granted:", value=f"<@&{world_role.id}>\n<@&{dc_role.id}>")
                                pass
                            elif character_dc_name == "Light":
                                embed = discord.Embed(title="Verification complete!", description="""Unfortunately, \
you have registered a character not from Aether, making our Discord useless to you. Please re-attempt \
the linking process with a character from Aether, or consider joining the Clan Centurio Discord, which caters to \
players from the Light Datacenter!""",
                                                      color=discord.Color(0xcf7602))
                                embed.add_field(name="Clan Centurio Discord Link:", value="https://discord.gg/h52Uzm4",
                                                inline=False)
                                embed.add_field(name="Roles Granted:", value=f"<@&{world_role.id}>\n<@&{dc_role.id}>")
                                pass
                            elif character_dc_name == "Primal":
                                embed = discord.Embed(title="Verification complete!", description="""Unfortunately, \
you have registered a character not from Aether, making our Discord useless to you. Please re-attempt \
the linking process with a character from Aether, or consider joining The Coeurl (Primal Hunts) Discord, which \
caters to players from the Primal Datacenter!""",
                                                      color=discord.Color(0xcf7602))
                                embed.add_field(name="The Coeurl (Primal Hunts) Discord Link:",
                                                value="https://discord.gg/k4xNWdV", inline=False)
                                embed.add_field(name="Roles Granted:", value=f"<@&{world_role.id}>\n<@&{dc_role.id}>")
                                pass
                            elif character_dc_name == "Elemental":
                                embed = discord.Embed(title="Verification complete!", description="""Unfortunately, \
you have registered with a character not from Aether, making our Discord useless to you. Please re-attempt \
the linking process with a character from Aether, or consider joining Faloop! - FFXIV The Hunt Discord, which \
caters to players from the Elemental Datacenter!""",
                                                      color=discord.Color(0xcf7602))
                                embed.add_field(name="Faloop! - FFXIV The Hunt Discord Link:",
                                                value="https://discord.gg/kQT4NfsemN", inline=False)
                                embed.add_field(name="Roles Granted:", value=f"<@&{world_role.id}>\n<@&{dc_role.id}>")
                                pass
                            else:
                                embed = discord.Embed(title="Verification complete!", description="""Unfortunately, \
you have registered using a character not from Aether, making our Discord useless to you. Please re-attempt \
the linking process with a character from Aether and the Discord will open up to you!""",
                                                      color=discord.Color(0xcf7602))
                                embed.add_field(name="Roles Granted:", value=f"<@&{world_role.id}>\n<@&{dc_role.id}>")
                                pass
                            if ctx.author.id == ctx.guild.owner_id:
                                embed.add_field(name="Unchangeable Name!", value="""Due to a Discord limitation, I am \
unable to change your name.""")
                                pass
                            elif if_is_admin is not None:
                                embed.add_field(name="Unchangeable Name!", value="""Due to a Discord limitation, I am \
unable to change your name.""")
                                pass
                            elif ctx.author.id != ctx.guild.owner_id:
                                embed.add_field(name="Name Changed:",
                                                value=f"{character_first_name} {character_last_name}")
                                pass
                            embed.set_thumbnail(url=character_avatar_url)
                            await ctx.send(embed=embed)
                            await asyncio.sleep(300)
                            await ctx.author.remove_roles(licensed_viewer_role)
                            return
                    elif is_in_database is not None:
                        await wait.delete()
                        with open("characters.json", "r+") as character__database:
                            data = json.load(character__database)
                            character_former_first_name = (data["character_info"]
                                                           [f"{ctx.author.id}"]["character_first_name"])
                            character_former_last_name = (data["character_info"]
                                                          [f"{ctx.author.id}"]["character_last_name"])
                            character_former_world_name = (data["character_info"]
                                                           [f"{ctx.author.id}"]["character_world_name"])
                            character_former_dc_name = (data["character_info"]
                                                        [f"{ctx.author.id}"]["character_dc_name"])
                            character_former_avatar_url = (data["character_info"]
                                                           [f"{ctx.author.id}"]["character_avatar_url"])
                            former_world_role = discord.utils.get(ctx.guild.roles,
                                                                  name=f"{character_former_world_name}")
                            former_dc_role = discord.utils.get(ctx.guild.roles,
                                                               name=f"{character_former_dc_name}")
                            character_updated_world_role = discord.utils.get(ctx.guild.roles,
                                                                             name=f"{character_world_name}")
                            character_updated_dc_role = discord.utils.get(ctx.guild.roles,
                                                                          name=f"{character_dc_name}")
                            character_update = {"character_id": f"{character_id}",
                                                "character_first_name": f"{character_first_name}",
                                                "character_last_name": f"{character_last_name}",
                                                "character_world_name": f"{character_world_name}",
                                                "character_dc_name": f"{character_dc_name}",
                                                "character_avatar_url": f"{character_avatar_url}"}
                            licensed_hunter_role = discord.utils.get(ctx.guild.roles, name="Licensed Hunter")
                            if character_dc_name == "Aether":
                                await ctx.author.add_roles(licensed_hunter_role)
                                pass
                            elif character_dc_name != "Aether":
                                if licensed_hunter_role in ctx.author.roles:
                                    await ctx.author.remove_roles(licensed_hunter_role)
                                    pass
                                else:
                                    pass
                            await ctx.author.remove_roles(former_world_role)
                            await ctx.author.remove_roles(former_dc_role)
                            check_for_deprecated_world = re.search(r"""(\'Adamantoise\'|\'Aegis\'|\'Alexander\'|
\'Anima\'|\'Asura\'|\'Bahamut\'|\'Balmung\'|\'Behemoth\'|\'Belias\'|\'Brynhildr\'|\'Cactuar\'|\'Carbuncle\'|
\'Cerberus\'|\'Chocobo\'|\'Coeurl\'|\'Diabolos\'|\'Durandal\'|\'Excalibur\'|Exodus\'|\'Faerie\'|\'Famfrit\'|\'Fenrir\'|
\'Garuda\'|\'Gilgamesh\'|\'Goblin\'|\'Gungnir\'|\'Hades\'|\'Hyperion\'|\'Ifrit\'|\'Ixion\'|\'Jenova\'|\'Kujata\'|
\'Lamia\'|\'Leviathan\'|\'Lich\'|\'Louisoix\'|\'Malboro\'|\'Mandragora\'|\'Mateus\'|\'Masamune\'|\'Midgardsormr\'|
\'Moogle\'|\'Odin\'|\'Omega\'|\'Pandaemonium\'|\'Phoenix\'|\'Ragnarok\'|\'Ramuh\'|\'Ridill\'|\'Sargatanas\'|\'Shinryu\'|
\'Shiva\'|\'Siren\'|\'Spriggan\'|\'Tiamat\'|\'Titan\'|\'Tonberry\'|\'Twintania\'|\'Typhon\'|\'Ultima\'|\'Ultros\'|
\'Unicorn\'|\'Valefor\'|\'Yojimbo\'|\'Zalera\'|\'Zeromus\'|\'Zodiark\')""", str(ctx.author.roles),
                                                                   re.IGNORECASE)
                            if check_for_deprecated_world is not None:
                                deprecated_world = str(check_for_deprecated_world.group(1))
                                deprecated_world_name = deprecated_world.strip("'")
                                deprecated_world_role = discord.utils.get(ctx.guild.roles,
                                                                          name=f"{deprecated_world_name}")
                                await ctx.author.remove_roles(deprecated_world_role)
                                pass
                            elif check_for_deprecated_world is None:
                                pass
                            await ctx.author.add_roles(character_updated_world_role)
                            await ctx.author.add_roles(character_updated_dc_role)
                            if ctx.author.id == ctx.guild.owner_id:
                                pass
                            elif ctx.author.id != ctx.guild.owner_id:
                                if if_is_admin is not None:
                                    pass
                                else:
                                    await ctx.author.edit(nick=f"{character_first_name} {character_last_name}")
                                    pass
                            world_roles_updated = []
                            dc_roles_updated = []
                            character_name_updated = 0
                            world_roles_updated_state = 0
                            dc_roles_updated_state = 0
                            if former_world_role.id != character_updated_world_role.id:
                                world_roles_updated = f"""- <@&{former_world_role.id}>
+ <@&{character_updated_world_role.id}>"""
                                world_roles_updated_state = 1
                                pass
                            elif former_world_role.id == character_updated_world_role.id:
                                world_roles_updated = "** **"
                                world_roles_updated_state = 0
                                pass
                            if former_dc_role.id != character_updated_dc_role.id:
                                dc_roles_updated = f"""- <@&{former_dc_role.id}>
+ <@&{character_updated_dc_role.id}>"""
                                dc_roles_updated_state = 1
                                pass
                            elif former_dc_role.id == character_updated_dc_role.id:
                                dc_roles_updated = "** **"
                                dc_roles_updated_state = 0
                                pass
                            if character_former_first_name != character_first_name:
                                character_name_updated = 1
                                pass
                            if character_former_last_name != character_last_name:
                                character_name_updated = 1
                                pass
                            if licensed_hunter_role in ctx.author.roles:
                                embed = discord.Embed(title="Update complete!", description="""Your \
information has been updated!""", color=discord.Color(0x00cc00))
                                if world_roles_updated_state == 0 and dc_roles_updated_state == 0:
                                    embed.add_field(name="Roles Updated:", value="No update!")
                                    pass
                                elif world_roles_updated_state == 0 and dc_roles_updated_state == 1:
                                    embed.add_field(name="Roles Updated:", value=f"{str(dc_roles_updated)}")
                                    pass
                                elif world_roles_updated_state == 1 and dc_roles_updated_state == 0:
                                    embed.add_field(name="Roles Updated:", value=f"{str(world_roles_updated)}")
                                    pass
                                elif world_roles_updated_state == 1 and dc_roles_updated_state == 1:
                                    embed.add_field(name="Roles Updated:",
                                                    value=f"""{str(world_roles_updated)}
{str(dc_roles_updated)}""")
                                    pass
                                else:
                                    embed.add_field(name="ERROR:", value="Neither change state detected!!!")
                                    pass
                                if ctx.author.id == ctx.guild.owner_id:
                                    embed.add_field(name="Unchangeable Name!", value="""Due to a Discord \
limitation, I am unable to change your name.""")
                                    pass
                                elif if_is_admin is not None:
                                    embed.add_field(name="Unchangeable Name!", value="""Due to a Discord limitation, I am \
                                unable to change your name.""")
                                    pass
                                elif character_name_updated == 0:
                                    embed.add_field(name="Name Updated:", value="No update!")
                                    pass
                                elif character_name_updated == 1:
                                    embed.add_field(name="Name Updated:",
                                                    value=f"""~~{character_former_first_name} \
{character_former_last_name}~~
{character_first_name} {character_last_name}""")
                                    pass
                                embed.set_thumbnail(url=character_avatar_url)
                                await ctx.send(embed=embed)
                                pass
                            elif licensed_hunter_role not in ctx.author.roles:
                                character_name_updated = 0
                                world_roles_updated_state = 0
                                dc_roles_updated_state = 0
                                if former_world_role.id != character_updated_world_role.id:
                                    world_roles_updated = f"""- {former_world_role}
+ {character_updated_world_role}"""
                                    world_roles_updated_state = 1
                                    pass
                                elif former_world_role.id == character_updated_world_role.id:
                                    world_roles_updated = "** **"
                                    world_roles_updated_state = 0
                                    pass
                                if former_dc_role.id != character_updated_dc_role.id:
                                    dc_roles_updated = f"""- {former_dc_role}
+ {character_updated_dc_role}"""
                                    dc_roles_updated_state = 1
                                    pass
                                elif former_dc_role.id == character_updated_dc_role.id:
                                    dc_roles_updated = "** **"
                                    dc_roles_updated_state = 0
                                    pass
                                if character_former_first_name != character_first_name:
                                    character_name_updated = 1
                                    pass
                                if character_former_last_name != character_last_name:
                                    character_name_updated = 1
                                    pass
                                embed = discord.Embed(title="Update complete!", description="""Unfortunately, \
however, when updating your information, it was found that your new character was not on the Aether data center. \
Aether Hunts only caters to characters on Aether, and, as such, your permissions to view the Discord have been \
limited. You are welcome to re-attempt verification with a character on Aether to regain these permissions.""",
                                                      color=discord.Color(0x91002c))
                                if world_roles_updated_state == 0 and dc_roles_updated_state == 0:
                                    embed.add_field(name="Roles Updated:", value="No update!")
                                    pass
                                elif world_roles_updated_state == 0 and dc_roles_updated_state == 1:
                                    embed.add_field(name="Roles Updated:",
                                                    value=f"""- {licensed_hunter_role}
{str(dc_roles_updated)}""")
                                    pass
                                elif world_roles_updated_state == 1 and dc_roles_updated_state == 0:
                                    embed.add_field(name="Roles Updated:", value=f"{str(world_roles_updated)}")
                                    pass
                                elif world_roles_updated_state == 1 and dc_roles_updated_state == 1:
                                    embed.add_field(name="Roles Updated:",
                                                    value=f"""- {licensed_hunter_role}
{str(world_roles_updated)}
{str(dc_roles_updated)}""")
                                    pass
                                else:
                                    embed.add_field(name="ERROR:", value="Neither change state detected!!!")
                                    pass
                                if ctx.author.id == ctx.guild.owner_id:
                                    embed.add_field(name="Unchangeable Name!", value="""Due to a Discord \
limitation, I am unable to change your name.""")
                                    pass
                                elif if_is_admin is not None:
                                    embed.add_field(name="Unchangeable Name!", value="""Due to a Discord limitation, I am \
                                unable to change your name.""")
                                    pass
                                elif character_name_updated == 0:
                                    embed.add_field(name="Name Updated:", value="No update!")
                                    pass
                                elif character_name_updated == 1:
                                    embed.add_field(name="Name Updated:",
                                                    value=f"""~~{character_former_first_name} \
{character_former_last_name}~~
{character_first_name} {character_last_name}""")
                                    pass
                                embed.set_thumbnail(url=character_avatar_url)
                                await ctx.send(embed=embed)
                                pass
                                await ctx.author.send(embed=embed)
                                pass
                            data["character_info"][f"{ctx.author.id}"].update(character_update)
                            character__database.seek(0)
                            json.dump(data, character__database, indent=2)
                            character__database.truncate()
                            character__database.close()
                            return  # There's probably a better way to have handled this than copying the majority
                        # of the normal linking command...


@bot.command(pass_context=True, name="info", aliases=["i"])  # Defines the info command.
async def info(ctx, user: discord.Member = None):
    """Shows your character information. Mention another user to view theirs."""
    if user is None:  # The function in this block sets the user argument to the command invoker if there is none
        # passed when the command is run.
        user = ctx.message.author
        pass
    else:
        pass  # Things get messy beyond this point.
    with open("characters.json", "r") as character_database:  # Opens the characters.json file and sets it to be known
        # as character_database in the future.
        data = json.load(character_database)  # Gets the information within the character database.
        is_user_linked = re.search(rf"{user.id}", str(data))  # This regex searches for the user's id within the
        # database. If it's not found, it returns None.
        if is_user_linked is None:  # Lets the command invoker know that their specified user (either themself or
            # the person they mentioned) is not in the database.
            await ctx.send("That user is not within my database!")
            return
        elif is_user_linked is not None:  # Functions in this block execute if the user's id is found within the
            # database.
            with open("characters.json", "r+") as character__database:  # Opens the database again.
                # Please don't ask me why I open it again. I think it errored when I didn't, and I don't want to fuck it
                # or anything else by changing it.
                data = json.load(character__database)  # I am once again retrieving the information within the database.
                retrieved_discord_id = (data["character_info"][f"{user.id}"])  # Gets the user's id.
                retrieved_first_name = (data["character_info"][f"{user.id}"]
                                            ["character_first_name"])  # Gets the user's character's first name.
                retrieved_last_name = (data["character_info"][f"{user.id}"]
                                           ["character_last_name"])  # Gets the user's character's last name.
                retrieved_world_name = (data["character_info"][f"{user.id}"]
                                            ["character_world_name"])  # Gets the user's character's world name.
                retrieved_dc_name = (data["character_info"][f"{user.id}"]
                                         ["character_dc_name"])  # Gets the user's character's datacenter name.
                retrieved_avatar_url = (data["character_info"][f"{user.id}"]
                                            ["character_avatar_url"])  # Gets the user's character's avatar url.
                embed = discord.Embed(title=f"""{retrieved_first_name} \
{retrieved_last_name}""", color=discord.Color(0x00a8a8))  # Defines an embed and sets the user's character's retrieved
                # first and last name as the title.
                embed.add_field(name="Linked User:", value=f"<@!{user.id}>")  # Mentions the user, for ease of viewing.
                # Does not ping. Embeds do not ping when a mention is contained within their content as a default
                # Discord behavior.
                embed.add_field(name="Current World/DC:", value=f"""{retrieved_world_name}
({retrieved_dc_name})""")  # Sets the field's title and the content as the retrieved world and DC names.
                embed.set_thumbnail(url=retrieved_avatar_url)  # Sets the thumbnail as the user's character's avatar
                # url.
                embed.set_footer(text=f"""This info may not be up to date if this user hasn't updated in a while. | \
To update, use the {PREFIX}link command.""")
                await ctx.send(embed=embed)
                return


@bot.command(pass_context=True, name="link", aliases=["l"])  # Defines the linking command. Shit gets messy in here.
async def link(ctx, first_name: str = None, last_name: str = None, world_name: str = None):
    """Links your FFXIV character to your Discord name. This process may take up to one minute."""
    if_is_admin = re.search(r"name='Admin'", str(ctx.author.roles), re.IGNORECASE)
    if ctx.guild is None:  # Stops the command from executing if the command is run in a DM. The command would
        # error anyway. This saves the user time and effort.
        await ctx.author.send("This command cannot be run in a DM! Please run it in the server.")
        return
    elif ctx.guild is not None:
        pass
    world_list = """Adamantoise, Aegis, Alexander, Anima, Asura, Bahamut, Balmung, Behemoth, Belias, Brynhildr,
Cactuar, Carbuncle, Cerberus, Chocobo, Coeurl, Diabolos, Durandal, Excalibur, Exodus, Faerie, Famfrit, Fenrir,
Garuda, Gilgamesh, Goblin, Gungnir, Hades, Hyperion, Ifrit, Ixion, Jenova, Kujata, Lamia, Leviathan, Lich, Louisoix,
Malboro, Mandragora, Mateus, Masamune, Midgardsormr, Moogle, Odin, Omega, Pandaemonium, Phoenix, Ragnarok, Ramuh,
Ridill, Sargatanas, Shinryu, Shiva, Siren, Spriggan, Tiamat, Titan, Tonberry, Twintania, Typhon, Ultima, Ultros,
Unicorn, Valefor, Yojimbo, Zalera, Zeromus, Zodiark"""  # Defines the list of worlds, which will need to be updated
    # if/when new worlds are updated.
    if first_name is None:  # The following blocks execute if an argument is missing, incomplete, or incorrect.
        # Usually missing.
        await ctx.send(f"""Could not complete operation! \
One or more arguments were missing, incomplete, or incorrect.
Proper use: `{PREFIX}link first_name last_name world_name`, ex. `{PREFIX}link Dusk Argentum Gilgamesh`.""")
        return
    if last_name is None:
        await ctx.send(f"""Could not complete operation! \
One or more arguments were missing, incomplete, or incorrect.
Proper use: `{PREFIX}link first_name last_name world_name`, ex. `{PREFIX}link Dusk Argentum Gilgamesh`.""")
        return
    if world_name is None:
        await ctx.send(f"""Could not complete operation! \
One or more arguments were missing, incomplete, or incorrect.
Proper use: `{PREFIX}link first_name last_name world_name`, ex. `{PREFIX}link Dusk Argentum Gilgamesh`.""")
        return
    elif world_name.lower() not in world_list.lower():  # This block prevents the command from going any further
        # if the world name is not within the above list. Saves users who can't spell Midgardsormr and Sargatanas
        # and long, weird world names like that from waiting the full linking time.
        await ctx.send(f"""Invalid world! Please make sure you have spelled it correctly. Attempted world: \
{world_name}.""")
        return
    else:
        async with aiohttp.ClientSession(timeout=120) as session:  # Opens the session to the Lodestone.
            session = aiohttp.ClientSession()  # I don't know why I define it again, tho. Not breaking it, tho.
            wait = await ctx.send("""Please wait while I search for your character... This could take up to one \
full minute, if either Discord or the Lodestone are having issues.""")
            # This, apparently, only takes a minute when running locally.
            client = pyxivapi.XIVAPIClient(session=session, api_key=XIVAPI_TOKEN)  # Opens the link between
            # XIVAPI and the bot, using the API token stored in environmental variables.
            is_search_finished = 0  # A presently unused variable.
            character_search = []  # Defines the character_search variable as empty.
            try:  # A try:except block is used for error checking. This... might work? I've never had any of the
                # errors execute, but I think this works in theory.
                async with ctx.typing():  # Sets the bot to send a typing status to Discord, so the command invoker
                    # knows the bot is still online while it's chugging away at those HTTP requests.
                    character_search = await client.character_search(world=world_name, forename=first_name,
                                                                     surname=last_name)  # Searches the lodestone
                    # for a character with the given information.
            except XIVAPIForbidden:  # All of the except blocks are error handling blocks. They *might* work.
                await ctx.send("""Sorry! I ran into an error. Please try again. If you keep seeing this, report it!
Debug information:
`ERROR: XIVAPI FORBIDDEN`""")
                return
            except XIVAPIBadRequest:
                await ctx.send("""Sorry! I ran into an error. Please try again. If you keep seeing this, report it!
Debug information:
`ERROR: XIVAPI BAD REQUEST`""")
                return
            except XIVAPINotFound:
                await ctx.send("""Sorry! I ran into an error. Please try again. If you keep seeing this, report it!
Debug information:
`ERROR: XIVAPI NOT FOUND`""")
                return
            except XIVAPIServiceUnavailable:
                await ctx.send("""Sorry! I ran into an error. Please try again. If you keep seeing this, report it!
Debug information:
`ERROR: XIVAPI SERVICE UNAVAILABLE`""")
                return
            except XIVAPIInvalidLanguage:
                await ctx.send("""Sorry! I ran into an error. Please try again. If you keep seeing this, report it!
Debug information:
`ERROR: XIVAPI INVALID LANGUAGE`""")
                return
            except XIVAPIInvalidIndex:
                await ctx.send("""Sorry! I ran into an error. Please try again. If you keep seeing this, report it!
Debug information:
`ERROR: XIVAPI INVALID INDEX`""")
                return
            except XIVAPIInvalidColumns:
                await ctx.send("""Sorry! I ran into an error. Please try again. If you keep seeing this, report it!
Debug information:
`ERROR: XIVAPI INVALID COLUMNS`""")
                return
            except XIVAPIInvalidFilter:
                await ctx.send("""Sorry! I ran into an error. Please try again. If you keep seeing this, report it!
Debug information:
`ERROR: XIVAPI INVALID FILTER`""")
                return
            except XIVAPIInvalidWorlds:
                await ctx.send("""Sorry! I ran into an error. Please try again. If you keep seeing this, report it!
Debug information:
`ERROR: XIVAPI INVALID WORLDS`""")
                return
            except XIVAPIInvalidDatacenter:
                await ctx.send("""Sorry! I ran into an error. Please try again. If you keep seeing this, report it!
Debug information:
`ERROR: XIVAPI INVALID DATACENTER`""")
                return
            except XIVAPIError:
                await ctx.send("""Sorry! I ran into an error. Please try again. If you keep seeing this, report it!
Debug information:
`ERROR: XIVAPI GENERAL ERROR`""")
                return
            finally:  # Functions after this execute once the character search is done.
                await session.close()  # Closes the session. Puts red text on my terminal if I leave it open too long.
                # Red text is bad.
                check_if_not_existent = re.search(r"{\'Page\': 0", str(character_search), re.IGNORECASE)  # This regex
                # searches the character_search string to see if any results were returned.
                if check_if_not_existent is None:  # If there is a result, the command passes on.
                    pass
                elif check_if_not_existent is not None:  # If there are no results, this message sends.
                    retry = await ctx.send(f"""I was not able to find **{first_name} {last_name}** of **{world_name}**.
Retrying...""")
                    # A persistent error I keep running into is that occasionally (1/20?-ish), even if a search has
                    # all of the accurate information and arguments required, the Lodestone/XIVAPI will return an empty
                    # search string. The following block and the above message inform the user of this issue for
                    # transparency reasons. I would *love* to know why this shit keeps happening.
                    session = aiohttp.ClientSession()  # Just retries the search.
                    client = pyxivapi.XIVAPIClient(session=session, api_key=XIVAPI_TOKEN)
                    async with ctx.typing():
                        character_search = await client.character_search(world=world_name, forename=first_name,
                                                                         surname=last_name)
                    await session.close()
                    second_check_if_not_existent = re.search(r"{\'Page\': 0", str(character_search), re.IGNORECASE)
                    if second_check_if_not_existent is None:
                        pass
                    elif second_check_if_not_existent is not None:
                        await ctx.send(f"""I was not able to find **{first_name} {last_name}** of **{world_name}**.
This could be due to an error on the Lodestone's end, such as the Lodestone returning empty information, or if your \
information has not been updated on the Lodestone yet.
Please wait and retry the command.""")
                        return
                character_id_search = re.search(r"(\'ID\': )(\d{1,10})", str(character_search), re.IGNORECASE)
                # Searches for the character's id from the returned Lodestone information.
                character_name_search = re.search(r"""(\'Name\': ['\"])([a-z\-\']{1,15})\s([a-z\-\']{1,15})(['\"])""",
                                                  str(character_search), re.IGNORECASE)  # Searches for the character's
                # full name from the returned Lodestone information.
                character_world_search = re.search(r"(\'Server\': \')([a-z]{4,12})", str(character_search),
                                                   re.IGNORECASE)  # Searches for the character's world name from the
                # returned Lodestone information.
                character_dc_search = re.search(r"(\\xa0\()([a-z]{4,9})", str(character_search), re.IGNORECASE)
                # Searches for the character's DC name from the returned Lodestone information.
                character_avatar_search = re.search(r"(\[{\'Avatar\': \')(\S{20,})(\',)",
                                                    str(character_search), re.IGNORECASE)  # Searches for the
                # character's avatar url from the returned Lodestone information.
                character_id = int(character_id_search.group(2))  # Specifically extracts the character's id from
                # the character_id_search search.
                character_first_name = str(character_name_search.group(2))  # Specifically extracts the character's
                # first name from the character_name_search.
                character_last_name = str(character_name_search.group(3))  # Specifically extracts the character's last
                # name from the character_name_search.
                character_world_name = str(character_world_search.group(2))  # Specifically extracts the character's
                # world name from the character_world_search.
                character_dc_name = str(character_dc_search.group(2))  # Specifically extracts the character's DC name
                # from the character_dc_search.
                character_avatar_url = str(character_avatar_search.group(2))  # Specifically extracts the character's
                # avatar url from the character_avatar_search.
                # print(str(character_search))
                # print(str(character_id))
                # print(str(character_first_name))
                # print(str(character_last_name))
                # print(str(character_world_name))
                # print(str(character_dc_name))
                # print(str(character_avatar_url))
                if character_first_name == "Dusk" and character_last_name == "Argentum":
                    if ctx.author.id != 97153790897045504 and ctx.author.id != 218530229730148352:
                        embed = discord.Embed(title="Whoops!", description=f"""Please be sure to read the verification \
instructions more clearly. You have attempted to verify as the example character.
Proper usage:
`{PREFIX}link CHARACTER_FIRST_NAME CHARACTER_LAST_NAME WORLD_NAME`""", color=discord.Color(0xff0000))
                        await ctx.send(embed=embed)
                        await wait.delete()
                        return
                    else:
                        pass
                if character_world_name not in str(ctx.guild.roles):  # Checks if the character's world has a role on the
                    # server the command is invoked on and adds the role if it doesn't exist.
                    await ctx.guild.create_role(name=f"{character_world_name}")
                    pass
                elif character_world_name in str(ctx.guild.roles):
                    pass
                if character_dc_name not in str(ctx.guild.roles):  # Checks if the character's DC has a role on the server
                    # the command is invoked on and adds the role if it doesn't exist.
                    await ctx.guild.create_role(name=f"{character_dc_name}")
                    pass
                elif character_dc_name in str(ctx.guild.roles):
                    pass
                with open("characters.json", "r+") as character_database:  # The first of many openings of the
                    # character database...
                    data = json.load(character_database)  # Loads the information from the database.
                    is_in_database = re.search(rf"{ctx.author.id}", str(data))  # Checks to see if the command invoker
                    # already has a character in the database.
                    if is_in_database is None:  # Functions in this block execute if no character is found for the
                        # command invoker's id.
                        character = {
                            f"{ctx.author.id}": {
                                "character_id": f"{character_id}",
                                "character_first_name": f"{character_first_name}",
                                "character_last_name": f"{character_last_name}",
                                "character_world_name": f"{character_world_name}",
                                "character_dc_name": f"{character_dc_name}",
                                "character_avatar_url": f"{character_avatar_url}"
                            }
                        }  # Defines the json block that contains the command invoker's id and their character's
                        # information.
                        with open("characters.json", "r+") as character__database:  # Please no booli.
                            await wait.delete()  # Deletes the wait message.
                            data_ = json.load(character__database)
                            data_["character_info"].update(character)  # Updates the loaded information with the
                            # new character's information.
                            character__database.seek(0)  # Sets the internal file cursor back to the beginning.
                            # Important. If this does not exist, the file gets all fucky-wucky.
                            json.dump(data_, character__database, indent=2)  # Writes the new information
                            # to the database file.
                            character__database.close()  # Closes the database file.
                            world_role = discord.utils.get(ctx.guild.roles, name=f"{character_world_name}")
                            # The following lines get their respective roles so they can be added.
                            dc_role = discord.utils.get(ctx.guild.roles, name=f"{character_dc_name}")
                            licensed_hunter_role = discord.utils.get(ctx.guild.roles, name="Licensed Hunter")
                            licensed_viewer_role = discord.utils.get(ctx.guild.roles, name="Licensed Viewer")
                            check_for_deprecated_world = re.search(r"""(\'Adamantoise\'|\'Aegis\'|\'Alexander\'|
\'Anima\'|\'Asura\'|\'Bahamut\'|\'Balmung\'|\'Behemoth\'|\'Belias\'|\'Brynhildr\'|\'Cactuar\'|\'Carbuncle\'|
\'Cerberus\'|\'Chocobo\'|\'Coeurl\'|\'Diabolos\'|\'Durandal\'|\'Excalibur\'|Exodus\'|\'Faerie\'|\'Famfrit\'|\'Fenrir\'|
\'Garuda\'|\'Gilgamesh\'|\'Goblin\'|\'Gungnir\'|\'Hades\'|\'Hyperion\'|\'Ifrit\'|\'Ixion\'|\'Jenova\'|\'Kujata\'|
\'Lamia\'|\'Leviathan\'|\'Lich\'|\'Louisoix\'|\'Malboro\'|\'Mandragora\'|\'Mateus\'|\'Masamune\'|\'Midgardsormr\'|
\'Moogle\'|\'Odin\'|\'Omega\'|\'Pandaemonium\'|\'Phoenix\'|\'Ragnarok\'|\'Ramuh\'|\'Ridill\'|\'Sargatanas\'|\'Shinryu\'|
\'Shiva\'|\'Siren\'|\'Spriggan\'|\'Tiamat\'|\'Titan\'|\'Tonberry\'|\'Twintania\'|\'Typhon\'|\'Ultima\'|\'Ultros\'|
\'Unicorn\'|\'Valefor\'|\'Yojimbo\'|\'Zalera\'|\'Zeromus\'|\'Zodiark\')""", str(ctx.author.roles), re.IGNORECASE)
                            if check_for_deprecated_world is not None:
                                deprecated_world = str(check_for_deprecated_world.group(1))
                                deprecated_world_name = deprecated_world.strip("'")
                                deprecated_world_role = discord.utils.get(ctx.guild.roles,
                                                                          name=f"{deprecated_world_name}")
                                await ctx.author.remove_roles(deprecated_world_role)
                                pass
                            elif check_for_deprecated_world is None:
                                pass
                            await ctx.author.add_roles(world_role)  # Adds the character's world role to the
                            # command invoker.
                            await ctx.author.add_roles(dc_role)  # Adds the character's DC role to the command invoker.
                            if character_dc_name == "Aether":  # Functions in this block execute if the character's
                                # DC is Aether.
                                await ctx.author.add_roles(licensed_hunter_role)  # Adds the Licensed Hunter role to the
                                # command invoker.
                                pass
                            else:  # If the command invoker's character's DC is not Aether, it passes on without
                                # adding the Licensed Hunter role.
                                pass
                            if ctx.author.id == ctx.guild.owner_id:  # Checks to see if the command invoker's id
                                # matches the server owner's id.
                                pass  # And skips changing their name. This is due to a Discord limitation; NOTHING,
                            # including bots, can change a server owner's name, except for the server owner themself.
                            # This used to cause the bot to stop dead in its tracks, but does not anymore.
                            elif ctx.author.id != ctx.guild.owner_id:  # Changes the command invoker's name
                                # to their character's name if they are not the server owner.
                                if if_is_admin is not None:
                                    pass
                                else:
                                    await ctx.author.edit(nick=f"{character_first_name} {character_last_name}")
                                    pass
                            if character_dc_name == "Aether":  # The following block executes if the command invoker's
                                # character's DC is Aether.
                                embed = discord.Embed(title="Verification complete!", description="""Please feel free \
to peruse the React Roles category and use <#865129809452728351> to pick up roles for anything you are interested in. \
Welcome to Aether Hunts!""", color=discord.Color(0x00cc00))
                                embed.add_field(name="Roles Granted:",
                                                value=f"""<@&{licensed_hunter_role.id}>
<@&{world_role.id}>\n<@&{dc_role.id}>""")  # Informs the command invoker that their Licensed Hunter, world, and DC
                                # roles have been added.
                                await ctx.author.add_roles(licensed_viewer_role)
                                pass
                            elif character_dc_name == "Crystal":  # The following block executes if the command
                                # invoker's character's DC is Crystal.
                                embed = discord.Embed(title="Verification complete!", description="""Unfortunately, \
you have registered a character not from Aether, making our Discord useless to you. Please re-attempt \
the linking process with a character from Aether, or consider joining the Crystal Hunts Discord, which caters to \
players from the Crystal Datacenter!""",
                                                      color=discord.Color(0xcf7602))  # Defines the embed and sets
                                # some content.
                                embed.add_field(name="Crystal Hunts Discord Link:", value="https://discord.gg/S8fKQvh",
                                                inline=False)  # Links to the affiliated DC's Discord.
                                embed.add_field(name="Roles Granted:", value=f"<@&{world_role.id}>\n<@&{dc_role.id}>")
                                pass
                            elif character_dc_name == "Light":  # The following block is for Light characters.
                                embed = discord.Embed(title="Verification complete!", description="""Unfortunately, \
you have registered a character not from Aether, making our Discord useless to you. Please re-attempt \
the linking process with a character from Aether, or consider joining the Clan Centurio Discord, which caters to \
players from the Light Datacenter!""",
                                                      color=discord.Color(0xcf7602))
                                embed.add_field(name="Clan Centurio Discord Link:", value="https://discord.gg/h52Uzm4",
                                                inline=False)  # Links the affiliated Discord.
                                embed.add_field(name="Roles Granted:", value=f"<@&{world_role.id}>\n<@&{dc_role.id}>")
                                pass
                            elif character_dc_name == "Primal":  # For Primal characters.
                                embed = discord.Embed(title="Verification complete!", description="""Unfortunately, \
you have registered a character not from Aether, making our Discord useless to you. Please re-attempt \
the linking process with a character from Aether, or consider joining The Coeurl (Primal Hunts) Discord, which \
caters to players from the Primal Datacenter!""",
                                                      color=discord.Color(0xcf7602))
                                embed.add_field(name="The Coeurl (Primal Hunts) Discord Link:",
                                                value="https://discord.gg/k4xNWdV", inline=False)  # Primal Discord.
                                embed.add_field(name="Roles Granted:", value=f"<@&{world_role.id}>\n<@&{dc_role.id}>")
                                pass
                            else:  # The following block executes if the command invoker's character's DC is none
                                # of the above.
                                embed = discord.Embed(title="Verification complete!", description="""Unfortunately, \
you have registered using a character not from Aether, making our Discord useless to you. Please re-attempt \
the linking process with a character from Aether and the Discord will open up to you!""",
                                                      color=discord.Color(0xcf7602))
                                embed.add_field(name="Roles Granted:", value=f"<@&{world_role.id}>\n<@&{dc_role.id}>")
                                pass
                            if ctx.author.id == ctx.guild.owner_id:  # This name field is added if the command invoker's
                                # id is the same as the server owner's id.
                                embed.add_field(name="Unchangeable Name!", value="""Due to a Discord limitation, I am \
unable to change your name.""")
                                pass
                            elif if_is_admin is not None:
                                embed.add_field(name="Unchangeable Name!", value="""Due to a Discord limitation, I am \
                            unable to change your name.""")
                                pass
                            elif ctx.author.id != ctx.guild.owner_id:  # Informs the command invoker that their Discord
                                # name has changed and what it has been changed to.
                                embed.add_field(name="Name Changed:",
                                                value=f"{character_first_name} {character_last_name}")
                                pass
                            embed.set_thumbnail(url=character_avatar_url)
                            await ctx.send(embed=embed)
                            await asyncio.sleep(300)
                            await ctx.author.remove_roles(licensed_viewer_role)
                            return
                    elif is_in_database is not None:  # The following block executes if the command invoker DOES
                        # have a character in the database.
                        await wait.delete()
                        with open("characters.json", "r+") as character__database:
                            data = json.load(character__database)
                            character_former_first_name = (data["character_info"]
                                                               [f"{ctx.author.id}"]["character_first_name"])
                            # The following functions grab the command invoker's character's current (soon to be
                            # outdated) information.
                            character_former_last_name = (data["character_info"]
                                                              [f"{ctx.author.id}"]["character_last_name"])
                            character_former_world_name = (data["character_info"]
                                                               [f"{ctx.author.id}"]["character_world_name"])
                            character_former_dc_name = (data["character_info"]
                                                            [f"{ctx.author.id}"]["character_dc_name"])
                            character_former_avatar_url = (data["character_info"]
                                                               [f"{ctx.author.id}"]["character_avatar_url"])
                            former_world_role = discord.utils.get(ctx.guild.roles,
                                                                  name=f"{character_former_world_name}")
                            former_dc_role = discord.utils.get(ctx.guild.roles,
                                                               name=f"{character_former_dc_name}")
                            character_updated_world_role = discord.utils.get(ctx.guild.roles,
                                                                             name=f"{character_world_name}")
                            # This function and the following grabs the command invoker's character's world/DC
                            # updated roles.
                            character_updated_dc_role = discord.utils.get(ctx.guild.roles,
                                                                          name=f"{character_dc_name}")
                            character_update = {"character_id": f"{character_id}",
                                                "character_first_name": f"{character_first_name}",
                                                "character_last_name": f"{character_last_name}",
                                                "character_world_name": f"{character_world_name}",
                                                "character_dc_name": f"{character_dc_name}",
                                                "character_avatar_url": f"{character_avatar_url}"}
                            # The above json defines the command invoker's character's new information.
                            licensed_hunter_role = discord.utils.get(ctx.guild.roles, name="Licensed Hunter")
                            if character_dc_name == "Aether":  # Adds the Licensed Hunter role to a character who
                                # verified on Aether.
                                await ctx.author.add_roles(licensed_hunter_role)
                                pass
                            elif character_dc_name != "Aether":  # This function removes the Licensed Hunter role from
                                # the command invoker if their new character's DC is not Aether.
                                if licensed_hunter_role in ctx.author.roles:
                                    await ctx.author.remove_roles(licensed_hunter_role)
                                    pass
                                else:
                                    pass
                            await ctx.author.remove_roles(former_world_role)  # The following functions change roles
                            # around, removing the old world/DC roles and adding the new ones.
                            await ctx.author.remove_roles(former_dc_role)
                            check_for_deprecated_world = re.search(r"""(\'Adamantoise\'|\'Aegis\'|\'Alexander\'|
\'Anima\'|\'Asura\'|\'Bahamut\'|\'Balmung\'|\'Behemoth\'|\'Belias\'|\'Brynhildr\'|\'Cactuar\'|\'Carbuncle\'|
\'Cerberus\'|\'Chocobo\'|\'Coeurl\'|\'Diabolos\'|\'Durandal\'|\'Excalibur\'|Exodus\'|\'Faerie\'|\'Famfrit\'|\'Fenrir\'|
\'Garuda\'|\'Gilgamesh\'|\'Goblin\'|\'Gungnir\'|\'Hades\'|\'Hyperion\'|\'Ifrit\'|\'Ixion\'|\'Jenova\'|\'Kujata\'|
\'Lamia\'|\'Leviathan\'|\'Lich\'|\'Louisoix\'|\'Malboro\'|\'Mandragora\'|\'Mateus\'|\'Masamune\'|\'Midgardsormr\'|
\'Moogle\'|\'Odin\'|\'Omega\'|\'Pandaemonium\'|\'Phoenix\'|\'Ragnarok\'|\'Ramuh\'|\'Ridill\'|\'Sargatanas\'|\'Shinryu\'|
\'Shiva\'|\'Siren\'|\'Spriggan\'|\'Tiamat\'|\'Titan\'|\'Tonberry\'|\'Twintania\'|\'Typhon\'|\'Ultima\'|\'Ultros\'|
\'Unicorn\'|\'Valefor\'|\'Yojimbo\'|\'Zalera\'|\'Zeromus\'|\'Zodiark\')""", str(ctx.author.roles), re.IGNORECASE)
                            if check_for_deprecated_world is not None:
                                deprecated_world = str(check_for_deprecated_world.group(1))
                                deprecated_world_name = deprecated_world.strip("'")
                                deprecated_world_role = discord.utils.get(ctx.guild.roles,
                                                                          name=f"{deprecated_world_name}")
                                await ctx.author.remove_roles(deprecated_world_role)
                                pass
                            elif check_for_deprecated_world is None:
                                pass
                            await ctx.author.add_roles(character_updated_world_role)
                            await ctx.author.add_roles(character_updated_dc_role)
                            if ctx.author.id == ctx.guild.owner_id:
                                pass
                            elif ctx.author.id != ctx.guild.owner_id:  # Changes the command invoker's name to match
                                # their character's in game name.
                                if if_is_admin is not None:
                                    pass
                                else:
                                    await ctx.author.edit(nick=f"{character_first_name} {character_last_name}")
                                    pass
                            world_roles_updated = []  # The following are empty/0 variables for use later.
                            dc_roles_updated = []
                            character_name_updated = 0
                            world_roles_updated_state = 0
                            dc_roles_updated_state = 0
                            if former_world_role.id != character_updated_world_role.id:  # This executes if a command
                                # invoker's old world role and new world role are not the same.
                                world_roles_updated = f"""- <@&{former_world_role.id}>
+ <@&{character_updated_world_role.id}>"""
                                world_roles_updated_state = 1  # And sets the variable that defines that their world
                                # role updated to 1.
                                pass
                            elif former_world_role.id == character_updated_world_role.id:  # Puts an empty message
                                # and does not change the world_roles_updated_state if the old and new world role id
                                # are the same.
                                world_roles_updated = "** **"
                                world_roles_updated_state = 0
                                pass
                            if former_dc_role.id != character_updated_dc_role.id:  # The following blocks are the same
                                # as the above, but for DC instead of world.
                                dc_roles_updated = f"""- <@&{former_dc_role.id}>
+ <@&{character_updated_dc_role.id}>"""
                                dc_roles_updated_state = 1
                                pass
                            elif former_dc_role.id == character_updated_dc_role.id:
                                dc_roles_updated = "** **"
                                dc_roles_updated_state = 0
                                pass
                            if character_former_first_name != character_first_name:  # The following functions execute
                                # if a character's new first/last name (respectively) do not match their old ones.
                                character_name_updated = 1
                                pass
                            if character_former_last_name != character_last_name:
                                character_name_updated = 1
                                pass
                            if licensed_hunter_role in ctx.author.roles:  # The functions in this block execute
                                # if the Licensed Hunter role is in the command invoker's roles.
                                # This check is here because it's very possible that a command invoker who updates
                                # their character information with a non-Aether character would no longer
                                # be able to see the channel that they invoked the command upon, due to permissions
                                # changing.
                                embed = discord.Embed(title="Update complete!", description="""Your \
information has been updated!""", color=discord.Color(0x00cc00))
                                if world_roles_updated_state == 0 and dc_roles_updated_state == 0:  # This executes
                                    # if the world and DC roles are the same as they were before the update.
                                    embed.add_field(name="Roles Updated:", value="No update!")
                                    pass
                                elif world_roles_updated_state == 0 and dc_roles_updated_state == 1:  # This executes
                                    # if the DC role is different, but the world role is the same.
                                    embed.add_field(name="Roles Updated:", value=f"{str(dc_roles_updated)}")
                                    pass
                                elif world_roles_updated_state == 1 and dc_roles_updated_state == 0:
                                    # This executes if the world role is different, but the DC role is the same.
                                    embed.add_field(name="Roles Updated:", value=f"{str(world_roles_updated)}")
                                    pass
                                elif world_roles_updated_state == 1 and dc_roles_updated_state == 1:  # This executes if
                                    # both world and DC are different.
                                    embed.add_field(name="Roles Updated:",
                                                    value=f"""{str(world_roles_updated)}
{str(dc_roles_updated)}""")
                                    pass
                                else:  # This should never execute, but is handled if it does.
                                    embed.add_field(name="ERROR:", value="Neither change state detected!!!")
                                    pass
                                if ctx.author.id == ctx.guild.owner_id:  # Sets the name changed embed field to the
                                    # Unchangeable message if the command invoker is the server's owner.
                                    embed.add_field(name="Unchangeable Name!", value="""Due to a Discord \
limitation, I am unable to change your name.""")
                                    pass
                                elif if_is_admin is not None:
                                    embed.add_field(name="Unchangeable Name!", value="""Due to a Discord limitation, I am \
                                unable to change your name.""")
                                    pass
                                elif character_name_updated == 0:  # Informs the command invoker that their name
                                    # needn't be changed.
                                    embed.add_field(name="Name Updated:", value="No update!")
                                    pass
                                elif character_name_updated == 1:  # Informs the command invoker that their name was
                                    # changed, and crosses out their old name.
                                    embed.add_field(name="Name Updated:",
                                                    value=f"""~~{character_former_first_name} \
{character_former_last_name}~~
{character_first_name} {character_last_name}""")
                                    pass
                                embed.set_thumbnail(url=character_avatar_url)
                                await ctx.send(embed=embed)
                                pass
                            elif licensed_hunter_role not in ctx.author.roles:  # Functions in this block execute if the
                                # command invoker does not have the Licensed Hunter role.
                                character_name_updated = 0
                                world_roles_updated_state = 0
                                dc_roles_updated_state = 0
                                if former_world_role.id != character_updated_world_role.id:  # Functions in the
                                    # following blocks are identical to those above.
                                    world_roles_updated = f"""- {former_world_role}
+ {character_updated_world_role}"""
                                    world_roles_updated_state = 1
                                    pass
                                elif former_world_role.id == character_updated_world_role.id:
                                    world_roles_updated = "** **"
                                    world_roles_updated_state = 0
                                    pass
                                if former_dc_role.id != character_updated_dc_role.id:
                                    dc_roles_updated = f"""- {former_dc_role}
+ {character_updated_dc_role}"""
                                    dc_roles_updated_state = 1
                                    pass
                                elif former_dc_role.id == character_updated_dc_role.id:
                                    dc_roles_updated = "** **"
                                    dc_roles_updated_state = 0
                                    pass
                                if character_former_first_name != character_first_name:
                                    character_name_updated = 1
                                    pass
                                if character_former_last_name != character_last_name:
                                    character_name_updated = 1
                                    pass
                                embed = discord.Embed(title="Update complete!", description="""Unfortunately, \
however, when updating your information, it was found that your new character was not on the Aether data center. \
Aether Hunts only caters to characters on Aether, and, as such, your permissions to view the Discord have been \
limited. You are welcome to re-attempt verification with a character on Aether to regain these permissions.""",
                                                      color=discord.Color(0x91002c))
                                # Informs the user that their update was complete, and that their permissions may have
                                # changed due to their character no longer being on Aether.
                                if world_roles_updated_state == 0 and dc_roles_updated_state == 0:
                                    embed.add_field(name="Roles Updated:", value="No update!")
                                    pass
                                elif world_roles_updated_state == 0 and dc_roles_updated_state == 1:
                                    embed.add_field(name="Roles Updated:",
                                                    value=f"""- {licensed_hunter_role}
{str(dc_roles_updated)}""")
                                    pass
                                elif world_roles_updated_state == 1 and dc_roles_updated_state == 0:
                                    embed.add_field(name="Roles Updated:", value=f"{str(world_roles_updated)}")
                                    pass
                                elif world_roles_updated_state == 1 and dc_roles_updated_state == 1:
                                    embed.add_field(name="Roles Updated:",
                                                    value=f"""- {licensed_hunter_role}
{str(world_roles_updated)}
{str(dc_roles_updated)}""")
                                    pass
                                else:
                                    embed.add_field(name="ERROR:", value="Neither change state detected!!!")
                                    pass
                                if ctx.author.id == ctx.guild.owner_id:
                                    embed.add_field(name="Unchangeable Name!", value="""Due to a Discord \
limitation, I am unable to change your name.""")
                                    pass
                                elif if_is_admin is not None:
                                    embed.add_field(name="Unchangeable Name!", value="""Due to a Discord limitation, I am \
                                unable to change your name.""")
                                    pass
                                elif character_name_updated == 0:
                                    embed.add_field(name="Name Updated:", value="No update!")
                                    pass
                                elif character_name_updated == 1:
                                    embed.add_field(name="Name Updated:",
                                                    value=f"""~~{character_former_first_name} \
{character_former_last_name}~~
{character_first_name} {character_last_name}""")
                                    pass
                                embed.set_thumbnail(url=character_avatar_url)
                                await ctx.send(embed=embed)
                                pass
                                await ctx.author.send(embed=embed)
                                pass
                            data["character_info"][f"{ctx.author.id}"].update(character_update)  # Updates the command
                            # invoker's character's information.
                            character__database.seek(0)  # Seeks to the beginning of the file.
                            json.dump(data, character__database, indent=2)  # Writes the information.
                            character__database.truncate()  # Truncates off any errant/additional characters that may
                            # have lingered, if the old content and the new content have different character lengths.
                            # Important, because the database gets fucky-wucky and all sorts of off-kilter if not
                            # included.
                            character__database.close()  # Closes the database.
                            return


@bot.command(pass_context=True, name="unlink", aliases=["ul"])  # Defines the unlink command.
async def unlink(ctx):
    """Deletes the current user's character information from the database."""
    if ctx.guild is None:  # Prevents the command from being run in a DM. The command would error anyway.
        await ctx.author.send("This command cannot be run in a DM! Please run it in the server.")
        return
    elif ctx.guild is not None:
        pass
    with open("characters.json", "r+") as character_database:  # Opens the database.
        data = json.load(character_database)  # Loads the database information.
        is_user_linked = re.search(rf"{ctx.author.id}", str(data))  # Checks if the command invoker is linked.
        if is_user_linked is None:  # Executes if the user is not linked.
            await ctx.send("You have no linked character!")
            return
        else:  # Executes if the user is linked.
            retrieved_world_name = data["character_info"][f"{ctx.author.id}"]["character_world_name"]
            # Retrieves the command invoker's character's world.
            retrieved_dc_name = data["character_info"][f"{ctx.author.id}"]["character_dc_name"]  # Retrieves the command
            # invoker's character's DC.
            world_role = discord.utils.get(ctx.guild.roles, name=retrieved_world_name)
            dc_role = discord.utils.get(ctx.guild.roles, name=retrieved_dc_name)
            licensed_hunter_role = discord.utils.get(ctx.guild.roles, name="Licensed Hunter")
            if world_role in ctx.author.roles:  # Executes if the command invoker's character's world role is in the
                # command invoker's roles.
                await ctx.author.remove_roles(world_role)
                pass
            elif world_role not in ctx.author.roles:  # Error handler.
                await ctx.author.send("""If you see this message, please report it to Dusk Argentum#6530, with the \
keywords: `Unlink: No world found!`""")
                pass
            if dc_role in ctx.author.roles:  # The same as above, but for DC.
                await ctx.author.remove_roles(dc_role)
                pass
            elif dc_role not in ctx.author.roles:  # DC error handler.
                await ctx.author.send("""If you see this message, please report it to Dusk Argentum#6530, with the \
keywords: `Unlink: No DC found!`""")
                pass
            if licensed_hunter_role in ctx.author.roles:  # Removes the Licensed Hunter role from the command
                # invoker if they have it.
                await ctx.author.remove_roles(licensed_hunter_role)
                pass
            elif licensed_hunter_role not in ctx.author.roles:
                pass
            del data["character_info"][f"{ctx.author.id}"]  # Deletes the command invoker's entry from the database.
            character_database.seek(0)  # Seeks to the beginning.
            json.dump(data, character_database, indent=2)  # "Writes" the deletion to the database.
            character_database.truncate()  # Truncates length.
            embed = discord.Embed(title="Character deleted.", description=f"""Your character has successfully been \
removed from the database. The associated roles have also been removed from you. Please note that if these roles \
contained the Licensed Hunter role, you will not be able to access the remainder of the Discord until you re-verify a \
character on the Aether datacenter using `{PREFIX}link`.""", color=discord.Color(0x57051a))
            # Informs the command invoker about the successful running, as well as their permissions changing.
            await ctx.author.send(embed=embed)  # Sends the above embed directly to the user.
            return


# RIP to discord.py, you were a real one. I learned Python because of you and am only where I am today thanks to you.
# Thank you to Danny and all discord.py contributors for your years of hard work. Discord is truly a better place
# because of you.

# I hope the future brings bright things.


bot.run(TOKEN)
