import os  # The os module. Used in Mudbot to call up environmental variables, which help obscure sensitive
# information.


import discord  # The Discord module. Used in Mudbot to do Discord things.
from discord.ext import commands, tasks  # Imports the commands and tasks submodules, for use in commands and tasks.
from discord.ext.commands import CommandInvokeError  # The following are error handling imports.
from discord.ext.commands import CommandNotFound


import random  # The random module. Used in Mudbot to generate random numbers when need be.


import re  # The re (regex) module. Extremely useful in gathering and paring down information from documents
# and other text strings.


import pyxivapi  # Imports pyxivapi. For linking. And maybe other stuff, down the line.
from pyxivapi.exceptions import XIVAPIForbidden, XIVAPIBadRequest, XIVAPINotFound, XIVAPIServiceUnavailable
from pyxivapi.exceptions import XIVAPIInvalidLanguage, XIVAPIInvalidIndex, XIVAPIInvalidColumns, XIVAPIInvalidFilter
from pyxivapi.exceptions import XIVAPIInvalidWorlds, XIVAPIInvalidDatacenter, XIVAPIError  # Pyxivapi's error handling.


import asyncio  # A pyxivapi dependency. Also used for sleeping when need be.
import aiohttp  # A web handler. Useful in grabbing information from the internet, eg. the Lodestone.


import json  # Json is used to keep track of imported character information and the like.


from datetime import datetime  # For use in getting times.
import pytz  # A timezone module.


PREFIX = "+"  # This defines the prefix for Mudbot. Commands MUST start with this character to be processed and run.
DESCRIPTION = "A proof of concept bot for use in the Aether Hunts Discord server. Made by Dusk Argentum#6530."
# This defines Mudbot's description.
TOKEN = os.environ.get("Mudbot_TOKEN")  # This defines the unique token used by Mudbot to log in to Discord.
# Stored in environmental variables for obscurity's sake.
XIVAPI_TOKEN = os.environ.get("Mudbot_XIVAPI")  # This defines the unique token used by Mudbot to log in to XIVAPI.


SHOULD_STATUS_CHANGE = 1  # A global variable that defines whether or not the bot's "Playing" status should change
# at any given time.
VERSION = "1.0.0"


bot = commands.Bot(command_prefix=commands.when_mentioned_or(PREFIX), description=DESCRIPTION, pm_help=False,
                   case_insensitive=True)  # Defines the bot as a bot.


bot.remove_command("help")  # Removes the in-built help command in favor of a custom one.


# ! EVENTS: These execute at varying times depending on their conditions.


@bot.event  # Defines the event to the bot.
async def on_ready():  # Functions in this block execute upon startup.
    await bot.change_presence(status=discord.Status.online, activity=discord.Game("w/ hunters! | +help"))
    # The above changes the bot's presence (status) to the specified "game" when starting up.
    status_rotation.start()  # This sets the status_rotation background task in motion.
    print("Mudbot online. Awaiting commands!")  # Prints to the console that the bot is ready to be used.


@bot.event
async def on_command_error(ctx, error):  # This is a general error-handling block.
    if isinstance(error, CommandNotFound):  # This executes if a command (or any message following the prefix) is used.
        error = "Command not found. View `+help` for valid commands."
    elif isinstance(error, CommandInvokeError):  # This executes if a command is used incorrectly, or in circumstances
        # where a command cannot finish executing properly and there is no specific handling for the error the command
        # invokes.
        error = "Incorrect invocation. Please re-examine the command in `+help`."
    await ctx.message.channel.send(f"Error: {error}")  # Sends the error message in the channel where the command was
    # invoked.


@bot.event
async def on_member_join(ctx):  # Functions in this block execute upon a member's joining.
    if ctx.guild.id == 725517856581746758:  # Functions in this block execute upon joining the Mudbot Testing Server.
        tz_utc = pytz.timezone("UTC")  # Defines the timezone to UTC.
        current_utc_time = datetime.now(tz_utc)  # Gets and defines the current time in UTC.
        join_log_channel = bot.get_channel(727920007690059936)  # Defines the join_log channel for join log messages.
        general_channel = bot.get_channel(725517857160691790)  # Defines the general_channel for welcome messages.
        tester_role = discord.utils.get(ctx.guild.roles, name="Tester")  # Defines the Tester role.
        embed = discord.Embed(title="Join Logged:", color=discord.Color(0x32a852))  # Defines and sets base parameters
        # for an embed.
        embed.add_field(name="User:", value=f"<@!{ctx.id}>\n{ctx.name}#{ctx.discriminator}\n({ctx.id})")
        # Defines the first field of the above embed with the title "User:" and the content as a mention of the joining
        # user, the user's Discord name and discrimination (eg. #1234), and the user's unique Snowflake ID.
        embed.add_field(name="Time:", value=f"""{current_utc_time.strftime("%m/%d/%Y @ %I:%M:%S %p %Z")}""")
        # Defines the second field of the above embed with the title "Time:", and sets the content as the current time,
        # with the format of month/day/year @ (at) hour:minute:second AM/PM UTC, eg. 07/19/20 @ 9:21:37 AM UTC.
        embed.set_thumbnail(url=ctx.avatar_url)  # Sets the thumbnail of the embed as the joining user's avatar.
        await join_log_channel.send(embed=embed)  # Sends the embed to the join log channel.
        await general_channel.send(f"Ohai, {ctx.mention}.")  # Sends a less formal welcome to the general channel.
        await ctx.add_roles(tester_role)  # Adds the previously-defined Tester role to the user.
        return  # Stops processing. Saves resource space. I think?
    if ctx.guild.id == 542602456132091904:  # Functions in this block execute upon joining the Aether Hunts server.
        tz_utc = pytz.timezone("UTC")  # The following functions are all identical to the above block's.
        current_utc_time = datetime.now(tz_utc)
        join_log_channel = bot.get_channel(573601933219332096)
        embed = discord.Embed(title="Join Logged:", color=discord.Color(0x32a852))
        embed.add_field(name="User:", value=f"<@!{ctx.id}>\n{ctx.name}#{ctx.discriminator}\n({ctx.id})")
        embed.add_field(name="Time:", value=f"""{current_utc_time.strftime("%m/%d/%Y @ %I:%M:%S %p %Z")}""")
        embed.set_thumbnail(url=ctx.avatar_url)
        await join_log_channel.send(embed=embed)
        return


# ! BACKGROUND TASKS:  These tasks execute in the background constantly.


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


# HELP COMMAND: This is the block where the help command is, which lists all commands and their arguments.
# Later, when it becomes necessary, every command will have its own separate help command, eg. !help link would show
# specific link command information


@bot.group(pass_context=True, name="help_", aliases=["cmds", "commands", "h", "help"])  # Defines the help command group
# and any of its aliases.
async def help_(ctx):
    """Shows a list of all commands, and whether or not a command has subcommands."""
    if ctx.invoked_subcommand is None:  # Functions in this block execute if no subcommands are invoked, eg. !help
        random_color = random.randint(1, 16777215)  # Generates a random color.
        embed = discord.Embed(title="Mudbot Commands", color=discord.Color(int(random_color)))  # Defines the beginning
        # of the embed, as well as setting its color to the random color generated above.
        embed.add_field(name="Verification", value="""`+info`
Shows your character information. Mention another user to view theirs.

`+link [first_name] [last_name] [world_name]`
Links your FFXIV character to your Discord name. This process may take up to one minute.

`+unlink`
Deletes the current user's character information from the database.""", inline=False)  # Lists all of the Verification
        # module's commands and their invocation examples.
        embed.set_footer(text=f"""To have the bot's help PM'd to you, put -pm after the command (eg. +help link -pm) |
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
    embed.add_field(name="Verification", value="""`+info`
Shows your character information. Mention another user to view theirs.

`+link [first_name] [last_name] [world_name]`
Links your FFXIV character to your Discord name. This process may take up to one minute.

`+unlink`
Deletes the current user's character information from the database.""", inline=False)
    embed.set_footer(text=f"""To have the bot's help PM'd to you, put -pm after the command (eg. +help link -pm) |
Current version: {VERSION} |
Made by Dusk Argentum#6530. |
Profile picture by Toast! Find them at https://twitter.com/pixel__toast""")  # Sets the footer.
    await ctx.send(embed=embed)
    return


# OWNER ONLY | These commands can only be run by Dusk Argentum#6530. These functions are used in the administration
# of the bot itself.


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


# VERIFICATION:


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
                embed.set_footer(text="""This info may not be up to date if this user hasn't updated in a while. | \
To update, use the +link command.""")
                await ctx.send(embed=embed)
                return


@bot.command(pass_context=True, name="link", aliases=["l"])  # Defines the linking command. Shit gets messy in here.
async def link(ctx, first_name: str = None, last_name: str = None, world_name: str = None):
    """Links your FFXIV character to your Discord name. This process may take up to one minute."""
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
        await ctx.send("""Could not complete operation! \
One or more arguments were missing, incomplete, or incorrect.
Proper use: `+link first_name last_name world_name`, ex. `+link Dusk Argentum Gilgamesh`.""")
        return
    if last_name is None:
        await ctx.send("""Could not complete operation! \
One or more arguments were missing, incomplete, or incorrect.
Proper use: `+link first_name last_name world_name`, ex. `+link Dusk Argentum Gilgamesh`.""")
        return
    if world_name is None:
        await ctx.send("""Could not complete operation! \
One or more arguments were missing, incomplete, or incorrect.
Proper use: `+link first_name last_name world_name`, ex. `+link Dusk Argentum Gilgamesh`.""")
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
If you're sure that information is correct, simply react with a thumbs-up and I will try again.
If you continue to see this error message, please wait a bit and try again. Thank you for your patience!""")
                    # A persistent error I keep running into is that occasionally (1/20?-ish), even if a search has
                    # all of the accurate information and arguments required, the Lodestone/XIVAPI will return an empty
                    # search string. The following block and the above message inform the user of this issue for
                    # transparency reasons. I would *love* to know why this shit keeps happening.
                    await retry.add_reaction("👍")  # Adds a thumbs up reaction to the above message, to prompt
                    # the command invoker to retry if they need to.

                    def check(reaction, user):  # The command only proceeds if the command invoker adds a thumbs up
                        # reaction to the above message.
                        return user == ctx.message.author and str(reaction.emoji) == "👍"

                    try:  # This try:except block only exists for timeout reasons.
                        reaction, user = await bot.wait_for("reaction_add", timeout=60.0, check=check)  # Checks to
                        # see if the command invoker has added a thumbs up reaction to the retry message.
                    except asyncio.TimeoutError:  # If the command invoker waits too long, this sends.
                        await ctx.send("Request has timed out. Please try again.")
                        return
                    else:  # Functions in this block execute if a thumbs up from the command invoker is found
                        # on the retry message.
                        await ctx.send("Retrying. Please wait, and thank you again for your patience.")
                        session = aiohttp.ClientSession()  # Just retries the search.
                        client = pyxivapi.XIVAPIClient(session=session, api_key=XIVAPI_TOKEN)
                        character_search = await client.character_search(world=world_name, forename=first_name,
                                                                         surname=last_name)
                        await session.close()
                        second_check_if_not_existent = re.search(r"{\'Page\': 0", str(character_search), re.IGNORECASE)
                        if second_check_if_not_existent is None:
                            pass
                        elif second_check_if_not_existent is not None:
                            await ctx.send(f"""I was not able to find **{first_name} {last_name}** of **{world_name}**.
Please wait and retry the command.""")
                            return
                character_id_search = re.search(r"(\'ID\': )(\d{1,10})", str(character_search), re.IGNORECASE)
                # Searches for the character's id from the returned Lodestone information.
                character_name_search = re.search(r"""(\'Name\': ['"])([a-z\-\']{1,15})\s([a-z\-\']{1,15})(['"])""",
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
                if character_world_name not in ctx.guild.roles:  # Checks if the character's world has a role on the
                    # server the command is invoked on and adds the role if it doesn't exist.
                    await ctx.guild.create_role(name=f"{character_world_name}")
                    pass
                elif character_world_name in ctx.guild.roles:
                    pass
                if character_dc_name not in ctx.guild.roles:  # Checks if the character's DC has a role on the server
                    # the command is invoked on and adds the role if it doesn't exist.
                    await ctx.guild.create_role(name=f"{character_dc_name}")
                    pass
                elif character_dc_name in ctx.guild.roles:
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
                            if ctx.author.id == ctx.guild.owner.id:  # Checks to see if the command invoker's id
                                # matches the server owner's id.
                                pass  # And skips changing their name. This is due to a Discord limitation; NOTHING,
                            # including bots, can change a server owner's name, except for the server owner themself.
                            # This used to cause the bot to stop dead in its tracks, but does not anymore.
                            elif ctx.author.id != ctx.guild.owner.id:  # Changes the command invoker's name
                                # to their character's name if they are not the server owner.
                                await ctx.author.edit(nick=f"{character_first_name} {character_last_name}")
                                pass
                            if character_dc_name == "Aether":  # The following block executes if the command invoker's
                                # character's DC is Aether.
                                embed = discord.Embed(title="Verification complete!", description="""Please feel free \
to peruse the React Roles category and pick up roles for anything you are interested in. Welcome to Aether Hunts!""",
                                                      color=discord.Color(0x00cc00))  # Defines the embed and sets
                                # some content.
                                embed.add_field(name="Roles Granted:",
                                                value=f"""<@&{licensed_hunter_role.id}>
<@&{world_role.id}>\n<@&{dc_role.id}>""")  # Informs the command invoker that their Licensed Hunter, world, and DC
                                # roles have been added.
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
                                                value="https://discord.gg/k4ZzY9B", inline=False)  # Primal Discord.
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
                            if ctx.author.id == ctx.guild.owner.id:  # This name field is added if the command invoker's
                                # id is the same as the server owner's id.
                                embed.add_field(name="Unchangeable Name!", value="""Due to a Discord limitation, I am \
unable to change your name.""")
                                pass
                            elif ctx.author.id != ctx.guild.owner.id:  # Informs the command invoker that their Discord
                                # name has changed and what it has been changed to.
                                embed.add_field(name="Name Changed:",
                                                value=f"{character_first_name} {character_last_name}")
                                pass
                            embed.set_thumbnail(url=character_avatar_url)
                            await ctx.send(embed=embed)
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
                            if character_dc_name == "Aether":  # Adds the Licensed Hunte role to a character who
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
                            await ctx.author.add_roles(character_updated_world_role)
                            await ctx.author.add_roles(character_updated_dc_role)
                            if ctx.author.id == ctx.guild.owner.id:
                                pass
                            elif ctx.author.id != ctx.guild.owner.id:  # Changes the command invoker's name to match
                                # their character's in game name.
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
                                if ctx.author.id == ctx.guild.owner.id:  # Sets the name changed embed field to the
                                    # Unchangeable message if the command invoker is the server's owner.
                                    embed.add_field(name="Unchangeable Name!", value="""Due to a Discord \
limitation, I am unable to change your name.""")
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
                                if ctx.author.id == ctx.guild.owner.id:
                                    embed.add_field(name="Unchangeable Name!", value="""Due to a Discord \
limitation, I am unable to change your name.""")
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


@bot.command(pass_context=True, name="unlink", aliases=["un"])  # Defines the unlink command.
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
            embed = discord.Embed(title="Character deleted.", description="""Your character has successfully been \
removed from the database. The associated roles have also been removed from you. Please note that if these roles \
contained the Licensed Hunter role, you will not be able to access the remainder of the Discord until you re-verify a \
character on the Aether datacenter using `+link`.""", color=discord.Color(0x57051a))
            # Informs the command invoker about the successful running, as well as their permissions changing.
            await ctx.author.send(embed=embed)  # Sends the above embed directly to the user.
            return


# TODO: Notes section.
# TODO: Figure out how to make a command to manage role react from in-server.
# TODO: For the above, make a command that makes the bot send a message with a defined name, and accepts arguments
# within to populate the message.
# TODO: Perhaps make a json with the different message IDs for later editing purposes?
# TODO: Which involves: Making and recognizing non-static role messages,
# TODO: Which involves: And making the bot add reactions autonomously to these new messages.


bot.run(TOKEN)