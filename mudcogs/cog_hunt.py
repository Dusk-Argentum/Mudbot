import disnake
from disnake.ext import commands
from disnake.ext.commands import MissingAnyRole

import json

from mudbot import PREFIX
from mudcogs import cog_tasks


FATE_ICON_URL = "http://ffxiv.gamerescape.com/w/images/1/11/Map65_Icon.png"  # Defines the FATE icon url global
# variable, since it's used a few times.
FATE_COLOR = 0xff00fb  # Same, but with the color.


MINION_ICON_URL = "https://cdn.discordapp.com/attachments/740603224826052608/740754471575093369/Minion.png"  # Defines
# the Minion icon url global variable, since it's long af.
MINION_COLOR = 0x757a92


RG_ICON_URL = "https://www.retahgaming.com/favicon.png"  # Thank you to Retah Sosshaa of Midgardsormr for this
# wonderful site and allowing me to use your maps and assets. Keep up the good work!


class Hunt(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):  # Defines a check that applies to every command in this cog.
        hunter = disnake.utils.get(ctx.guild.roles, name="Licensed Hunter")
        if hunter not in ctx.author.roles:
            raise MissingAnyRole([1])
        return hunter in ctx.author.roles  # Permits the command to execute if the admin role is in the author's roles.

    @commands.command(aliases=["f"], brief="Shows FATE information.", help="""Shows the spawning conditions and the \
locations of FATEs.""", name="fate", usage="fate (name)")
    @commands.guild_only()
    async def fate(self, ctx, *, fate: str = None):
        with open("fates.json", "r", encoding="utf-8") as fates:  # Opens the FATE JSON with a specific file encoding,
            # as certain characters within the JSON render oddly if the encoding is not provided.
            data = json.load(fates)
        for expansions, fates in data["fates"].items():  # Gets the list of expansions and FATEs from the FATEs JSON.
            for names in fates.keys():  # Functions in this block essentially check to ensure the provided FATE exists.
                keys = names.split(" | ")
                for count, unused in enumerate(keys):
                    if fate is None:
                        break
                    elif fate.lower().removeprefix('"').removesuffix('"') == str(keys[int(count)]).lower():
                        fate = names
                        break
                    else:
                        continue
                else:
                    continue
                break
            else:
                continue
            break
        else:  # The above is probably very bad Python, but it works.
            await ctx.send(f"The FATE `{fate}` was not found. To view a list of valid FATEs, use `{PREFIX}fate`.")
            return
        if fate is None:  # Functions in this block execute if the FATE provided either does not exist, or if no
            # name is provided.
            embed = disnake.Embed(color=FATE_COLOR, description=f"""Final Fantasy XIV holds a number of creatures \
from other Final Fantasy games as bosses in powerful FATEs, granting rewards upon completion. These FATEs are \
listed below.
To view a specific FATE, use `{PREFIX}fate <name>`, eg. `{PREFIX}fate ixion` or `{PREFIX}fate "A Horse Outside"`.""",
                                  title="FATEs")
            embed.set_author(icon_url=FATE_ICON_URL, name="FATE Information")
            embed.set_thumbnail(url=FATE_ICON_URL)
            embed.set_footer(icon_url=RG_ICON_URL, text="Maps by RetahGaming.com")
            expansions = []
            for expansion in data["fates"]:  # Functions in this block essentially put together a list of expansions
                # and their major FATEs.
                expansions.append(expansion)
                fates = []
                monsters = []
                shorts = []
                monster_urls = []
                fate_urls = []
                for fate in data["fates"][expansion].keys():
                    monsters.append(fate.split(" | ")[0])
                    fates.append(fate.split(" | ")[1])
                    shorts.append(fate.split(" | ")[2])
                    monster_urls.append(data["fates"][expansion][fate]["monster_url"])
                    fate_urls.append(data["fates"][expansion][fate]["fate_url"])
                    continue
                else:
                    value = []
                    for count, fate in enumerate(monsters):
                        value.append(f"""[**{monsters[int(count)]}**]({monster_urls[int(count)]}) | \
[{fates[int(count)]}]({fate_urls[int(count)]}) | \
`{PREFIX}fate {shorts[int(count)]}`\n""")
                        continue
                    embed.add_field(inline=False, name=expansion, value="".join(value))
                    continue
            await ctx.send(embed=embed)
        elif fate is not None:  # Gets a specific FATE if provided.
            info = data["fates"][expansions][fate]
            embed = disnake.Embed(color=FATE_COLOR, description=info["description"],
                                  title=f"""{info["location"]} | Level \
{info["level"]} FATE""")
            embed.set_author(icon_url=FATE_ICON_URL, name=info["name"])
            embed.set_thumbnail(url=info["thumbnail"])
            embed.add_field(inline=True, name="Spawn Timer:", value=info["timer"])
            if info["weather"] != "":
                embed.add_field(inline=True, name="Weather:", value=info["weather"])
            embed.add_field(inline=False, name="Rewards:", value=info["rewards"])
            if info["process"] != "":
                embed.add_field(inline=False, name="Preceding FATEs:", value=info["process"])
            embed.set_image(url=info["map"])
            embed.set_footer(icon_url=RG_ICON_URL, text="Maps by RetahGaming.com")
            await ctx.send(embed=embed)

    @commands.command(aliases=["goss", "gossip", "m", "shroud"], brief="Shows the location of SS Rank minions.",
                      help="""Shows the locations of the SS Rank minions (Forgiven Gossip [ShB]/Ker Shroud [EW]) in \
the provided zone.""", name="minions", usage="minions (mark) (zone)")
    @cog_tasks.is_allowed_channel()
    @commands.guild_only()
    async def minions(self, ctx, mark: str = None, zone: str = None):
        with open("minions.json", "r", encoding="utf-8") as minions:
            data = json.load(minions)
        for expansions, minions in data["minions"].items():
            for names in minions.keys():
                keys = names.split(" | ")
                for count, mark_full in enumerate(keys):
                    if mark is None:
                        break
                    if zone is None:
                        await ctx.send(f"""Please specify what zone the mark has spawned in. Example usage: `{PREFIX}\
minions "Forgiven Rebellion" "Amh Araeng"`.""")
                        return
                    if mark.lower().removeprefix('"').removesuffix('"') == str(keys[int(count)]).lower():
                        mark = names
                        for location in data["minions"][expansions][names]["locations"].keys():
                            keys = location.split(" | ")
                            for count1, zone_full in enumerate(keys):
                                if zone.lower().removeprefix('"').removesuffix('"') == str(keys[int(count1)]).lower():
                                    zone = location
                                    break
                            else:
                                continue
                        break
                    else:
                        continue
                else:
                    continue
                break
            else:
                continue
            break
        else:
            await ctx.send(f"""The mark/zone pairing of `{mark}` `{zone}` was not valid. Correct usage: `{PREFIX}\
minions <mark> <zone>`, eg. `{PREFIX}minions "Forgiven Rebellion" "Amh Araeng"`.""")
            return
        if mark is None:
            embed = disnake.Embed(color=MINION_COLOR, description=f"""Upon the defeat of S Rank marks in zones \
within Shadowbringers or Endwalker, there is a chance that the minions of an extraordinarily powerful mark will begin \
to prey... Find and defeat them to spawn their respective extraordinarily powerful marks! These marks are listed below.
To view the spawning locations for a specific mark's minions on a specific map, use `{PREFIX}minions <mark> <zone>`, \
eg. `{PREFIX}minions "Forgiven Rebellion" "Amh Araeng"` or `{PREFIX}minions Ker Garlemald`.
**As a reminder, bringing up a map pings the S Rank role, so please only bring up a map when a mark has spawned there\
**. If you wish to view the maps alone, you can view them on the \
[RetahGaming.com](https://www.retahgaming.com/ffxiv/huntmaps.php) website.""", title="Minions")
            embed.set_author(icon_url=MINION_ICON_URL, name="Minion Information")
            embed.set_thumbnail(url=MINION_ICON_URL)
            embed.set_footer(icon_url=RG_ICON_URL, text="Maps by RetahGaming.com")
            expansions = []
            for count, expansion in enumerate(data["minions"]):
                expansions.append(expansion)
                aliases = []
                locations = []
                location_aliases = []
                marks = []
                mark_aliases = []
                urls = []
                for mark in data["minions"][expansion].keys():
                    aliases.append(mark.split(" | ")[1])
                    marks.append(mark.split(" | ")[0])
                    for location in data["minions"][expansion][mark]["locations"].keys():
                        locations.append(location.split(" | ")[0])
                        location_aliases.append(location.split(" | ")[1])
                        mark_aliases.append(str(data["minions"][expansion].keys()).split(" | ")[1].removesuffix("'])"))
                        urls.append(data["minions"][expansion][mark]["locations"][location]["url"])
                else:
                    value = [f"**{data['minions'][expansion][mark]['name']}**"]
                    for count2, location in enumerate(locations):
                        value.append(f"""[{location}]({urls[int(count2)]}) (`{PREFIX}minions {mark_aliases[int(count2)]} \
{location_aliases[int(count2)]}`)""")
                    str(value).removesuffix(" | ")
                    embed.add_field(inline=False, name=expansion, value=" |\n".join(value))
            await ctx.send(embed=embed)
        elif mark is not None:
            embed = disnake.Embed(color=MINION_COLOR, title="""The minions of an extraordinarily powerful mark are on \
the hunt for prey...""")
            info = data["minions"][expansions][mark]
            embed.set_author(icon_url=info["minion_icon_url"], name=info["minion_name"])
            embed.set_thumbnail(url=info["minion_icon_url"])
            embed.add_field(inline=True, name=f"{info['minion_name']}:", value=info["locations"][zone]["minions"])
            embed.add_field(inline=True, name=f"{info['name']}:", value=info["locations"][zone]["mark"])
            embed.add_field(inline=True, name="World:", value="See previous post.")
            embed.add_field(inline=False, name="Map:", value=f""":blue_circle: | {info["minion_name"]}
:red_circle: | {info["name"]}""")
            embed.set_image(url=info["locations"][zone]["url"])
            embed.set_footer(icon_url=RG_ICON_URL, text="Maps by RetahGaming.com")
            await ctx.send(content=f"""<:minion:610656093680697366> <:minion:610656093680697366> \
{info["ping"]} <:minion:610656093680697366> <:minion:610656093680697366>""", embed=embed)


def setup(bot):
    bot.add_cog(Hunt(bot))
