from bs4 import BeautifulSoup as Soup  # Imports an aesthetically pleasing stew. Not just for fun; this pretty stock is
# used in reading and parsing HTML, the language webpages on the FFXIV Lodestone use. Now that's a sharp chowder!

import disnake
from disnake import Forbidden, HTTPException  # Imports some exceptions that might be thrown if things get funky.
from disnake.ext import commands

import json

import re  # Imports regex. Needed to strip certain information from much longer strings of text.

import requests  # Imports the requests module, used to make web requests to websites on the Internet. In our case,
# the Lodestone.

import sqlite3  # Imports sqlite3, which is used as the database for the character information upon a successful
# verification.
from sqlite3 import OperationalError  # Imports the exception that often gets thrown when sqlite3 detects a faulty
# atom somewhere in space... It randomly fails, basically, so I need handling for this.

from typing import Union  # Imports a Union type that can be used to allow multiple types of objects to coexist.


BYPASS_IMG = "https://64.media.tumblr.com/3c2f826671df24c57758d7e24c295064/9a071b6ba8cc2ed5-d7/s75x75_c1/299911d7e59c2c6f81458b8d4cb3cd8f8d9458ab.pnj"
# These lines define the links to images that will be used in embeds throughout the Verification Cog.
ERROR_IMG = "https://64.media.tumblr.com/d4a0b44f54423c5ea426122a99477127/9a071b6ba8cc2ed5-c9/s75x75_c1/e2b4df00ac22b12bc1404b017ae344ed2eb7e189.pnj"
LOADING_IMG = "https://64.media.tumblr.com/e1af2b9bdfb454b824455c7a64167fe0/9a071b6ba8cc2ed5-86/s75x75_c1/1870f65d30ae50ab4c1faa7a6a604dba1c5b0f6a.gif"
NEWBIE_IMG = "https://64.media.tumblr.com/67c95cd16e37c33760f18c8dc3436289/9a071b6ba8cc2ed5-81/s75x75_c1/c05f7042515153de8602fd79846c71b6dba2b4fe.pnj"
NOT_FOUND_IMG = "https://64.media.tumblr.com/0f229b4e9dec9bc9428f4f5ad9e1f01a/9a071b6ba8cc2ed5-5d/s75x75_c1/ea5f9e880590df5e73f2302c5ee89487025fd985.pnj"
WARNING_IMG = "https://64.media.tumblr.com/b922e1af120c24326b0f55d2a80623cc/9a071b6ba8cc2ed5-c1/s75x75_c1/1598add95d6d0060d74a00a6c57837525c17abd1.pnj"

class Confirmation(disnake.ui.View):  # Defines a View class; this one is used for popping up a confirmation dialogue
    # when a user attempts to link or unlink, to ensure information is all correct, or "OK", as the kids say.
    forward = None  # Defines the variable that will be forwarded upon completion of this confirmation.

    def __init__(self):
        super().__init__()  # Please don't ask me what this does.

    @disnake.ui.button(label="Yep!", style=disnake.ButtonStyle.green)  # Creates a Button, in the color green.
    async def confirmed(self, button: disnake.Button, interaction: disnake.Interaction):
        Confirmation.forward = True  # Passes along a successful confirmation.
        self.stop()  # Stops processing this button, so no further inputs are accepted.

    @disnake.ui.button(label="Nope.", style=disnake.ButtonStyle.red)
    async def denied(self, button: disnake.Button, interaction: disnake.Interaction):
        Confirmation.forward = False  # Passes along a failed confirmation, or a "denial".
        self.stop()


class Verification(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @staticmethod  # Declares a function that can be called later.
    async def link_func(self, inter, character_id):  # This is the function that both linking commands call eventually.
        r = requests.get(f"https://na.finalfantasyxiv.com/lodestone/character/{character_id}/")  # Makes a web request
        # to a character's page based on the character ID, which is passed to the function from the Slash Command.
        if r.status_code != 200:  # Functions in this block execute if the web requests results in any status other
            # than 200, which is the only status where everything returns just fine.
            embed = disnake.Embed(color=disnake.Color(0x9c2c37), description="Please try again later.",
                                  title="We're sorry; an error occurred!")
            embed.set_author(icon_url=self.bot.user.avatar.url, name=self.bot.user.name)
            embed.set_thumbnail(url=ERROR_IMG)
            embed.set_footer(icon_url=self.bot.user.avatar.url, text=f"Error code: {r.status_code}.")
            await inter.edit_original_response(embed=embed)
            return
        html = Soup(r.text, "html.parser")  # Grabs the raw text from the earlier web request and parses it as
        # HTML.
        name = re.search(r"""chara__name\">([\w'-]{2,15})\s([\w'-]{2,15})<""",
                         str(html.select("div.frame__chara__box:nth-child(2) > .frame__chara__name")))  # Uses a CSS
        # selector to grab the character's name from a specific web element on the web page, and uses Regex to isolate
        # the specific string of the name from the HTML code.
        portrait = re.search(r"""src=\"(\S+)\"""",
                             str(html.select(".frame__chara__face > img:nth-child(1)"))).group(1)  # Does the same,
        # but with the character portrait, and, below, the world.
        world = re.search(r"(\w{4,13})\s\[(\w{4,9})]",
                          str(html.select("p.frame__chara__world:last-of-type")))
        dc = world.group(2)  # Separates out the DC name from the element that contains both DC and Server.
        first_name = name.group(1)
        last_name = name.group(2)
        portrait = portrait  # This is a silly line. I don't know why I kept it.
        server = world.group(1)
        embed = disnake.Embed(color=disnake.Color(0x3b9da5), description="Does this information appear correct?",
                              title="Confirmation")
        embed.set_author(icon_url=self.bot.user.avatar.url, name=self.bot.user.name)
        embed.set_thumbnail(url=portrait)
        embed.add_field(inline=True, name="Name:", value=f"{first_name} {last_name}")
        embed.add_field(inline=True, name="Server:", value=f"{server} ({dc})")
        embed.add_field(inline=False, name="Lodestone:",
                        value=f"[{character_id}](https://na.finalfantasy.com/lodestone/charactrer/{character_id}/)")
        embed.set_footer(icon_url=inter.guild.icon.url,
                         text="Information on the Lodestone may be slightly outdated.")
        view = Confirmation()  # Uses the Confirmation view from earlier to ask the user if the displayed information
        # is correct. It usually should be, if the user filled in everything correctly.
        await inter.edit_original_response(attachments=None, embed=embed, view=view)
        await view.wait()  # Waits for a response from the Confirmation view.
        if Confirmation.forward is False:  # Functions in this block execute if the user denied ownership of the
            # character shown to them.
            embed = disnake.Embed(color=disnake.Color(0x9c2c37),
                                  description="A negative response was given. Please try again.",
                                  title="Linking aborted.")
            embed.set_author(icon_url=self.bot.user.avatar.url, name=self.bot.user.name)
            embed.set_thumbnail(url=ERROR_IMG)
            embed.set_footer(icon_url=inter.guild.icon.url, text="Consider using /id_link instead.")
            await inter.edit_original_response(embed=embed, view=None)
            return
        with open("server_config.json", "r") as server_config:
            data = json.load(server_config)
        if data["server_config"][str(inter.guild.id)]["level_gate"]["state"] == "True":  # Functions in this block only
            # execute if the server the command was run on has enabled the level gate function.
            threshold = int(data["server_config"][str(inter.guild.id)]["level_gate"]["level"])  # Grabs the level that
            # the server administration had determined to be the minimum required level to use the server.
            with open("classes.json", "r") as classes:  # Opens up the file where all the class level CSS selectors live
                data = json.load(classes)  # and, you know what, there's almost 3 dozen of those these days!
                # Thank you to the authors of the maintainers of the lodestone-css-selectors bit of the XIVAPI repo!
            for class_ in enumerate(data["classes"]):  # Loops through every class in the JSON.
                level = re.search(r"""\.png\" width=\"\d*\"/>(\d{1,3})</li>""",
                                  str(html.select(data["classes"][str(class_[0])]["selector"])))  # Searches through
                # the HTML looking for the selector for each respective class.
                # Also, you'll never guess what seemingly updated mid-testing! That's right; the CSS selectors
                # for each class. :)
                if level is not None and int(level.group(1)) >= threshold:  # If the character has at least one level
                    # above the gate, it may pass.
                    break
            else:  # Functions in this block only execute if the above loop never broke.
                licensed_hunter = disnake.utils.get(inter.guild.roles, name="Licensed Hunter")
                if licensed_hunter in inter.author.roles:  # Functions in this block only execute if the user already
                    # has access to the server.
                    embed = disnake.Embed(color=disnake.Color(0x3b9da5), description="""Please hold.""",
                                          title="Throwing wide the level gate...")  # Throw wide the gates...
                    embed.set_author(icon_url=self.bot.user.avatar.url, name=self.bot.user.name)
                    embed.set_thumbnail(url=BYPASS_IMG)
                    embed.set_footer(icon_url=WARNING_IMG,
                                     text="You must have drank the soda, because you're seeing faster.")
                    # Drink the soda, Mr. Freeman, it'll help you see faster.
                    await inter.edit_original_response(embed=embed, view=None)
                    pass
                elif licensed_hunter not in inter.author.roles:  # Functions in this block only execute if the user
                    # neither has a level above the threshold nor is already a Licensed Hunter.
                    embed = disnake.Embed(color=disnake.Color(0x3b9da5), description=f"""The moderation team of \
{inter.guild.name} has determined that only characters that have at least one job at level {threshold} will be able to \
make use of this server.
Please attempt to verify again once you have at least one job at level {threshold}.""",
                                          title="We're sorry!")
                    embed.set_author(icon_url=self.bot.user.avatar.url, name=self.bot.user.name)
                    embed.set_thumbnail(url=NEWBIE_IMG)  # It's OK, Sprouts. Enjoy the first part of the game while
                    # you still can! We'll be here.
                    # If Aether Hunts was going to implode itself, it would have done so by now. TRUST ME.
                    embed.set_footer(icon_url=inter.guild.icon.url, text="We look forward to your future visit!")
                    await inter.edit_original_response(embed=embed, view=None)
                    return
        if first_name == "Dusk" and last_name == "Argentum" and inter.author.id != self.bot.owner_id:  # Functions in
            # this block execute if a user tries to verify as me. While I also don't like imposters, this serves the
            # dual purpose of making sure people don't fill in their information as my name, as it's used as an example
            # in some places.
            embed = disnake.Embed(color=disnake.Color(0x3b9da5), description="""Please read the instructions \
more carefully. You have attempted to verify as the example character.""", title="Whoops!")
            embed.set_author(icon_url=self.bot.user.avatar.url, name=self.bot.user.name)
            embed.set_thumbnail(url=NOT_FOUND_IMG)
            embed.set_footer(icon_url="https://cdn.discordapp.com/emojis/1288585929090400257.webp?size=160",
                             text="No doubles!")
            await inter.edit_original_response(embed=embed, view=None)
            return
        new = [character_id, dc, first_name, last_name, portrait, server]  # Makes a list which fills in the
        # values mentioned earlier into a specific order.
        try:  # Attempts to open the database...
            con = sqlite3.connect("characters.db", timeout=30.0)
        except OperationalError:  # If sqlite3 decides it doesn't want to work, this block happens.
            embed = disnake.Embed(color=disnake.Color(0x9c2c37),
                                    description="Please wait a moment and try again.",
                                    title="We're sorry; an error occurred!")
            embed.set_author(icon_url=self.bot.user.avatar.url, name=self.bot.user.name)
            embed.set_thumbnail(url=ERROR_IMG)
            embed.set_footer(icon_url=self.bot.user.avatar.url, text="Bog in, flush out!")
            await inter.edit_original_response(embed=embed, view=None)
            return
        cur = con.cursor()  # Defines a cursor for the database.
        cur.execute("SELECT discord_id FROM characters")  # This is an SQL query which gets a list of all of the
        # entries in the discord_id column of the characters database.
        ids = cur.fetchall()  # Declares a variable with the aforementioned fetching.
        con.close()  # Closes the connection. This reopens later, but is closed prematurely because sqlite3 can
        # sometimes act strange if there are too many simultaneous open connections.
        new_diff = []  # Defines an empty list with the "new" information.
        old_diff = []  # Same, but for old.
        old = []  # I know it seems like the same, but this is actually a DIFFERENT old.
        if str(inter.author.id) in str(ids):  # Functions in this block execute if the user is not in the database.
            attributes = ["character_id", "dc", "first", "last", "portrait", "server"]  # Creates a list with the
            # attributes that are the same as the title of each column in the database, for iteration reasons.
            try:
                con = sqlite3.connect("characters.db", timeout=30.0)
            except OperationalError:
                embed = disnake.Embed(color=disnake.Color(0x9c2c37),
                                        description="Please wait a moment and try again.",
                                        title="We're sorry; an error occurred!")
                embed.set_author(icon_url=self.bot.user.avatar.url, name=self.bot.user.name)
                embed.set_thumbnail(url=ERROR_IMG)
                embed.set_footer(icon_url=self.bot.user.avatar.url, text="Bog in, flush out!")
                await inter.edit_original_response(embed=embed, view=None)
                return
            cur = con.cursor()
            for attribute in attributes:  # Loops through every attribute in the list.
                cur.execute(f"SELECT {attribute} FROM characters WHERE discord_id = '{str(inter.author.id)}'")  # Grabs
                # the data in each column for the user using the command.
                fetched = str(cur.fetchall())  # For some reason, cur.fetchall() only persists for a SINGLE use. So,
                # I set it as a variable here so it persists longer.
                details = re.search(r"\([\'\"](.+)[\'\"],\)", fetched)  # Grabs the information from the data
                # sent by the column retrieval.
                if details is None:
                    details = re.search(r"\[\((.+),\)]", fetched)  # Somehow, in the middle of
                    # testing, this completely shit the bed and started saving values without quotes. Why?
                    # I'll never know.
                old.append(details.group(1))  # Appends the details gathered from the database to the list.
            con.close()  # Cannot stress how unfortunately and needlessly important this is.
            for count, attribute in enumerate(new):  # Enumerates through the list of attributes.
                if attribute == old[count]:  # If the new information is the same as the old, functions in this block
                    # execute.
                    if count == 0 or count == 4:  # Ignores character_id and portrait.
                        continue
                    new_diff.append("")  # Adds an "empty" entry to the list.
                    old_diff.append("")
                elif attribute != old[count]:  # But if the information is not the same, it commits it to the lists.
                    if count == 0 or count == 4:
                        continue
                    new_diff.append(new[count])
                    old_diff.append(old[count])
            try:
                con = sqlite3.connect("characters.db", timeout=30.0)
            except OperationalError:
                embed = disnake.Embed(color=disnake.Color(0x9c2c37),
                                        description="Please wait a moment and try again.",
                                        title="We're sorry; an error occurred!")
                embed.set_author(icon_url=self.bot.user.avatar.url, name=self.bot.user.name)
                embed.set_thumbnail(url=ERROR_IMG)
                embed.set_footer(icon_url=self.bot.user.avatar.url, text="Bog in, flush out!")
                await inter.edit_original_response(embed=embed, view=None)
                return
            for count, unused in enumerate(new):  # Variable named unused goes unused, surprisingly.
                if new[count] != old[count]:  # If the new information is not the same as the old information, does
                    # the below.
                    update = f"UPDATE characters SET {attributes[count]} = ? WHERE discord_id = ?"  # Creates an update
                    # for the information if it is different.
                    d = (new[count], str(inter.author.id))
                    con.execute(update, d)  # Commits the information to the database.
            con.commit()  # Sike! It actually does that now.
            con.close()
            with open("worlds.json", "r+") as worlds:
                data = json.load(worlds)
            new_dc = disnake.utils.get(inter.guild.roles, name=new[1])  # Gets the role of the "new" DC.
            if new_dc not in inter.guild.roles:  # Functions in this block execute if the new DC doesn't already
                # have a role on the server. Literally just future-proofing, at this point.
                await inter.guild.create_role(name=new[1])  # Creates a role that is named the same as the DC.
                with open("worlds.json", "r+") as worlds:
                    world_update = {f"{len(data['worlds']['dcs'])}": {
                        "name": new[1]
                    }
                    }
                    data["worlds"]["dcs"].update(world_update)
                    worlds.seek(0)
                    json.dump(data, worlds, indent=4)
                    worlds.truncate()  # Would you believe that, in fixing this, I realized it never worked on the
                    # old version?
            old_dc = disnake.utils.get(inter.guild.roles, name=old[1])  # Same as the new stuff, but with the old.
            if old_dc in inter.author.roles:  # Functions in this block execute if the old DC's role is in the user's
                # role list at time of execution.
                try:  # Tries to remove the old DC from the user's roles, if it can.
                    await inter.author.remove_roles(old_dc)
                except (Forbidden, HTTPException):
                    pass  # Just gives up if it can't.
            elif old_dc not in inter.author.roles:  # Basic premise of this block is to delete all DC roles from
                # the user to ensure they only have the new one.
                for count, unused in enumerate(data["worlds"]["dcs"]):
                    role = str(data["worlds"]["dcs"][str(count)]["name"])
                    if role in str(inter.author.roles) and role != new_dc.name:
                        old_dc = disnake.utils.get(inter.guild.roles, name=role)
                        try:
                            await inter.author.remove_roles(old_dc)
                        except (Forbidden, HTTPException):
                            pass
            try:
                await inter.author.add_roles(new_dc)
            except (Forbidden, HTTPException):
                pass
            try:  # Tries to change the user's nickname on the server to their in-game name.
                await inter.author.edit(nick=f"{first_name} {last_name}")
            except (Forbidden, HTTPException):
                pass
            new_server = disnake.utils.get(inter.guild.roles, name=new[5])  # Same as the DC stuff, but for server.
            if new_server not in inter.guild.roles:
                with open("worlds.json", "r+") as worlds:
                    world_update = {f"{len(data['worlds']['servers'])}": {
                        "name": new[5]
                    }
                    }
                    data["worlds"]["servers"].update(world_update)
                    worlds.seek(0)
                    json.dump(data, worlds, indent=4)
                    worlds.truncate()
                if new[1] == "Aether":
                    with open("worlds.json", "r+") as worlds:
                        aether_update = {f"{len(data['worlds']['aether_dc'])}": {
                            "name": new[5]
                        }
                        }
                        data["worlds"]["aether_dc"].update(aether_update)
                        worlds.seek(0)
                        json.dump(data, worlds, indent=4)
                        worlds.truncate()
                    await inter.guild.create_role(name=new[5])
            old_server = disnake.utils.get(inter.guild.roles, name=old[5])
            if old_server in inter.author.roles:
                try:
                    await inter.author.remove_roles(old_server)
                except (Forbidden, HTTPException):
                    pass
            elif old_server not in inter.author.roles:
                for count, unused in enumerate(data["worlds"]["servers"]):
                    role = str(data["worlds"]["servers"][str(count)]["name"])
                    if role in str(inter.author.roles) and role != new_server.name:
                        old_server = disnake.utils.get(inter.guild.roles, name=role)
                        try:
                            await inter.author.remove_roles(old_server)
                        except (Forbidden, HTTPException):
                            pass
            if new[1] == "Aether":
                try:
                    await inter.author.add_roles(new_server)
                except (Forbidden, HTTPException):
                    pass
        elif str(inter.author.id) not in str(ids):  # Functions in this block execute if the user is not already
            # in the database.
            try:
                con = sqlite3.connect("characters.db", timeout=30.0)
            except OperationalError:
                embed = disnake.Embed(color=disnake.Color(0x9c2c37),
                                      description="Please wait a moment and try again.",
                                      title="We're sorry; an error occurred!")
                embed.set_author(icon_url=self.bot.user.avatar.url, name=self.bot.user.name)
                embed.set_thumbnail(url=ERROR_IMG)
                embed.set_footer(icon_url=self.bot.user.avatar.url, text="Bog in, flush out!")
                await inter.edit_original_response(embed=embed, view=None)
                return
            cur = con.cursor()
            cur.execute("""INSERT INTO characters VALUES (?, ?, ?, ?, ?, ?, ?)""",
                        (str(inter.author.id), str(character_id), dc, first_name, last_name, portrait,
                         server))  # Creates a new database entry with the specified values.
            con.commit()
            con.close()
            worlds_list = []  # Creates an empty list, ready to be filled with the world names.
            with open("worlds.json", "r") as worlds:
                data = json.load(worlds)
            for count, world in enumerate(data["worlds"]["dcs"]):
                worlds_list.append(data["worlds"]["dcs"][str(count)]["name"])
            for count, world in enumerate(data["worlds"]["servers"]):
                worlds_list.append(data["worlds"]["servers"][str(count)]["name"])
            for role in inter.author.roles:  # A lot of this stuff is removing or adding roles from the user or server
                # if they should or shouldn't have them.
                if role.name in worlds_list:
                    for world in worlds_list:
                        if role.name == world:
                            await inter.author.remove_roles(role)
            if dc not in str(inter.guild.roles):
                await inter.guild.create_role(name=dc)
                with open("worlds.json", "r+") as worlds:
                    world_update = {f"{len(data['worlds']['dcs'])}": {
                        "name": dc
                    }
                    }
                    data["worlds"]["dcs"].update(world_update)
                    worlds.seek(0)
                    json.dump(data, worlds, indent=4)
                    worlds.truncate()
            dc_role = disnake.utils.get(inter.guild.roles, name=dc)
            try:
                await inter.author.add_roles(dc_role)
            except (Forbidden, HTTPException):
                pass
            try:
                await inter.author.edit(nick=f"{first_name} {last_name}")
            except (Forbidden, HTTPException):
                pass
            if server not in str(inter.guild.roles):
                with open("worlds.json", "r+") as worlds:
                    world_update = {f"{len(data['worlds']['servers'])}": {
                        "name": server
                    }
                    }
                    data["worlds"]["servers"].update(world_update)
                    worlds.seek(0)
                    json.dump(data, worlds, indent=4)
                    worlds.truncate()
                if dc == "Aether":
                    with open("worlds.json", "r+") as worlds:
                        aether_update = {f"{len(data['worlds']['aether_dc'])}": {
                            "name": server
                        }
                        }
                        data["worlds"]["aether_dc"].update(aether_update)
                        worlds.seek(0)
                        json.dump(data, worlds, indent=4)
                        worlds.truncate()
                    await inter.guild.create_role(name=server)
            server_role = disnake.utils.get(inter.guild.roles, name=server)
            if dc  == "Aether":
                try:
                    await inter.author.add_roles(server_role)
                except (Forbidden, HTTPException):
                    pass
        description = "** **"  # Sets a "blank" description. Descriptions can't be blank, and a bold space is somehow
        # "not-blank", but reads as blank.
        licensed_hunter = disnake.utils.get(inter.guild.roles, name="Licensed Hunter")
        licensed_viewer = disnake.utils.get(inter.guild.roles, name="Licensed Viewer")
        accepted_dcs = ["Aether"]  # Aether Hunts, surprisingly, only caters to the Aether DC.
        accepted_visitors = ["Aether", "Dynamis", "Crystal", "Primal"]  # But! Aether Hunts has been playing along
        # mostly nice with people from these DCs as well. Except when they decide they don't like them again, very
        # suddenly. Then it becomes a problem for everyone else. :)
        if new[1] in accepted_dcs:
            if inter.channel.id == 738670827490377800:  # Functions in this block execute if the channel in which this
                # command is executed is... A channel I don't get the name of anymore. Probably whatever the onboarding
                # channel for AH is.
                await inter.author.add_roles(licensed_viewer)
            await inter.author.add_roles(licensed_hunter)
            if str(inter.author.id) in str(ids) and inter.channel.id == 738670827490377800:
                description = """Welcome back! Be sure to peruse <#1095159801329229945> to add Hunt-related roles to \
yourself."""
            elif str(inter.author.id) in str(ids) and inter.channel.id != 738670827490377800:
                description = """Information updated! Thank you for taking the time to keep your information \
up-to-date."""
            elif str(inter.author.id) not in str(ids):
                description = """Welcome to Aether Hunts! Be sure to peruse <#1095159801329229945> to add \
Hunt-related roles to yourself."""
        elif new[1] not in accepted_visitors:  # Functions in this block execute if, for whatever reason, someone who
            # WAS on Aether linked with a character that isn't even in the Accepted Visitors list. Why?
            if licensed_hunter in inter.author.roles:  # Removes access for people who verify with a character off of
                # the aforementioned DCs. Sorry! We have little here for you.
                await inter.author.remove_roles(licensed_hunter)
            description = """Thank you for verifying! Unfortunately, Aether Hunts is a community dedicated to \
hunting on the Aether datacenter, and you have verified with a character not on Aether.
You're welcome to attempt the linking process again with a character on Aether, though! We'd love to have you."""
        embed = disnake.Embed(color=disnake.Color(0x3b9da5), description=description,
                                title="Verification complete!")
        embed.set_author(icon_url=self.bot.user.avatar.url, name=self.bot.user.name)
        embed.set_thumbnail(url=portrait)
        if str(inter.author.id) in str(ids):  # Functions in this and the below blocks are making the text look
            # nice and pretty for users who link or update their information.
            if new_diff[0] is not None and old_diff[0] is not None and new_diff[0] in str(inter.guild.roles) \
                    and old_diff[0] in str(inter.guild.roles):
                new_diff[0] = disnake.utils.get(inter.guild.roles, name=new_diff[0])
                old_diff[0] = disnake.utils.get(inter.guild.roles, name=old_diff[0])
            if new_diff[3] is not None and old_diff[3] is not None and new_diff[3] in str(inter.guild.roles) \
                    and old_diff[3] in str(inter.guild.roles):
                new_diff[3] = disnake.utils.get(inter.guild.roles, name=new_diff[3])
                old_diff[3] = disnake.utils.get(inter.guild.roles, name=old_diff[3])
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
                    old_value.append(f"~~{old_diff[count].mention}~~")
                elif isinstance(old_diff[count], str):
                    if old_diff[count] == "":
                        pass
                    elif old_diff[count] != "":
                        old_value.append(f"~~{old_diff[count]}~~")
            for _ in new_value:
                arrow_value.append("►")
            if new[1] in accepted_dcs and licensed_viewer in inter.author.roles:
                arrow_value.append("+")
                new_value.append(licensed_hunter.mention)
                old_value.append("** **")
            arrow_value = "\n".join(arrow_value)
            new_value = "\n".join(new_value)
            old_value = "\n".join(old_value)
            if new_diff[0] is None and len(new_diff[1]) == 0 and len(new_diff[2]) == 0 and new_diff[3] is None \
                    and old_diff[0] is None and len(old_diff[1]) == 0 and len(old_diff[2]) == 0 and old_diff[
                3] is None:
                arrow_value = "<:dusk2:1288585929090400257>"  # That's my face!
                old_value = "Nothing changed!"
                new_value = "You're good to go!"
            embed.add_field(inline=True, name="Old:", value=old_value)
            embed.add_field(inline=True, name="►", value=arrow_value)
            embed.add_field(inline=True, name="New:", value=new_value)
        elif str(inter.author.id) not in str(ids):  # Functions in this block execute specifically if this is a new
            # user who is verifying now but was not previously in the database.
            added_names = []
            added_roles = []
            for item in new:
                if item == new[1] or item == new[5]:
                    if item == new[5] and new[1] != "Aether":
                        continue
                    role = disnake.utils.get(inter.guild.roles, name=item)
                    added_roles.append(role)
                if item == new[1] and new[1] in accepted_dcs:
                    added_roles.append(licensed_hunter)
                elif item == new[2] or item == new[3]:
                    added_names.append(item)
            value = []
            for item in added_roles and added_roles:
                if isinstance(item, disnake.Role):
                    value.append(item.mention)
            embed.add_field(inline=True, name="Added:", value="\n".join(value))
            embed.add_field(inline=True, name="Name Changed:", value=" ".join(added_names))
        if "Aether" not in new[1]:
            if "Crystal" in new[1]:
                embed.add_field(inline=False, name="Crystal Hunts:", value="""Looks like you verified with a \
character on the Crystal Datacenter!
We are now offering limited usage of our Discord to the other NA Datacenters, so members from those Datacenters can \
receive Hunt callouts on Aether while they are visiting!
Please head to <#591099527667253248> and follow the instructions within to opt-in.

Please also feel free to join your Datacenter's native Hunt Discord for Hunt callouts on your own Datacenter!
[Invite](https://discord.gg/S8fKQvh)""")  # Gee, I sure hope all these links are up-to-date!
            elif "Light" in new[1]:
                embed.add_field(inline=False, name="Clan Centurio:", value="""Looks like you verified with a \
character on the Light datacenter! Here's a link to their Hunting Discord.
[Invite](https://discord.gg/h52Uzm4)""")  # No clue why this text is different. I must have had a reason six years ago.
            elif "Primal" in new[1]:
                embed.add_field(inline=False, name="The Coeurl:", value="""Looks like you verified with a \
character on the Primal Datacenter!
We are now offering limited usage of our Discord to the other NA Datacenters, so members from those Datacenters can \
receive Hunt callouts on Aether while they are visiting!
Please head to <#591099527667253248> and follow the instructions within to opt-in.

Please also feel free to join your Datacenter's native Hunt Discord for Hunt callouts on your own Datacenter!
[Invite](https://discord.gg/k4xNWdV)""")
        embed.set_footer(icon_url=inter.guild.icon.url, text=inter.guild.name)
        await inter.edit_original_response(embed=embed, view=None)
        await inter.delete_original_response(delay=300)  # Deletes the response after 300 seconds to keep the channel
        # clean.

    @commands.slash_command(description="""Links your FFXIV character to your Discord using your character's \
Lodestone ID.""", name="id_link")  # The two linking commands actually start here, though, until their functions merge
    # into the above link_func.
    @commands.contexts(guild=True)
    async def id_link(self, inter, character_id: int = commands.Param(description="Your character's Lodestone ID.",
                                                                      name="id", min_length=1, max_length=9)):
        embed = disnake.Embed(color=disnake.Color(0x3b9da5), description="Searching for your character...",
                              title="Please wait...")
        embed.set_author(icon_url=self.bot.user.avatar.url, name=self.bot.user.name)
        embed.set_thumbnail(url=LOADING_IMG)
        embed.set_footer(icon_url=self.bot.user.avatar.url, text="This may take up to one minute.")  # This usually only
        # takes a few seconds these days, but it used to take sixteenever.
        await inter.response.send_message(delete_after=300, embed=embed, ephemeral=True)
        async with inter.channel.typing():  # This helps to show that the bot has not, in fact, passed away while
            # doing some web requests.
            r = requests.get(f"https://na.finalfantasyxiv.com/lodestone/character/{character_id}/")  # Also: /id_link
            # is officially the faster way to link, because /id_link only makes one web request, while /link makes two!
            if r.status_code == 403:  # Functions in this block execute if the provided link has a character, but it
                # is hidden from Mudbot.
                embed = disnake.Embed(color=disnake.Color(0x9c2c37),
                                      description=f"""To successfully verify with Mudbot, your must set your \
Character Profile Page and Character Information: Profile (two different settings) to "All Users".
You may re-hide your character after verifying.""",
                                      title="Your character is private!")
                embed.set_author(icon_url=self.bot.user.avatar.url, name=self.bot.user.name)
                embed.set_thumbnail(url=WARNING_IMG)
                embed.set_footer(icon_url=inter.guild.icon.url,
                                 text="We hope for your understanding.")
                await inter.edit_original_response(embed=embed)
                return
            elif r.status_code == 404:  # Functions in this block execute if the provided link does not resolve into
                # an actual character page.
                embed = disnake.Embed(color=disnake.Color(0x9c2c37),
                                      description=f"""There was no character with the ID **{character_id}** found.
Please ensure all inputs were entered properly and try again.""",
                                      title="Character not found!")
                embed.set_author(icon_url=self.bot.user.avatar.url, name=self.bot.user.name)
                embed.set_thumbnail(url=NOT_FOUND_IMG)
                embed.set_footer(icon_url=inter.guild.icon.url,
                                 text="Your ID is in the URL of your character's Lodestone page.")
                await inter.edit_original_response(embed=embed)
                return
            elif r.status_code != 200:
                embed = disnake.Embed(color=disnake.Color(0x9c2c37),
                                      description=f"""I wasn't able to find a character...
Please ensure all inputs were entered properly and try again.
Alternatively, ensure your character's Lodestone page is set to be visible to the public.""",
                                      title="Generic page error code!")  # Kinda ran out of steam with these errors.
                embed.set_author(icon_url=self.bot.user.avatar.url, name=self.bot.user.name)
                embed.set_thumbnail(url=NOT_FOUND_IMG)
                embed.set_footer(icon_url=inter.guild.icon.url,
                                 text=f"Error code: {r.status_code}. If this isn't 404, sorry! Please try again later.")
                await inter.edit_original_response(embed=embed)
                return
            await self.link_func(self=self, inter=inter, character_id=character_id)  # Runs the generic link function,
            # since everything after this point would literally just be copy-pasted. This saves me from needing to
            # scrutinize both functions if I make a change to one of them. Also, makes the code shorter!

    @commands.slash_command(description="Shows your current linked information.", name="info")
    @commands.contexts(guild=True)
    async def info(self, inter, member: Union[disnake.Member, disnake.User] = None):  # You can view the linked
        # information for people who are not on the server anymore but are still in the database. This is intended
        # for use for mods, generally, but, eh.
        if member is None:  # Functions in this block execute if the user did not provide a member in the command
            # invocation. Basically, defaults to the user who used the command.
            member = inter.author
        embed = disnake.Embed(color=disnake.Color(0x3b9da5), description="Looking for that user in my database...",
                              title="Searching...")
        embed.set_author(icon_url=self.bot.user.avatar.url, name=self.bot.user.name)
        embed.set_thumbnail(url=LOADING_IMG)
        embed.set_footer(icon_url=self.bot.user.avatar.url, text=f"This should be quick.")
        await inter.response.send_message(delete_after=300, embed=embed)
        try:
            con = sqlite3.connect("characters.db", timeout=30.0)
        except OperationalError:
            embed = disnake.Embed(color=disnake.Color(0x9c2c37), description="Please try again later.",
                                  title="We're sorry; an error occurred!")
            embed.set_author(icon_url=self.bot.user.avatar.url, name=self.bot.user.name)
            embed.set_thumbnail(url=ERROR_IMG)
            embed.set_footer(icon_url=self.bot.user.avatar.url, text=f"Error code: {r.status_code}.")
            await inter.edit_original_response(embed=embed)
            return
        cur = con.cursor()
        cur.execute("SELECT discord_id FROM characters")
        ids = cur.fetchall()
        con.close()
        for id_ in ids:  # I hate this block so much.
            id_ = re.search(r"\(\'(\d+)\',", str(id_))
            if id_ is None:
                id_ = re.search(r"\((\d+),", str(id_))
            if id_.group(1) == str(member.id):
                break
        else:
            embed = disnake.Embed(color=disnake.Color(0x9c2c37), description="That user is not in my database.",
                                  title="Could not find user!")
            embed.set_author(icon_url=self.bot.user.avatar.url, name=self.bot.user.name)
            embed.set_thumbnail(url=ERROR_IMG)
            embed.set_footer(icon_url=self.bot.user.avatar.url, text="Bog in, flush out!")
            await inter.edit_original_response(embed=embed)
            return
        attributes = ["character_id", "dc", "first", "last", "portrait", "server"]
        info = []  # Much like with linking, this defines an empty list and a series of attributes which are going
        # to be filled out as the bot loops through them.
        try:
            con = sqlite3.connect("characters.db", timeout=30.0)
        except OperationalError:
            embed = disnake.Embed(color=disnake.Color(0x9c2c37), description="Please try again later.",
                                  title="We're sorry; an error occurred!")
            embed.set_author(icon_url=self.bot.user.avatar.url, name=self.bot.user.name)
            embed.set_thumbnail(url=ERROR_IMG)
            embed.set_footer(icon_url=self.bot.user.avatar.url, text=f"Error code: {r.status_code}.")
            await inter.edit_original_response(embed=embed)
            return
        cur = con.cursor()
        for attribute in attributes:
            cur.execute(f"SELECT {attribute} FROM characters WHERE discord_id = '{str(member.id)}'")
            fetched = str(cur.fetchall())
            details = re.search(r"\([\'\"](.+)[\'\"],\)", fetched)
            if details is None:
                details = re.search(r"\[\((.+),\)]", fetched)
            info.append(details.group(1))
        con.close()
        embed = disnake.Embed(color=disnake.Color(0x3b9da5), title="Character information:")
        embed.set_author(icon_url=member.avatar.url, name=f"{member.name} ({member.id})")
        embed.set_thumbnail(url=info[4])
        embed.add_field(inline=True, name="Name:", value=f"{info[2]} {info[3]}")
        embed.add_field(inline=True, name="Server:", value=f"{info[5]} ({info[1]})")
        embed.add_field(inline=False, name="Lodestone:",
                        value=f"[{info[0]}](https://na.finalfantasyxiv.com/lodestone/character/{info[0]}/)")
        embed.set_footer(icon_url=inter.guild.icon.url,
                         text="If this information is outdated, please update it by verifying again.")
        await inter.edit_original_response(embed=embed)
        await inter.delete_original_response(delay=300)

    @commands.slash_command(description="Links your FFXIV character to your Discord using your character's name.",
                            name="link")
    @commands.contexts(guild=True)
    async def link(self, inter,
                   first_name: str = commands.Param(description="Your character's first name.", name="first_name",
                                                    max_length=15, min_length=2),
                   last_name: str = commands.Param(description="Your character's last name.", name="last_name",
                                                   max_length=15, min_length=2),
                   world_name: str = commands.Param(description="Your character's world name.", name="world_name",
                                                    max_length=13, min_length=4)):
        # Look at these unwieldy arguments! Now do you understand why I split /link and /id_link?
        # Also, this will have to be hard-updated if world names get longer than 13 characters. Surely that will
        # never happen. Surely.
        embed = disnake.Embed(color=disnake.Color(0x3b9da5), description="Searching for your character...",
                              title="Please wait...")
        embed.set_author(icon_url=self.bot.user.avatar.url, name=self.bot.user.name)
        embed.set_thumbnail(url=LOADING_IMG)
        embed.set_footer(icon_url=self.bot.user.avatar.url, text="This may take up to one minute.")
        await inter.response.send_message(delete_after=300, embed=embed, ephemeral=True)
        first_name = first_name.lower().capitalize().replace("‘", "'")  # This is actually a neat bit of
        # trickery, which I'm going to talk about here because nobody else fucking understands me except you.
        # Some mobile devices replace the default apostrophe character ' with a "smart quote", which is basically
        # a single-quote character, which, in most circumstances, is fine. However, the apostrophes in character names
        # in-game are... Apostrophes. And the Lodestone treats them as such. So, instead of confusing users by making
        # them try and dig around in their device settings to turn off Smart Quotes or whatever, this and the below line
        # actually just substitute those "smart quotes" with an apostrophe. This seems simple, but took me a long time
        # to crack, and actually resulted in a lot of errors when I first made Mudbot!
        # Please learn from my mistakes. Essay ovar.
        last_name = last_name.lower().capitalize().replace("‘", "'")  # Oh, also, the information is
        # lowercase'd and then capitalized so that, if someone accidentally mixes punctuation in their name, they don't
        # have to retry.
        world_name = world_name.lower().capitalize()
        async with inter.channel.typing():
            r = requests.get(
                f"""https://na.finalfantasyxiv.com/lodestone/character/?q={first_name}+{last_name}
&worldname={world_name}""")
            if r.status_code != 200:
                embed = disnake.Embed(color=disnake.Color(0x9c2c37), description="Please try again later.",
                                      title="We're sorry; an error occurred!")
                embed.set_author(icon_url=self.bot.user.avatar.url, name=self.bot.user.name)
                embed.set_thumbnail(url=ERROR_IMG)
                embed.set_footer(icon_url=self.bot.user.avatar.url, text=f"Error code: {r.status_code}.")
                await inter.edit_original_response(embed=embed)
                return
            html = Soup(r.text, "html.parser")
            not_found = html.select(".parts__zero")  # This searches for a CSS selector which is used when there
            # are no results found when searching a character.
            if not_found:  # Functions in this block execute if there are no results for a character.
                embed = disnake.Embed(color=disnake.Color(0x9c2c37),
                                      description=f"""There was no character with the name **{first_name} {last_name}**\
 found on **{world_name}**.
 Please ensure all inputs were entered properly and try again.""",
                                      title="Character not found!")
                embed.set_author(icon_url=self.bot.user.avatar.url, name=self.bot.user.name)
                embed.set_thumbnail(url=NOT_FOUND_IMG)
                embed.set_footer(icon_url=inter.guild.icon.url, text="Consider using /id_link instead.")
                await inter.edit_original_response(embed=embed)
                return
            for character in html.select("div.entry"):  # Iterates through every character result returned and finds
                # the one that has the same first, last, AND world name that was entered.
                # Mudbot < 3.0 actually didn't check for world name, which was silly of me.
                name = re.search(r"""entry__name\">([\w'-]{2,15})\s([\w'-]{2,15})<""",
                                str(character.select(".entry__name")))
                world = re.search(r"""\"Home World\"></i>(\w{4,13})\s\[""",
                                  str(character.select(".entry__world")))
                if name is not None and f"{name.group(1)} {name.group(2)}" == f"{first_name} {last_name}" and \
                        world is not None and f"{world.group(1)}" == f"{world_name}":
                    character = character
                    break  # Stops iterating in the above loop if this is the correct character. Usually only needs to
                    # do one loop, but this stops it from going on and on and on if it finds the correct character
                    # but there's 30 more pages of characters.
                else:
                    continue
            else:
                if len(first_name) < 4 or len(last_name) < 4:  # OK, so: For some reason, the Lodestone is WILDLY
                    # INCONSISTENT with returning correct character names if either your first OR last name is short.
                    # It could really use some fuzzy matching, to be honest. Unfortunately, this problem gets passed
                    # to the user. Some names are just too short to reliably find, and, in lieu of allowing the bot to
                    # loop through a hundred different characters before finding the right one, it just. Doesn't.
                    embed = disnake.Embed(color=disnake.Color(0x9c2c37),
                                          description="""Your character's name is too short to reliably find. \
Please consider trying again using your Lodestone ID in /id_link.""", title="Character not found!")
                    embed.set_author(icon_url=self.bot.user.avatar.url, name=self.bot.user.name)
                    embed.set_thumbnail(url=NOT_FOUND_IMG)
                    embed.set_footer(icon_url=inter.guild.icon.url, text="Bog in, flush out!")
                    await inter.edit_original_response(embed=embed)
                else:  # Functions in this block execute if there were straight up zero results for the information
                    # the user provided.
                    embed = disnake.Embed(color=disnake.Color(0x9c2c37),
                                          description=f"""There was no character with the name **{first_name} \
{last_name}** found on **{world_name}**.
Please ensure all inputs were entered properly and try again.""", title="Character not found!")
                    embed.set_author(icon_url=self.bot.user.avatar.url, name=self.bot.user.name)
                    embed.set_thumbnail(url=NOT_FOUND_IMG)
                    embed.set_footer(icon_url=inter.guild.icon.url, text="Consider using /id_link instead.")
                    await inter.edit_original_response(embed=embed)
                return
            character_id = re.search(r"/lodestone/character/(\d{1,11})/",
                                     str(character.select(".entry__link"))).group(1)  # Grabs the character ID from
            # the returned webpage, which is then...
            await self.link_func(self=self, inter=inter, character_id=character_id)  # Passed to this function, so it
            # can find the character's full page in the link_func.

    @commands.slash_command(description="Unlinks your FFXIV character from your Discord.", name="unlink")
    @commands.contexts(guild=True)
    async def unlink(self, inter):
        embed = disnake.Embed(color=disnake.Color(0x3b9da5),
                              description="Are you sure you want to unlink your accounts?", title="Confirmation")
        embed.set_author(icon_url=self.bot.user.avatar.url, name=self.bot.user.name)
        embed.set_thumbnail(url=WARNING_IMG)
        embed.set_footer(icon_url=self.bot.user.avatar.url, text="This will restrict your access to Aether Hunts!")
        # This seriously WILL restrict your access to Aether Hunts. It removes ALL of your roles, except ones above
        # Mudbot in the role hierarchy. Which is definitely confusing, at least.
        view = Confirmation()  # A confirmation.
        await inter.response.send_message(delete_after=300, embed=embed, ephemeral=True, view=view)
        await view.wait()
        if Confirmation.forward is False:
            embed = disnake.Embed(color=disnake.Color(0x9c2c37),
                                  description="A negative response was given.",
                                  title="Unlinking aborted.")
            embed.set_author(icon_url=self.bot.user.avatar.url, name=self.bot.user.name)
            embed.set_thumbnail(url=ERROR_IMG)
            embed.set_footer(icon_url=self.bot.user.avatar.url, text="No further action necessary.")
            await inter.edit_original_response(embed=embed, view=None)
            return
        try:
            con = sqlite3.connect("characters.db", timeout=30.0)
        except OperationalError:
            embed = disnake.Embed(color=disnake.Color(0x9c2c37),
                                  description="Please wait a moment and try again.",
                                  title="We're sorry; an error occurred!")
            embed.set_author(icon_url=self.bot.user.avatar.url, name=self.bot.user.name)
            embed.set_thumbnail(url=ERROR_IMG)
            embed.set_footer(icon_url=self.bot.user.avatar.url, text="Bog in, flush out!")
            await inter.edit_original_response(embed=embed, view=None)
            return
        cur = con.cursor()
        cur.execute("SELECT discord_id FROM characters")
        ids = cur.fetchall()
        con.close()
        for id_ in ids:
            id_ = re.search(r"\(\'(\d+)\',", str(id_))
            if id_ is None:
                id_ = re.search(r"\((\d+),", str(id_))
            if id_.group(1) == str(inter.author.id):
                break
        else:
            embed = disnake.Embed(color=disnake.Color(0x9c2c37),
                                  description="You are not in my database.",
                                  title="We're sorry; an error occurred!")
            embed.set_author(icon_url=self.bot.user.avatar.url, name=self.bot.user.name)
            embed.set_thumbnail(url=ERROR_IMG)
            embed.set_footer(icon_url=self.bot.user.avatar.url,
                             text="If you would like, you may /link and /unlink to be sure.")
            await inter.edit_original_response(embed=embed, view=None)
            return
        try:
            con = sqlite3.connect("characters.db", timeout=30.0)
        except OperationalError:
            embed = disnake.Embed(color=disnake.Color(0x9c2c37),
                                  description="Please wait a moment and try again.",
                                  title="We're sorry; an error occurred!")
            embed.set_author(icon_url=self.bot.user.avatar.url, name=self.bot.user.name)
            embed.set_thumbnail(url=ERROR_IMG)
            embed.set_footer(icon_url=self.bot.user.avatar.url, text="Bog in, flush out!")
            await inter.edit_original_response(embed=embed, view=None)
            return
        con.execute(f"DELETE FROM characters WHERE discord_id = '{str(inter.author.id)}'")
        con.commit()
        con.close()
        try:  # This command removes all roles from the user to ensure they do not have access to the server.
            for role in inter.author.roles:
                try:
                    await inter.author.remove_roles(role)
                except (Forbidden, HTTPException):
                    continue
        except (Forbidden, HTTPException):
            pass
        embed = disnake.Embed(color=disnake.Color(0x3b9da5),
                                description="If applicable, all member roles have been removed from you.",
                                title="Unlinking complete!")
        embed.set_author(icon_url=self.bot.user.avatar.url, name=self.bot.user.name)
        embed.set_thumbnail(url=ERROR_IMG)
        embed.set_footer(icon_url=self.bot.user.avatar.url, text="Bog in, flush out!")
        await inter.edit_original_response(embed=embed, view=None)
        await inter.delete_original_response(delay=300)


def setup(bot):
    bot.add_cog(Verification(bot))
