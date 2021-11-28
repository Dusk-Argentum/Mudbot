from bs4 import BeautifulSoup as Soup  # Imports the best possible soup, just, like, the most exquisite soup, which is
# to say, the most beautiful soup, as Soup, because I'm not typing that whole thing every time.
# Used for parsing HTML gathered from the Lodestone.


import json


import disnake
from disnake import Forbidden, HTTPException
from disnake.ext import commands


from mudbot import PREFIX


import re


import requests  # Imports the requests module for use in making HTTP requests to the Lodestone.
# What I wouldn't give for an official Lodestone API... Make it happen, Squeenix. Please.


import sqlite3  # Imports the sqlite3 module for use in keeping track of the database.


from typing import Union


class Verification(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=["i"], brief="Shows basic information about your character.", help="""Shows basic \
information about your linked character, including your name, world, and your character portrait.
Mention another user to view theirs.""", name="info",
                      usage="info (mention)")
    @commands.guild_only()
    async def info(self, ctx, member: Union[disnake.Member, disnake.User] = None):
        if member is None:
            member = ctx.author
        con = sqlite3.connect("characters.db")  # Connects to the database file.
        cur = con.cursor()  # Sets the cursor within the database.
        cur.execute("SELECT discord_id FROM characters")  # Selects all of the Discord IDs.
        ids = cur.fetchall()  # Fetches all of the Discord IDs.
        for id_ in ids:  # Loops through every Discord ID and checks it against either the author's or the ID of the
            # user provided.
            id_ = re.search(r"\(\'(\d+)\',", str(id_))  # Searches for a valid Discord ID within the information
            # returned.
            if id_.group(1) == str(member.id):  # Moves on if the ID matches.
                break
        else:  # Functions in this block execute if the user is not found within the database.
            # Due to eccentricities in the convoluted verification processes over the past few years, some members
            # who are able to use the server normally may not be in the database.
            # If you're reading through this looking for an answer, just do the verification process! It's quick
            # and easy.
            await ctx.send("That user is not in my database.")
            return
        attributes = ["character_id", "dc", "first", "last", "portrait", "server"]  # Makes a list of the attributes.
        info = []
        for attribute in attributes:
            cur.execute(f"SELECT {attribute} FROM characters WHERE discord_id = '{str(member.id)}'")  # Selects the
            # attribute that the loop is currently on from the character's table where the Discord ID matches the
            # ID of the provided user.
            details = re.search(r"\([\'\"](.+)[\'\"],\)", str(cur.fetchall()))
            info.append(details.group(1))
        embed = disnake.Embed(color=disnake.Color(0x3b9da5), title="Character information:")
        embed.set_author(icon_url=member.avatar.url, name=f"{member.name} ({member.id})")
        embed.set_thumbnail(url=info[4])
        embed.add_field(name="Name:", value=f"{info[2]} {info[3]}")
        embed.add_field(name="Server:", value=f"{info[5]} ({info[1]})")
        embed.set_footer(icon_url=ctx.guild.icon.url,
                         text="If this information is outdated, please update it by verifying again.")
        await ctx.send(embed=embed)

    @commands.command(aliases=["id_link", "l"], brief="Links your FFXIV character to your Discord.",
                      help="""Links your FFXIV character to your Discord or updates it if already linked. Accepts \
`<first> <last> <world>` and `<lodestone ID>`.""", name="link", usage=f"""link <first> <last> <world>` OR \
`{PREFIX}link <lodestone ID>""")
    @commands.guild_only()
    async def link(self, ctx, first: str = None, last: str = None, world: str = None):
        wait = await ctx.send("""Attempting to verify your character... Please wait...
This process can take up to thirty seconds.""")  # Squeenix please give us a native Lodestone API.
        id_ = []
        if first.isnumeric() and first is not None:  # Functions in this block execute if the first name is a string
            # of numbers instead of a name. Bypasses searching for character ID using a name.
            id_ = first
            pass
        elif not first.isnumeric() and first is not None:  # Functions in this block execute if the first name is a
            # string of non-numeric things (for example, letters).
            if (last, world) is None:  # Functions in this block execute if either the last name or world name is not
                # provided.
                await ctx.send(f"""One or more arguments missing. Please ensure you are running the command properly.
Example: `{PREFIX}link Dusk Argentum Gilgamesh`""")  # Please do not attempt to verify as me.
                await wait.delete()
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
            if r.status_code != 200:  # Functions in this block execute if the request did not receive a status 202,
                # which is basically an "OK".
                await ctx.send(f"""Apologies for the inconvenience, but an error occurred.
`{r.status_code}`
If you see this message too many times, please open a support ticket.""")
                await wait.delete()
                return
            html = Soup(r.text, "html.parser")  # Turns the HTML from the request into something parsable.
            not_found = html.select(".parts__zero")  # Selects the appropriate element, if it exists.
            if not_found:  # If the not_found element named above exists, functions in this block execute.
                # Only happens if information provided is incorrect,
                # Theoretically.
                await ctx.send(f"""There was no character with the name **{first} {last}** found on **{world}**.
Please make sure all inputs were spelled properly and try again.""")
                await wait.delete()
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
                await ctx.send(f"""There was no character with the name **{first} {last}** found on **{world}**.
Please make sure all inputs were spelled properly and try again.""")
                await wait.delete()
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
                await ctx.send(f"""Apologies for the inconvenience, but the moderation team of this server \
has determined that only characters that have at least one class/job at level {threshold} will be able to make use of \
this server.
Please attempt to verify once again once you have at least one class/job at level {threshold}!""")
                # Sorry to new players. You can join eventually. I prommy.
                await wait.delete()
                return
        async with ctx.typing():  # Gets the provided character's Lodestone page.
            r = requests.get(f"https://na.finalfantasyxiv.com/lodestone/character/{id_}/")
        if r.status_code == 404:  # Functions in this block execute if the status returned is 404, not found.
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
            await ctx.send(embed=embed)
            await wait.delete()
            return
        new = [id_, dc, first, last, portrait, server]  # Sets a list of the new information.
        con = sqlite3.connect("characters.db")
        cur = con.cursor()
        cur.execute("SELECT discord_id FROM characters")
        ids = cur.fetchall()
        new_diff = []  # Sets an empty list for the new stuff.
        old_diff = []  # Sets an empty list for the old stuff.
        old = []  # Sets an empty list for the old..?
        if str(ctx.author.id) in str(ids):
            attributes = ["character_id", "dc", "first", "last", "portrait", "server"]
            for attribute in attributes:
                cur.execute(f"SELECT {attribute} FROM characters WHERE discord_id = '{str(ctx.author.id)}'")
                details = re.search(r"\([\'\"](.+)[\'\"],\)", str(cur.fetchall()))
                old.append(details.group(1))
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
            for count, unused in enumerate(new):  # Functions in this block update information to the new stuff.
                if new[count] != old[count]:
                    update = f"UPDATE characters SET {attributes[count]} = ? WHERE discord_id = ?"
                    data = (new[count], str(ctx.author.id))
                    con.execute(update, data)
                if count == 2:
                    first = new[2]
                if count == 3:
                    last = new[3]
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
            if old_dc in ctx.author.roles:
                try:
                    await ctx.author.remove_roles(old_dc)
                except (Forbidden, HTTPException):
                    pass
            elif old_dc not in ctx.author.roles:
                for count, unused in enumerate(d["worlds"]["dcs"]):
                    role = str(d["worlds"]["dcs"][str(count)]["name"])
                    if role in str(ctx.author.roles) and role != new_dc.name:
                        old_dc = disnake.utils.get(ctx.guild.roles, name=role)
                        try:
                            await ctx.author.remove_roles(old_dc)
                        except (Forbidden, HTTPException):
                            pass
            try:
                await ctx.author.add_roles(new_dc)
            except (Forbidden, HTTPException):
                pass
            try:  # The following function changes the member's name. If it can.
                await ctx.author.edit(nick=f"{first} {last}")
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
            if old_server in ctx.author.roles:
                try:
                    await ctx.author.remove_roles(old_server)
                except (Forbidden, HTTPException):
                    pass
            elif old_server not in ctx.author.roles:
                for count, unused in enumerate(d["worlds"]["servers"]):
                    role = str(d["worlds"]["servers"][str(count)]["name"])
                    if role in str(ctx.author.roles) and role != new_server.name:
                        old_server = disnake.utils.get(ctx.guild.roles, name=role)
                        try:
                            await ctx.author.remove_roles(old_server)
                        except (Forbidden, HTTPException):
                            pass
            try:
                await ctx.author.add_roles(new_server)
            except (Forbidden, HTTPException):
                pass
        elif str(ctx.author.id) not in str(ids):  # Functions in this block execute if the member is not already in
            # the database.
            cur.execute("""INSERT INTO characters VALUES (?, ?, ?, ?, ?, ?, ?)""",  # Makes a new row with the
                        # provided information.
                        (str(ctx.author.id), str(id_), dc, first, last, portrait, server))
            if dc not in str(ctx.guild.roles):
                await ctx.guild.create_role(name=dc)
            dc_role = disnake.utils.get(ctx.guild.roles, name=dc)
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
            server_role = disnake.utils.get(ctx.guild.roles, name=server)
            try:
                await ctx.author.add_roles(server_role)
            except (Forbidden, HTTPException):
                pass
        con.commit()  # Commits the new information.
        con.close()  # Then closes the connection.
        description = "** **"  # Sets a blank description, to be edited. Usually.
        licensed_hunter = disnake.utils.get(ctx.guild.roles, name="Licensed Hunter")
        licensed_viewer = disnake.utils.get(ctx.guild.roles, name="Licensed Viewer")
        if "Aether" in new[1]:  # Functions in this block execute if the member is from Aether.
            if ctx.channel.id == 738670827490377800:
                await ctx.author.add_roles(licensed_viewer)
            await ctx.author.add_roles(licensed_hunter)
            if str(ctx.author.id) in str(ids) and ctx.channel.id == 738670827490377800:
                description = """Welcome back! Be sure to peruse <#865129809452728351> to add Hunt-related roles to \
yourself."""
            elif str(ctx.author.id) not in str(ids):
                description = """Welcome to Aether Hunts! Be sure to peruse <#865129809452728351> to add Hunt-related \
roles to yourself."""
        elif "Aether" not in new[1]:  # Functions in this block execute if the member is not from Aether.
            if licensed_hunter in ctx.author.roles:
                await ctx.author.remove_roles(licensed_hunter)
            description = """Thank you for verifying! Unfortunately, Aether Hunts is a community dedicated to hunting \
on the Aether datacenter, and you have verified with a character not on Aether.
You're welcome to attempt the linking process again with a character on Aether, though! We'd love to have you."""
        embed = disnake.Embed(color=disnake.Color(0x3b9da5), description=description, title="Verification complete!")
        embed.set_author(icon_url=self.bot.user.avatar.url, name=self.bot.user.name)
        embed.set_thumbnail(url=portrait)
        if str(ctx.author.id) in str(ids):  # Functions in this block execute if the member is not already in the
            # database.
            if new_diff[0] is not None and old_diff[0] is not None and new_diff[0] in str(ctx.guild.roles)\
                    and old_diff[0] in str(ctx.guild.roles):
                new_diff[0] = disnake.utils.get(ctx.guild.roles, name=new_diff[0])
                old_diff[0] = disnake.utils.get(ctx.guild.roles, name=old_diff[0])
            if new_diff[3] is not None and old_diff[3] is not None and new_diff[3] in str(ctx.guild.roles)\
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
                    new_value.append(new_diff[count])
            for count, diff in enumerate(old_diff):
                if isinstance(old_diff[count], disnake.Role):
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
                arrow_value = "<:dusk:906079428524777524>"  # Me face.
                old_value = "Nothing changed!"
                new_value = "You're good to go!"
            embed.add_field(inline=True, name="Old:", value=old_value)
            embed.add_field(inline=True, name="►", value=arrow_value)
            embed.add_field(inline=True, name="New:", value=new_value)  # This stuff looks weird in certain
            # circumstances. Requires further testing and the ability to know how it happens to fix. Effects nothing
            # functionally, just cosmetically.
        elif str(ctx.author.id) not in str(ids):  # Another block that executes if the member is not in the database.
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
character on the Crystal datacenter! Here's a link to their Hunting Discord.
[Invite](https://discord.gg/h52Uzm4""")
            elif "Primal" in new[1]:
                embed.add_field(inline=False, name="The Coeurl:", value="""Looks like you verified with a \
character on the Crystal datacenter! Here's a link to their Hunting Discord.
[Invite](https://discord.gg/k4xNWdV)""")
        embed.set_footer(icon_url=ctx.guild.icon.url, text=ctx.guild.name)
        await ctx.send(embed=embed)
        await wait.delete()

    @commands.command(aliases=["u", "un_link"], brief="Removes your character from the database.",
                      help="Removes your character from the database. Also removes the applicable roles.",
                      name="unlink", usage="unlink")
    @commands.guild_only()
    async def unlink(self, ctx):
        confirm = await ctx.send("Unlinking your account will remove all your roles. Proceed?")
        await confirm.add_reaction("👍")
        await confirm.add_reaction("👎")
        reactions = ["👍", "👎"]

        def check(reaction, user):  # Defines a check that checks the reaction provided to the source message and its
            # reactor.
            return user == ctx.author and str(reaction.emoji) in reactions

        try:
            reaction, users = await self.bot.wait_for("reaction_add", timeout=60, check=check)
        except TimeoutError:  # Functions in this block execute if the unlink prompt times out.
            await confirm.delete()
            await ctx.send("Unlinking aborted. Neither accepted reaction added.")
            return
        if str(reaction.emoji) == "👎":
            await confirm.delete()
            await ctx.send("Unlinking aborted.")
            return
        await confirm.delete()
        con = sqlite3.connect("characters.db")
        cur = con.cursor()
        cur.execute("SELECT discord_id FROM characters")
        ids = cur.fetchall()
        for id_ in ids:
            id_ = re.search(r"\(\'(\d+)\',", str(id_))
            if id_.group(1) == str(ctx.author.id):
                break
        else:
            await ctx.send("""You are not in my database.
If you see this message, but have verified properly (have Licensed Hunter role, can see channels, etc.), \
please open a support ticket.""")
            return
        con.execute(f"DELETE FROM characters WHERE discord_id = '{str(ctx.author.id)}'")
        con.commit()
        for role in ctx.author.roles:
            try:
                await ctx.author.remove_roles(role)
            except (Forbidden, HTTPException):
                continue
        await ctx.author.send("""You have successfully unlinked your character.
To regain access to the server, you must re-link your account.""")


def setup(bot):
    bot.add_cog(Verification(bot))
