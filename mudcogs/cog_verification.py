import asyncio


from bs4 import BeautifulSoup as soup


from datetime import datetime, timezone


import json


import discord
from discord import Forbidden, HTTPException
from discord.ext import commands


from mudbot import PREFIX


import re


import requests


import sqlite3


class Verification(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=["id_link", "l"], brief="Links your FFXIV character to your Discord.",
                      help="""Links your FFXIV character to your Discord or updates it if already linked. Accepts \
`[first] [last] [world]` and `[lodestone ID]`.""", name="link", usage=f"""link [first] [last] [world]` OR \
`{PREFIX}link [lodestone ID]""")
    @commands.guild_only()
    async def link(self, ctx, first: str = None, last: str = None, world: str = None):
        wait = await ctx.send("""Attempting to verify your character... Please wait...
This process can take up to thirty seconds.""")
        id_ = []
        if first.isnumeric() and first is not None:
            id_ = first
            pass
        elif not first.isnumeric() and first is not None:
            if (last, world) is None:
                await ctx.send(f"""One or more arguments missing. Please ensure you are running the command properly.
Example: `{PREFIX}link Dusk Argentum Gilgamesh`""")
                await wait.delete()
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
                await ctx.send(f"""Apologies for the inconvenience, but an error occurred.
`{r.status_code}`
If you see this message too many times, please open a support ticket.""")
                await wait.delete()
                return
            html = soup(r.text, "html.parser")
            not_found = html.select(".parts__zero")
            if not_found:
                await ctx.send(f"""There was no character with the name **{first} {last}** found on **{world}**.
Please make sure all inputs were spelled properly and try again.""")
                await wait.delete()
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
                await ctx.send(f"""There was no character with the name **{first} {last}** found on **{world}**.
Please make sure all inputs were spelled properly and try again.""")
                await wait.delete()
                return
            id_ = re.search(r"""/lodestone/character/(\d{1,10})/""", str(character.select(".entry__link"))).group(1)
        with open("server_config.json", "r") as server_config:
            data = json.load(server_config)
        if data["server_config"][str(ctx.guild.id)]["level_gate"]["state"] == "True":
            async with ctx.typing():
                r = requests.get(f"https://na.finalfantasyxiv.com/lodestone/character/{id_}/class_job/")
            if r.status_code == 404:
                await ctx.send(f"""There was no character with the name **{first} {last}** found on **{world}**.
Please make sure all inputs were spelled properly and try again.""")
                await wait.delete()
                return
            elif r.status_code != 200:
                await ctx.send(f"""Apologies for the inconvenience, but an error occurred.
`{r.status_code}`
If you see this message too many times, please open a support ticket.""")
                await wait.delete()
                return
            html = soup(r.text, "html.parser")
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
                await ctx.send(f"""Apologies for the inconvenience, but the moderation team of this server \
has determined that only characters that have at least one class/job at level {threshold} will be able to make use of \
this server.
Please attempt to verify once again once you have at least one class/job at level {threshold}!""")
                await wait.delete()
                return
        async with ctx.typing():
            r = requests.get(f"https://na.finalfantasyxiv.com/lodestone/character/{id_}/")
        if r.status_code == 404:
            await ctx.send(f"""There was no character with the name **{first} {last}** found on **{world}**.
Please make sure all inputs were spelled properly and try again.""")
            await wait.delete()
            return
        elif r.status_code != 200:
            await ctx.send(f"""Apologies for the inconvenience, but an error occurred.
`{r.status_code}`
If you see this message too many times, please open a support ticket.""")
            await wait.delete()
            return
        html = soup(r.text, "html.parser")
        name = re.search(r"""chara__name\">([\w'-]{2,15})\s([\w'-]{2,15})<""",
                         str(html.select("div.frame__chara__box:nth-child(2) > .frame__chara__name")))
        world = re.search(r"""World\"></i>(\w{4,12})\s\((\w{4,9})""",
                          str(html.select("p.frame__chara__world:last-of-type")))
        portrait = re.search(r"""src=\"(\S+)\"""", str(html.select(".frame__chara__face > img:nth-child(1)"))).group(1)
        dc = world.group(2)
        first = name.group(1)
        last = name.group(2)
        portrait = portrait
        server = world.group(1)
        if first == "Dusk" and last == "Argentum" and ctx.author.id != self.bot.owner_id:
            embed = discord.Embed(color=discord.Color(0x3b9da5), description=f"""Please read the verification \
instructions more clearly. You have attempted to verify as the example character.
Proper usage:
`{PREFIX}link first_name last_name world_name`""", title="Whoops!")
            embed.set_author(icon_url=self.bot.user.avatar_url, name=self.bot.user.name)
            embed.set_thumbnail(url=self.bot.user.avatar_url)
            embed.set_footer(icon_url=ctx.guild.icon_url, text=ctx.guild.name)
            await ctx.send(embed=embed)
            await wait.delete()
            return
        new = [id_, dc, first, last, portrait, server]
        con = sqlite3.connect("characters.db")
        cur = con.cursor()
        cur.execute("SELECT discord_id FROM characters")
        ids = cur.fetchall()
        new_diff = []
        old_diff = []
        old = []
        if str(ctx.author.id) in str(ids):
            attributes = ["character_id", "dc", "first", "last", "portrait", "server"]
            cur.execute(f"SELECT first FROM characters WHERE discord_id = '{str(ctx.author.id)}'")
            for attribute in attributes:
                cur.execute(f"SELECT {attribute} FROM characters WHERE discord_id = '{str(ctx.author.id)}'")
                details = re.search(r"\([\'\"](.+)[\'\"],\)", str(cur.fetchall()))
                old.append(details.group(1))
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
            for count, unused in enumerate(new):
                if new[count] != old[count]:
                    update = f"UPDATE characters SET {attributes[count]} = ? WHERE discord_id = ?"
                    data = (new[count], str(ctx.author.id))
                    con.execute(update, data)
                if count == 2:
                    first = new[2]
                if count == 3:
                    last = new[3]
            new_dc = discord.utils.get(ctx.guild.roles, name=new[1])
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
            old_dc = discord.utils.get(ctx.guild.roles, name=old[1])
            if old_dc in ctx.author.roles:
                try:
                    await ctx.author.remove_roles(old_dc)
                except (Forbidden, HTTPException):
                    pass
            elif old_dc not in ctx.author.roles:
                for count, unused in enumerate(d["worlds"]["dcs"]):
                    role = str(d["worlds"]["dcs"][str(count)]["name"])
                    if role in str(ctx.author.roles) and role != new_dc.name:
                        old_dc = discord.utils.get(ctx.guild.roles, name=role)
                        try:
                            await ctx.author.remove_roles(old_dc)
                        except (Forbidden, HTTPException):
                            pass
            try:
                await ctx.author.add_roles(new_dc)
            except (Forbidden, HTTPException):
                pass
            try:
                await ctx.author.edit(nick=f"{first} {last}")
            except (Forbidden, HTTPException):
                pass
            new_server = discord.utils.get(ctx.guild.roles, name=new[5])
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
            old_server = discord.utils.get(ctx.guild.roles, name=old[5])
            if old_server in ctx.author.roles:
                try:
                    await ctx.author.remove_roles(old_server)
                except (Forbidden, HTTPException):
                    pass
            elif old_server not in ctx.author.roles:
                for count, unused in enumerate(d["worlds"]["servers"]):
                    role = str(d["worlds"]["servers"][str(count)]["name"])
                    if role in str(ctx.author.roles) and role != new_server.name:
                        old_server = discord.utils.get(ctx.guild.roles, name=role)
                        try:
                            await ctx.author.remove_roles(old_server)
                        except (Forbidden, HTTPException):
                            pass
            try:
                await ctx.author.add_roles(new_server)
            except (Forbidden, HTTPException):
                pass
        elif str(ctx.author.id) not in str(ids):
            cur.execute("""INSERT INTO characters VALUES (?, ?, ?, ?, ?, ?, ?)""",
                        (str(ctx.author.id), str(id_), dc, first, last, portrait, server))
            if dc not in str(ctx.guild.roles):
                await ctx.guild.create_role(name=dc)
            dc_role = discord.utils.get(ctx.guild.roles, name=dc)
            try:
                await ctx.author.add_roles(dc_role)
            except (Forbidden, HTTPException):
                pass
            try:
                await ctx.author.edit(nick=f"{first} {last}")
            except (Forbidden, HTTPException):
                pass
            if server not in str(ctx.guild.roles):
                await ctx.guild.create_role(name=server)
            server_role = discord.utils.get(ctx.guild.roles, name=server)
            try:
                await ctx.author.add_roles(server_role)
            except (Forbidden, HTTPException):
                pass
        con.commit()
        con.close()
        description = "** **"
        licensed_hunter = discord.utils.get(ctx.guild.roles, name="Licensed Hunter")
        licensed_viewer = discord.utils.get(ctx.guild.roles, name="Licensed Viewer")
        if "Aether" in new[1]:
            if ctx.channel.id == 738670827490377800:
                await ctx.author.add_roles(licensed_viewer)
            await ctx.author.add_roles(licensed_hunter)
            if str(ctx.author.id) in str(ids) and ctx.channel.id == 738670827490377800:
                description = """Welcome back! Be sure to peruse <#865129809452728351> to add Hunt-related roles to \
yourself."""
            elif str(ctx.author.id) not in str(ids):
                description = """Welcome to Aether Hunts! Be sure to peruse <#865129809452728351> to add Hunt-related \
roles to yourself."""
        elif "Aether" not in new[1]:
            if licensed_hunter in ctx.author.roles:
                await ctx.author.remove_roles(licensed_hunter)
            description = """Thank you for verifying! Unfortunately, Aether Hunts is a community dedicated to hunting \
on the Aether datacenter, and you have verified with a character not on Aether.
You're welcome to attempt the linking process again with a character on Aether, though! We'd love to have you."""
        embed = discord.Embed(color=discord.Color(0x3b9da5), description=description, title="Verification complete!")
        embed.set_author(icon_url=self.bot.user.avatar_url, name=self.bot.user.name)
        embed.set_thumbnail(url=portrait)
        if str(ctx.author.id) in str(ids):
            if new_diff[0] is not None and old_diff[0] is not None and new_diff[0] in str(ctx.guild.roles)\
                    and old_diff[0] in str(ctx.guild.roles):
                new_diff[0] = discord.utils.get(ctx.guild.roles, name=new_diff[0])
                old_diff[0] = discord.utils.get(ctx.guild.roles, name=old_diff[0])
            if new_diff[3] is not None and old_diff[3] is not None and new_diff[3] in str(ctx.guild.roles)\
                    and old_diff[3] in str(ctx.guild.roles):
                new_diff[3] = discord.utils.get(ctx.guild.roles, name=new_diff[3])
                old_diff[3] = discord.utils.get(ctx.guild.roles, name=old_diff[3])
            arrow_value = []
            new_value = []
            old_value = []
            for count, diff in enumerate(new_diff):
                if isinstance(new_diff[count], discord.Role):
                    new_value.append(new_diff[count].mention)
                elif isinstance(new_diff[count], str):
                    new_value.append(new_diff[count])
            for count, diff in enumerate(old_diff):
                if isinstance(old_diff[count], discord.Role):
                    old_value.append(f"~~{old_diff[count].mention}~~")
                elif isinstance(old_diff[count], str):
                    old_value.append(f"~~{old_diff[count]}~~")
            for value in new_value:
                arrow_value.append("►")
            if "Aether" in new[1] and licensed_viewer in ctx.author.roles:
                arrow_value.append("+")
                new_value.append(licensed_hunter.mention)
                old_value.append("** **")
            arrow_value = "\n".join(arrow_value)
            new_value = "\n".join(new_value)
            old_value = "\n".join(old_value)
            if new_diff[0] is None and len(new_diff[1]) == 0 and len(new_diff[2]) == 0 and new_diff[3] is None\
                    and old_diff[0] is None and len(old_diff[1]) == 0 and len(old_diff[2]) == 0 and old_diff[3] is None:
                arrow_value = "<:dusk:906079428524777524>"
                old_value = "Nothing changed!"
                new_value = "You're good to go!"
            embed.add_field(inline=True, name="Old:", value=old_value)
            embed.add_field(inline=True, name="►", value=arrow_value)
            embed.add_field(inline=True, name="New:", value=new_value)
        elif str(ctx.author.id) not in str(ids):
            added_names = []
            added_roles = []
            for item in new:
                if item == new[1] or item == new[5]:
                    role = discord.utils.get(ctx.guild.roles, name=item)
                    added_roles.append(role)
                if item == new[1] == "Aether":
                    added_roles.append(licensed_hunter)
                elif item == new[2] or item == new[3]:
                    added_names.append(item)
            value = []
            for item in added_roles and added_roles:
                if isinstance(item, discord.Role):
                    value.append(item.mention)
            embed.add_field(inline=True, name="Added:", value="\n".join(value))
            embed.add_field(inline=True, name="Name Changed:", value=" ".join(added_names))
        if "Aether" not in new[1]:
            if "Crystal" in new[1]:
                embed.add_field(inline=False, name="Crystal Hunts:", value="""Looks like you verified with a \
character on the Crystal datacenter! Here's a link to their Hunting Discord.
[Invite](https://discord.gg/S8fKQvh)""")
            elif "Light" in new[1]:
                embed.add_field(inline=False, name="Clan Centurio:", value="""Looks like you verified with a \
character on the Crystal datacenter! Here's a link to their Hunting Discord.
[Invite](https://discord.gg/h52Uzm4""")
            elif "Primal" in new[1]:
                embed.add_field(inline=False, name="The Coeurl:", value="""Looks like you verified with a \
character on the Crystal datacenter! Here's a link to their Hunting Discord.
[Invite](https://discord.gg/k4xNWdV)""")
        embed.set_footer(icon_url=ctx.guild.icon_url, text=ctx.guild.name)
        await ctx.send(embed=embed)
        await wait.delete()
        await asyncio.sleep(300)
        try:
            await ctx.author.remove_roles(licensed_viewer)
        except(Forbidden, HTTPException):
            pass


def setup(bot):
    bot.add_cog(Verification(bot))
