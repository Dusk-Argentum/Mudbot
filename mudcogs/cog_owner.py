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


from typing import Union


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
                      name="force_link", usage=f"""force_link <user> <first> <last> <world>` OR `{PREFIX}force_link \
<lodestone ID>""")  # Comments on force_link and force_unlink can be found in the Verification cog.
    @commands.guild_only()
    async def force_link(self, ctx, member: disnake.Member = None, first: str = None, last: str = None,
                         world: str = None):
        wait = await ctx.send("""Attempting to verify this character... Please wait...
This could take up to a minute.""")
        id_ = []
        if member is None:
            raise MemberNotFound
        if first.isnumeric() and first is not None:
            id_ = first
            pass
        elif not first.isnumeric() and first is not None:
            if last is None or world is None:
                await wait.edit(content=f"""One or more arguments missing. Please ensure you are running the command \
properly.
Example: `{PREFIX}link Dusk Argentum Gilgamesh`""")
                return
            first = first.lower()
            last = last.lower()
            world = world.lower()
            first = first.capitalize()
            last = last.capitalize()
            world = world.capitalize()
            async with ctx.typing():
                r = (requests.get
                     (f"https://na.finalfantasyxiv.com/lodestone/character/?q={first}+{last}&worldname={world}"))
            if r.status_code != 200:
                await wait.edit(content=f"""Apologies for the inconvenience, but an error occurred.
`{r.status_code}`
If you see this message too many times, please open a support ticket.""")
                return
            html = Soup(r.text, "html.parser")
            not_found = html.select(".parts__zero")
            if not_found:
                await wait.edit(content=f"""There was no character with the name **{first} {last}** found on \
**{world}**.
Please make sure all inputs were spelled properly and try again.""")
                return
            character = []
            for character in html.select("div.entry"):
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
        with open("server_config.json", "r") as server_config:
            data = json.load(server_config)
        if data["server_config"][str(ctx.guild.id)]["level_gate"]["state"] == "True":
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
                    return
        async with ctx.typing():
            r = requests.get(f"https://na.finalfantasyxiv.com/lodestone/character/{id_}/")
        if r.status_code == 404:
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
        world = re.search(r"(\w{4,12})\s\[(\w{4,9})]",
                          str(html.select("p.frame__chara__world:last-of-type")))
        portrait = re.search(r"""src=\"(\S+)\"""", str(html.select(".frame__chara__face > img:nth-child(1)"))).group(1)
        dc = world.group(2)
        first = name.group(1)
        last = name.group(2)
        portrait = portrait
        server = world.group(1)
        if first == "Dusk" and last == "Argentum" and ctx.author.id != self.bot.owner_id:
            embed = disnake.Embed(color=disnake.Color(0x3b9da5), description=f"""Please read the verification \
instructions more clearly. You have attempted to verify as the example character.
Proper usage:
`{PREFIX}link <first_name> <last_name> <world_name>`""", title="Whoops!")
            embed.set_author(icon_url=self.bot.user.avatar.url, name=self.bot.user.name)
            embed.set_thumbnail(url=self.bot.user.avatar.url)
            embed.set_footer(icon_url=ctx.guild.icon.url, text=ctx.guild.name)
            await wait.edit(content=None, embed=embed)
            return
        new = [id_, dc, first, last, portrait, server]
        try:
            con = sqlite3.connect("characters.db", timeout=30.0)
        except OperationalError:
            await wait.edit(content="Please wait a moment and try again.")
            return
        cur = con.cursor()
        cur.execute("SELECT discord_id FROM characters")
        ids = cur.fetchall()
        con.close()
        new_diff = []
        old_diff = []
        old = []
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
            for count, attribute in enumerate(new):
                if attribute == old[count]:
                    if count == 0 or count == 4:
                        continue
                    new_diff.append("")
                    old_diff.append("")
                elif attribute != old[count]:
                    if count == 0 or count == 4:
                        continue
                    new_diff.append(new[count])
                    old_diff.append(old[count])
            with open("worlds.json", "r+") as worlds:
                d = json.load(worlds)
            try:
                con = sqlite3.connect("characters.db", timeout=30.0)
            except OperationalError:
                await wait.edit(content="Please wait a moment and try again.")
                return
            cur = con.cursor()
            for count, unused in enumerate(new):
                if new[count] != old[count]:
                    update = f"UPDATE characters SET {attributes[count]} = ? WHERE discord_id = ?"
                    data = (new[count], str(member.id))
                    con.execute(update, data)
                if count == 2:
                    first = new[2]
                if count == 3:
                    last = new[3]
            con.commit()
            con.close()
            new_dc = disnake.utils.get(ctx.guild.roles, name=new[1])
            if new_dc not in ctx.guild.roles:
                await ctx.guild.create_role(name=new[1])
                world_update = {str(int(len(d["worlds"]["dcs"])) + 2): {
                    "name": new[1]
                    }
                }
                d["worlds"]["dcs"].update(world_update)
                worlds.seek(0)
                json.dump(d, worlds, indent=4)
                worlds.truncate()
            old_dc = disnake.utils.get(ctx.guild.roles, name=old[1])
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
            try:
                await member.edit(nick=f"{first} {last}")
            except (Forbidden, HTTPException):
                pass
            new_server = disnake.utils.get(ctx.guild.roles, name=new[5])
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
        elif str(member.id) not in str(ids):
            try:
                con = sqlite3.connect("characters.db", timeout=30.0)
            except OperationalError:
                await wait.edit(content="Please wait a moment and try again.")
                return
            cur = con.cursor()
            cur.execute("""INSERT INTO characters VALUES (?, ?, ?, ?, ?, ?, ?)""",
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
        description = "** **"
        licensed_hunter = disnake.utils.get(ctx.guild.roles, name="Licensed Hunter")
        licensed_viewer = disnake.utils.get(ctx.guild.roles, name="Licensed Viewer")
        accepted_dcs = ["Aether"]  # A list of DCs to applied the Licensed Hunter role to.
        accepted_visitors = ["Aether", "Crystal", "Primal"]
        if new[1] in accepted_dcs:  # Functions in this block execute if the member is from Aether.
            if ctx.channel.id == 738670827490377800:
                await ctx.author.add_roles(licensed_viewer)
            await ctx.author.add_roles(licensed_hunter)
            if str(ctx.author.id) in str(ids) and ctx.channel.id == 738670827490377800:
                description = """Welcome back! Be sure to peruse <#865129809452728351> to add Hunt-related roles to \
yourself."""
            elif str(ctx.author.id) in str(ids) and ctx.channel.id != 738670827490377800:
                description = """Information updated! Thank you for taking the time to keep your information \
up-to-date."""
            elif str(ctx.author.id) not in str(ids):
                description = """Welcome to Aether Hunts! Be sure to peruse <#865129809452728351> to add Hunt-related \
roles to yourself."""
        elif new[1] not in accepted_visitors:  # Functions in this block execute if the member is not from Aether.
            if licensed_hunter in ctx.author.roles:
                await ctx.author.remove_roles(licensed_hunter)
            description = """Thank you for verifying! Unfortunately, Aether Hunts is a community dedicated to hunting \
on the Aether datacenter, and you have verified with a character not on Aether.
You're welcome to attempt the linking process again with a character on Aether, though! We'd love to have you."""
        embed = disnake.Embed(color=disnake.Color(0x3b9da5), description=description, title="Verification complete!")
        embed.set_author(icon_url=self.bot.user.avatar.url, name=self.bot.user.name)
        embed.set_thumbnail(url=portrait)
        if str(member.id) in str(ids):
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
                arrow_value = "<:dusk:906079428524777524>"
                old_value = "Nothing changed!"
                new_value = "You're good to go!"
            embed.add_field(inline=True, name="Old:", value=old_value)
            embed.add_field(inline=True, name="►", value=arrow_value)
            embed.add_field(inline=True, name="New:", value=new_value)
        elif str(member.id) not in str(ids):
            added_names = []
            added_roles = []
            for item in new:
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
character on the Crystal Datacenter!
We are now offering limited usage of our Discord to the other NA Datacenters, so members from those Datacenters can \
receive Hunt callouts on Aether while they are visiting!
Please head to <#591099527667253248> and follow the instructions within to opt-in.

Please also feel free to join your Datacenter's native Hunt Discord for Hunt callouts on your own Datacenter!
[Invite](https://discord.gg/S8fKQvh)""")
                elif "Light" in new[1]:
                    embed.add_field(inline=False, name="Clan Centurio:", value="""Looks like you verified with a \
character on the Light datacenter! Here's a link to their Hunting Discord.
[Invite](https://discord.gg/h52Uzm4)""")
                elif "Primal" in new[1]:
                    embed.add_field(inline=False, name="The Coeurl:", value="""Looks like you verified with a \
character on the Primal Datacenter!
We are now offering limited usage of our Discord to the other NA Datacenters, so members from those Datacenters can \
receive Hunt callouts on Aether while they are visiting!
Please head to <#591099527667253248> and follow the instructions within to opt-in.

Please also feel free to join your Datacenter's native Hunt Discord for Hunt callouts on your own Datacenter!
[Invite](https://discord.gg/k4xNWdV)""")
        embed.set_footer(icon_url=ctx.guild.icon.url, text=ctx.guild.name)
        await wait.edit(content=None, embed=embed)

    @commands.command(aliases=["fun"], brief="Forces a user to unlink and removes their roles.", help="""Forces a \
user to unlink and removes their roles.""", name="force_unlink", usage="force_unlink <@mention>`/`<ID>")
    @commands.guild_only()
    async def force_unlink(self, ctx, user: Union[disnake.Member, disnake.User] = None):
        confirm = await ctx.send("""Unlinking this account will remove all their roles and remove their access to the \
server.
        Proceed?""")
        await confirm.add_reaction("👍")
        await confirm.add_reaction("👎")
        reactions = ["👍", "👎"]

        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in reactions

        try:
            reaction, users = await self.bot.wait_for("reaction_add", timeout=60, check=check)
        except TimeoutError:
            await confirm.edit(content="Unlinking aborted. Neither accepted reaction added.")
            await confirm.clear_reactions()
            return
        if str(reaction.emoji) == "👎":
            await confirm.edit(content="Unlinking aborted.")
            await confirm.clear_reactions()
            return
        try:
            con = sqlite3.connect("characters.db", timeout=30.0)
        except OperationalError:
            await confirm.edit(content="Please wait a moment and try again.")
            return
        cur = con.cursor()
        cur.execute("SELECT discord_id FROM characters")
        ids = cur.fetchall()
        con.close()
        for id_ in ids:
            id_ = re.search(r"\(\'(\d+)\',", str(id_))
            if id_.group(1) == str(user.id):
                break
        else:
            await confirm.edit(content="They are not in my database.")
            return
        try:
            con = sqlite3.connect("characters.db", timeout=30.0)
        except OperationalError:
            await confirm.edit(content="Please wait a moment and try again.")
            return
        cur = con.cursor()
        con.execute(f"DELETE FROM characters WHERE discord_id = '{str(user.id)}'")
        con.commit()
        con.close()
        if isinstance(user, disnake.Member):
            for role in user.roles:
                try:
                    await user.remove_roles(role)
                except (Forbidden, HTTPException):
                    continue
        await ctx.send("That user has been successfully unverified and must now repeat the verification process.")

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

    @commands.command(aliases=["vr"], brief="Removes all members from Licensed Viewer.", help="""Removes all members \
from Licensed Viewer.""", name="viewer_removal", usage="viewer_removal")
    @commands.guild_only()
    async def viewer_removal(self, ctx):
        viewer = disnake.utils.get(ctx.guild.roles, name="Licensed Viewer")
        count = 0
        for member in ctx.guild.members:
            if viewer in member.roles:
                await member.remove_roles(viewer)
                count += 1
        await ctx.send(f"Removed Licensed Viewer from {count} member{'s' if count != 1 else ''}.")


def setup(bot):
    bot.add_cog(Owner(bot))
