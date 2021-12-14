import asyncio


from bs4 import BeautifulSoup as Soup


import disnake
from disnake import Forbidden, HTTPException
from disnake.ext import commands
from disnake.ext.commands import MemberNotFound


import json


from mudbot import PREFIX


import os


import random  # Imports the random module for use in generating random numbers.


import re


import requests


import sqlite3
from sqlite3 import OperationalError


class Owner(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        return ctx.author.id == self.bot.owner_id

    @commands.command(aliases=["de"], brief="Echoes message.", help="Echoes message, deleting invocation.",
                      name="delete_echo", usage="delete_echo <message>")
    @commands.guild_only()
    async def delete_echo(self, ctx, *args):
        await ctx.message.delete()
        await ctx.send(" ".join(args))

    @commands.command(aliases=["fl"], brief="Forces verification for a user.", help="Forces verification for a user.",
                      name="force_link", usage=f"""force_link <user> <first> <last> <world>` OR `{PREFIX}force_veri \
<lodestone ID>`""")  # Force unlink coming soon to a Mudbot near you
    @commands.guild_only()
    async def force_link(self, ctx, member: disnake.Member = None, first: str = None, last: str = None,
                         world: str = None):
        wait = await ctx.send("""Attempting to verify this character... Please wait...
This could take up to a minute.""")  # Squeenix please give us a native Lodestone API.
        id_ = []
        if member is None:
            raise MemberNotFound
        if first.isnumeric() and first is not None:  # Functions in this block execute if the first name is a string
            # of numbers instead of a name. Bypasses searching for character ID using a name.
            id_ = first
            pass
        elif not first.isnumeric() and first is not None:  # Functions in this block execute if the first name is a
            # string of non-numeric things (for example, letters).
            if last is None or world is None:  # Functions in this block execute if either the last name or world name is not
                # provided.
                await wait.edit(content=f"""One or more arguments missing. Please ensure you are running the command \
properly.
Example: `{PREFIX}link Dusk Argentum Gilgamesh`""")  # Please do not attempt to verify as me.
                return
            first = first.lower()  # The following lines make every letter in the first, last, and world names
            # lowercase...
            last = last.lower()
            world = world.lower()
            first = first.capitalize()  # And then these following lines capitalize the first letter in each.
            last = last.capitalize()  # Breaks things, because the world gILGAMEsH isn't valid, for example.
            world = world.capitalize()
            async with ctx.typing():  # Shows a typing indicator while this long af process happens.
                r = (requests.get
                     (f"https://na.finalfantasyxiv.com/lodestone/character/?q={first}+{last}&worldname={world}"))
                # Makes a request to the Lodestone searching for the character with the given information.
            if r.status_code != 200:  # Functions in this block execute if the request did not receive a status 200
                # which is basically an "OK".
                await wait.edit(content=f"""Apologies for the inconvenience, but an error occurred.
`{r.status_code}`
If you see this message too many times, please open a support ticket.""")
                return
            html = Soup(r.text, "html.parser")  # Turns the HTML from the request into something parsable.
            not_found = html.select(".parts__zero")  # Selects the appropriate element, if it exists.
            if not_found:  # If the not_found element named above exists, functions in this block execute.
                # Only happens if information provided is incorrect,
                # Theoretically.
                await wait.edit(content=f"""There was no character with the name **{first} {last}** found on \
**{world}**.
Please make sure all inputs were spelled properly and try again.""")
                return
            character = []
            for character in html.select("div.entry"):  # Parses every character returned in the search.
                name = re.search(r"""entry__name\">([\w'-]{2,15})\s([\w'-]{2,15})<""",
                                 str(character.select(".entry__name")))
                if name is not None and f"{name.group(1)} {name.group(2)}" == f"{first} {last}":
                    break
                else:
                    continue
            else:
                if len(first) < 4 or len(last) < 4:
                    await wait.edit(content=f"""This character's name is too short to reliably find. Please try again \
using their Lodestone ID.
Example: `{PREFIX}link 22568447`.""")
                else:
                    await wait.edit(content=f"""There was no character with the name **{first} {last}** found on
**{world}**.
Please make sure all inputs were spelled properly and try again.""")
                return
            id_ = re.search(r"""/lodestone/character/(\d{1,10})/""", str(character.select(".entry__link"))).group(1)
            # The above gets the character ID of the found character, if a character is found.
        with open("server_config.json", "r") as server_config:
            data = json.load(server_config)
        if data["server_config"][str(ctx.guild.id)]["level_gate"]["state"] == "True":  # Functions in the following
            # blocks dictate how the level-gating function functions.
            async with ctx.typing():
                r = requests.get(f"https://na.finalfantasyxiv.com/lodestone/character/{id_}/class_job/")
            if r.status_code == 404:
                if first.isnumeric():
                    await wait.edit(content=f"""There was no character with the ID **{first}** found.
Please make sure all inputs were entered properly and try again.""")
                elif not first.isnumeric():
                    await wait.edit(content=f"""There was no character with the name **{first} {last}** found on \
**{world}**.
Please make sure all inputs were spelled properly and try again.""")
                return
            elif r.status_code != 200:
                await wait.edit(content=f"""Apologies for the inconvenience, but an error occurred.
`{r.status_code}`
If you see this message too many times, please open a support ticket.""")
                return
            html = Soup(r.text, "html.parser")
            class_above_threshold = False
            threshold = int(data["server_config"][str(ctx.guild.id)]["level_gate"]["level"])
            with open("classes.json", "r") as classes:
                data = json.load(classes)
            for count, class_ in enumerate(data["classes"]):
                level = re.search(r"""level\">(\d{2})<""", str(html.select(data["classes"][str(count)]["selector"])))
                if level is not None and int(level.group(1)) >= threshold:
                    class_above_threshold = True
                    break
            else:
                licensed_hunter = disnake.utils.get(ctx.guild.roles, name="Licensed Hunter")
                if licensed_hunter in ctx.author.roles:
                    await wait.edit(content="Bypassing level gate...")
                    pass
                elif licensed_hunter not in ctx.author.roles:
                    await wait.edit(content=f"""Apologies for the inconvenience, but the moderation team of this \
server has determined that only characters that have at least one class/job at level {threshold} will be able to make \
use of this server.
Please attempt to verify once again once you have at least one class/job at level {threshold}!""")
                    # Sorry to new players. You can join eventually. I prommy.
                    return
        async with ctx.typing():  # Gets the provided character's Lodestone page.
            r = requests.get(f"https://na.finalfantasyxiv.com/lodestone/character/{id_}/")
        if r.status_code == 404:  # Functions in this block execute if the status returned is 404, not found.
            await wait.edit(content=f"""There was no character with the name **{first} {last}** found on **{world}**.
Please make sure all inputs were spelled properly and try again.""")
            return
        elif r.status_code != 200:
            await wait.edit(content=f"""Apologies for the inconvenience, but an error occurred.
`{r.status_code}`
If you see this message too many times, please open a support ticket.""")
            return
        html = Soup(r.text, "html.parser")
        name = re.search(r"""chara__name\">([\w'-]{2,15})\s([\w'-]{2,15})<""",
                         str(html.select("div.frame__chara__box:nth-child(2) > .frame__chara__name")))
        # Grabs the name.
        world = re.search(r"""World\"></i>(\w{4,12})\s\((\w{4,9})""",
                          str(html.select("p.frame__chara__world:last-of-type")))
        # Grabs the world.
        portrait = re.search(r"""src=\"(\S+)\"""", str(html.select(".frame__chara__face > img:nth-child(1)"))).group(1)
        # Grabs the portrait.
        dc = world.group(2)  # Gets the DC from the second group in the world selection.
        first = name.group(1)  # Gets the first name from the first group in the name selection.
        last = name.group(2)  # And so on and so forth.
        portrait = portrait
        server = world.group(1)
        if first == "Dusk" and last == "Argentum" and ctx.author.id != self.bot.owner_id:
            embed = disnake.Embed(color=disnake.Color(0x3b9da5), description=f"""Please read the verification \
instructions more clearly. You have attempted to verify as the example character.
Proper usage:
`{PREFIX}link <first_name> <last_name> <world_name>`""", title="Whoops!")
            # No verifying as me! No doubles!
            embed.set_author(icon_url=self.bot.user.avatar.url, name=self.bot.user.name)
            embed.set_thumbnail(url=self.bot.user.avatar.url)
            embed.set_footer(icon_url=ctx.guild.icon.url, text=ctx.guild.name)
            await wait.edit(content=None, embed=embed)
            return
        new = [id_, dc, first, last, portrait, server]  # Sets a list of the new information.
        try:
            con = sqlite3.connect("characters.db", timeout=30.0)
        except OperationalError:
            await wait.edit(content="Please wait a moment and try again.")
            return
        cur = con.cursor()
        cur.execute("SELECT discord_id FROM characters")
        ids = cur.fetchall()
        con.close()
        new_diff = []  # Sets an empty list for the new stuff.
        old_diff = []  # Sets an empty list for the old stuff.
        old = []  # Sets an empty list for the old..?
        if str(member.id) in str(ids):
            attributes = ["character_id", "dc", "first", "last", "portrait", "server"]
            try:
                con = sqlite3.connect("characters.db", timeout=30.0)
            except OperationalError:
                await wait.edit(content="Please wait a moment and try again.")
                return
            cur = con.cursor()
            for attribute in attributes:
                cur.execute(f"SELECT {attribute} FROM characters WHERE discord_id = '{str(member.id)}'")
                details = re.search(r"\([\'\"](.+)[\'\"],\)", str(cur.fetchall()))
                old.append(details.group(1))
            con.close()
            for count, attribute in enumerate(new):  # Functions in this loop execute for every thing in the new list.
                if attribute == old[count]:  # Functions in this block execute if the old attribute and new one
                    # are the same.
                    if count == 0 or count == 4:  # But ignores character ID and portrait.
                        continue  # Because those aren't displayed.
                    new_diff.append("")
                    old_diff.append("")
                elif attribute != old[count]:
                    if count == 0 or count == 4:
                        continue
                    new_diff.append(new[count])
                    old_diff.append(old[count])
            with open("worlds.json", "r+") as worlds:
                d = json.load(worlds)  # d is used instead of data cuz I wrote this line after I had already used
                # the data name for a different variable and didn't feel like rewriting it.
            try:
                con = sqlite3.connect("characters.db", timeout=30.0)
            except OperationalError:
                await wait.edit(content="Please wait a moment and try again.")
                return
            cur = con.cursor()
            for count, unused in enumerate(new):  # Functions in this block update information to the new stuff.
                if new[count] != old[count]:
                    update = f"UPDATE characters SET {attributes[count]} = ? WHERE discord_id = ?"
                    data = (new[count], str(member.id))
                    con.execute(update, data)
                if count == 2:
                    first = new[2]
                if count == 3:
                    last = new[3]
            con.commit()  # Commits the new information.
            con.close()
            new_dc = disnake.utils.get(ctx.guild.roles, name=new[1])
            if new_dc not in ctx.guild.roles:  # Functions in this block execute if the DC name is not in the guild's
                # role list. Basically just future-proofing.
                await ctx.guild.create_role(name=new[1])
                world_update = {str(int(len(d["worlds"]["dcs"])) + 2): {
                    "name": new[1]
                    }
                }
                d["worlds"]["dcs"].update(world_update)
                worlds.seek(0)
                json.dump(d, worlds, indent=4)
                worlds.truncate()
            old_dc = disnake.utils.get(ctx.guild.roles, name=old[1])  # The following functions remove old stuff and
            # add the new stuff.
            if old_dc in member.roles:
                try:
                    await member.remove_roles(old_dc)
                except (Forbidden, HTTPException):
                    pass
            elif old_dc not in member.roles:
                for count, unused in enumerate(d["worlds"]["dcs"]):
                    role = str(d["worlds"]["dcs"][str(count)]["name"])
                    if role in str(member.roles) and role != new_dc.name:
                        old_dc = disnake.utils.get(ctx.guild.roles, name=role)
                        try:
                            await member.remove_roles(old_dc)
                        except (Forbidden, HTTPException):
                            pass
            try:
                await member.add_roles(new_dc)
            except (Forbidden, HTTPException):
                pass
            try:  # The following function changes the member's name. If it can.
                await member.edit(nick=f"{first} {last}")
            except (Forbidden, HTTPException):
                pass
            new_server = disnake.utils.get(ctx.guild.roles, name=new[5])  # Same stuff as DC.
            if new_server not in ctx.guild.roles:
                await ctx.guild.create_role(name=new[5])
                world_update = {str(int(len(d["worlds"]["servers"])) + 2): {
                    "name": new[5]
                    }
                }
                d["worlds"]["servers"].update(world_update)
                worlds.seek(0)
                json.dump(d, worlds, indent=4)
                worlds.truncate()
            old_server = disnake.utils.get(ctx.guild.roles, name=old[5])
            if old_server in member.roles:
                try:
                    await member.remove_roles(old_server)
                except (Forbidden, HTTPException):
                    pass
            elif old_server not in member.roles:
                for count, unused in enumerate(d["worlds"]["servers"]):
                    role = str(d["worlds"]["servers"][str(count)]["name"])
                    if role in str(member.roles) and role != new_server.name:
                        old_server = disnake.utils.get(ctx.guild.roles, name=role)
                        try:
                            await member.remove_roles(old_server)
                        except (Forbidden, HTTPException):
                            pass
            try:
                await member.add_roles(new_server)
            except (Forbidden, HTTPException):
                pass
        elif str(member.id) not in str(ids):  # Functions in this block execute if the member is not already in
            # the database.
            try:
                con = sqlite3.connect("characters.db", timeout=30.0)
            except OperationalError:
                await wait.edit(content="Please wait a moment and try again.")
                return
            cur = con.cursor()
            cur.execute("""INSERT INTO characters VALUES (?, ?, ?, ?, ?, ?, ?)""",  # Makes a new row with the
                        # provided information.
                        (str(member.id), str(id_), dc, first, last, portrait, server))
            con.commit()
            con.close()
            licensed_hunter = disnake.utils.get(ctx.guild.roles, name="Licensed Hunter")
            if licensed_hunter in member.roles:
                worlds_list = []
                with open("worlds.json", "r") as worlds:
                    d = json.load(worlds)
                for count, world in enumerate(d["worlds"]["dcs"]):
                    worlds_list.append(d["worlds"]["dcs"][str(count)]["name"])
                for count, world in enumerate(d["worlds"]["servers"]):
                    worlds_list.append(d["worlds"]["servers"][str(count)]["name"])
                for role in ctx.author.roles:
                    if role.name in worlds_list:
                        for world in worlds_list:
                            if role.name == world:
                                await member.remove_roles(role)
            if dc not in str(ctx.guild.roles):
                await ctx.guild.create_role(name=dc)
            dc_role = disnake.utils.get(ctx.guild.roles, name=dc)
            try:
                await member.add_roles(dc_role)
            except (Forbidden, HTTPException):
                pass
            try:
                await member.edit(nick=f"{first} {last}")
            except (Forbidden, HTTPException):
                pass
            if server not in str(ctx.guild.roles):
                await ctx.guild.create_role(name=server)
            server_role = disnake.utils.get(ctx.guild.roles, name=server)
            try:
                await member.add_roles(server_role)
            except (Forbidden, HTTPException):
                pass
        description = "** **"  # Sets a blank description, to be edited. Usually.
        licensed_hunter = disnake.utils.get(ctx.guild.roles, name="Licensed Hunter")
        licensed_viewer = disnake.utils.get(ctx.guild.roles, name="Licensed Viewer")
        if "Aether" in new[1]:  # Functions in this block execute if the member is from Aether.
            if ctx.channel.id == 738670827490377800:
                await member.add_roles(licensed_viewer)
            await member.add_roles(licensed_hunter)
            if str(member.id) in str(ids) and ctx.channel.id == 738670827490377800:
                description = """Welcome back! Be sure to peruse <#865129809452728351> to add Hunt-related roles to \
yourself."""
            elif str(member.id) in str(ids) and ctx.channel.id != 738670827490377800:
                description = """Information updated! Thank you for taking the time to keep your information \
up-to-date."""
            elif str(member.id) not in str(ids):
                description = """Welcome to Aether Hunts! Be sure to peruse <#865129809452728351> to add Hunt-related \
roles to yourself."""
        elif "Aether" not in new[1]:  # Functions in this block execute if the member is not from Aether.
            if licensed_hunter in member.roles:
                await member.remove_roles(licensed_hunter)
            description = """Thank you for verifying! Unfortunately, Aether Hunts is a community dedicated to hunting \
on the Aether datacenter, and you have verified with a character not on Aether.
You're welcome to attempt the linking process again with a character on Aether, though! We'd love to have you."""
        embed = disnake.Embed(color=disnake.Color(0x3b9da5), description=description, title="Verification complete!")
        embed.set_author(icon_url=self.bot.user.avatar.url, name=self.bot.user.name)
        embed.set_thumbnail(url=portrait)
        if str(member.id) in str(ids):  # Functions in this block execute if the member is not already in the
            # database.
            if new_diff[0] is not None and old_diff[0] is not None and new_diff[0] in str(ctx.guild.roles) \
                    and old_diff[0] in str(ctx.guild.roles):
                new_diff[0] = disnake.utils.get(ctx.guild.roles, name=new_diff[0])
                old_diff[0] = disnake.utils.get(ctx.guild.roles, name=old_diff[0])
            if new_diff[3] is not None and old_diff[3] is not None and new_diff[3] in str(ctx.guild.roles) \
                    and old_diff[3] in str(ctx.guild.roles):
                new_diff[3] = disnake.utils.get(ctx.guild.roles, name=new_diff[3])
                old_diff[3] = disnake.utils.get(ctx.guild.roles, name=old_diff[3])
            arrow_value = []
            new_value = []
            old_value = []
            for count, diff in enumerate(new_diff):
                if isinstance(new_diff[count], disnake.Role):
                    new_value.append(new_diff[count].mention)
                elif isinstance(new_diff[count], str):
                    if new_diff[count] == "":
                        pass
                    elif new_diff[count] != "":
                        new_value.append(new_diff[count])
            for count, diff in enumerate(old_diff):
                if isinstance(old_diff[count], disnake.Role):
                    if old_diff[count] == "":
                        pass
                    elif old_diff[count] != "":
                        old_value.append(f"~~{old_diff[count].mention}~~")
                elif isinstance(old_diff[count], str):
                    if old_diff[count] == "":
                        pass
                    elif old_diff[count] != "":
                        old_value.append(f"~~{old_diff[count]}~~")
            for value in new_value:
                arrow_value.append("►")
            if "Aether" in new[1] and licensed_viewer in member.roles:
                arrow_value.append("+")
                new_value.append(licensed_hunter.mention)
                old_value.append("** **")
            arrow_value = "\n".join(arrow_value)
            new_value = "\n".join(new_value)
            old_value = "\n".join(old_value)
            if new_diff[0] is None and len(new_diff[1]) == 0 and len(new_diff[2]) == 0 and new_diff[3] is None \
                    and old_diff[0] is None and len(old_diff[1]) == 0 and len(old_diff[2]) == 0 and old_diff[3] is None:
                arrow_value = "<:dusk:906079428524777524>"  # Me face.
                old_value = "Nothing changed!"
                new_value = "You're good to go!"
            embed.add_field(inline=True, name="Old:", value=old_value)
            embed.add_field(inline=True, name="►", value=arrow_value)
            embed.add_field(inline=True, name="New:", value=new_value)  # This stuff looks weird in certain
            # circumstances. Requires further testing and the ability to know how it happens to fix. Effects nothing
            # functionally, just cosmetically.
        elif str(member.id) not in str(ids):  # Another block that executes if the member is not in the database.
            added_names = []
            added_roles = []
            for item in new:  # Functions in this loop add to lists that show what information changed.
                if item == new[1] or item == new[5]:
                    role = disnake.utils.get(ctx.guild.roles, name=item)
                    added_roles.append(role)
                if item == new[1] == "Aether":
                    added_roles.append(licensed_hunter)
                elif item == new[2] or item == new[3]:
                    added_names.append(item)
            value = []
            for item in added_roles and added_roles:
                if isinstance(item, disnake.Role):
                    value.append(item.mention)
            embed.add_field(inline=True, name="Added:", value="\n".join(value))
            embed.add_field(inline=True, name="Name Changed:", value=" ".join(added_names))
        if "Aether" not in new[1]:  # Functions in this block execute if the member is not on Aether.
            if "Crystal" in new[1]:
                embed.add_field(inline=False, name="Crystal Hunts:", value="""Looks like you verified with a \
character on the Crystal datacenter! Here's a link to their Hunting Discord.
[Invite](https://discord.gg/S8fKQvh)""")
            elif "Light" in new[1]:
                embed.add_field(inline=False, name="Clan Centurio:", value="""Looks like you verified with a \
character on the Light datacenter! Here's a link to their Hunting Discord.
[Invite](https://discord.gg/h52Uzm4)""")
            elif "Primal" in new[1]:
                embed.add_field(inline=False, name="The Coeurl:", value="""Looks like you verified with a \
character on the Primal datacenter! Here's a link to their Hunting Discord.
[Invite](https://discord.gg/k4xNWdV)""")
        embed.set_footer(icon_url=ctx.guild.icon.url, text=ctx.guild.name)
        await wait.edit(content=None, embed=embed)

    @commands.command(aliases=["inv"], brief="Sends invite link.", help="Sends invite link.", name="invite",
                      usage="invite")
    @commands.guild_only()
    async def invite(self, ctx):
        await ctx.send(str(os.environ.get("Mudbot_Invite")))

    @commands.command(aliases=["bye"], brief="Leaves the provided server.", help="""Leaves the provided server. \
Leaves the current server if none is provided. Accept only IDs.""", usage="leave (server_id)")
    @commands.guild_only()
    async def leave(self, ctx, server: int = None):
        if server is None:
            server = self.bot.get_guild(ctx.guild.id)
        elif server is not None:
            server = self.bot.get_guild(server)
        await server.leave()

    @commands.command(aliases=["server_list"], brief="Lists servers the bot is on.",
                      help="Lists servers the bot is on.", name="list", usage="list")
    @commands.guild_only()
    async def list(self, ctx):
        servers = []
        for server in self.bot.guilds:
            servers.append(f"{server.name} (`{server.id}`)\n")
            await asyncio.sleep(1)
        await ctx.author.send(servers)

    @commands.group(aliases=["stat"], brief="Commands for adjusting bot status.", case_insensitive=True,
                    help="""Commands for adjusting the bot's status, including toggling auto-rotation on/off \
and custom statuses.""", name="status", usage="status [subcommand] <argument>")
    @commands.guild_only()
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
    @commands.guild_only()
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
    @commands.guild_only()
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
    @commands.guild_only()
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
    @commands.guild_only()
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
