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


RG_ICON_URL = "https://www.retahgaming.com/rgicon.png"  # Thank you to Retah Sosshaa of Midgardsormr for this
# wonderful site and allowing me to use your maps and assets. Keep up the good work!


class Hunt(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):  # Defines a check that applies to every command in this cog.
        hunter = disnake.utils.get(ctx.guild.roles, name="Licensed Hunter")  # Gets the admin role by name.
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

    @commands.group(aliases=["goss", "gossip", "m"], brief="Shows Forgiven Gossip locations.", case_insensitive=True,
                    help="""Shows the locations of the Forgiven Gossip marks in the provided zone.""", name="minions",
                    usage="minions <zone>")
    @cog_tasks.is_allowed_channel()  # Uses a custom check to ensure the command is being executed in an allowed
    # channel.
    @commands.guild_only()
    async def minions(self, ctx):
        if ctx.invoked_subcommand is not None:
            return
        embed = disnake.Embed(color=MINION_COLOR, description="""Upon the defeat of certain S Rank marks \
in Norvrandt, the minions of an extraordinarily powerful mark will begin to prey... Find and defeat them to spawn \
Forgiven Rebellion.""", title="Minions")
        embed.set_author(icon_url=MINION_ICON_URL, name="Forgiven Gossip")
        embed.set_thumbnail(url=MINION_ICON_URL)
        argument = []
        for arguments in ctx.command.walk_commands():
            argument.append(arguments)
        argument.sort(key=lambda argus: argus.name)  # I don't know what lambda does and when I tried to look it
        # up I literally had to go take a break. The fuck is an "anonymous function"?
        # I wrote this comment when I initially made this function and I still don't know what lambda does.
        for count, arguments in enumerate(argument):
            embed.add_field(inline=False, name=f"""`{argument[count].name}` (Alias{"es" if
            len(argument[count].aliases) > 1 else ""}: `{"`, `".join(argument[count].aliases)}`)""",
                            value=argument[count].help)
        embed.set_footer(icon_url=RG_ICON_URL, text="Maps by RetahGaming.com")
        await ctx.send(embed=embed)

    @minions.command(aliases=["aa", "ahmaraeng"], brief="Shows the minions map for Amh Araeng.", help="Shows the \
spawning locations of Forgiven Gossip in Amh Araeng.", name="amharaeng", usage="minions amharaeng")
    @commands.guild_only()
    async def amharaeng(self, ctx, world: str = "See previous post."):  # Most people won't realize you can define
        # what world FR is on now, so the default argument is the previous default.
        embed = disnake.Embed(color=MINION_COLOR, title="""The minions of an extraordinarily powerful mark are on \
the hunt for prey...""")
        embed.set_author(icon_url=MINION_ICON_URL, name="Forgiven Gossip")
        embed.set_thumbnail(url=MINION_ICON_URL)
        embed.add_field(inline=True, name="Forgiven Gossip:", value="""`X 14 Y 32`
`X 13 Y 12`
`X 30 Y 10`
`X 30 Y 25`""")
        embed.add_field(inline=True, name="Forgiven Rebellion:", value="`X 27 Y 35`")
        embed.add_field(inline=True, name="World:", value=world)
        embed.add_field(inline=False, name="Map:", value=""":blue_circle: | Forgiven Gossip
:red_circle: | Forgiven Rebellion""")
        embed.set_image(url="https://retahgaming.com/ffxiv/images/shfull/ahmssfull.gif")
        embed.set_footer(icon_url=RG_ICON_URL, text="Maps by RetahGaming.com")
        await ctx.send(content="""<:minion:610656093680697366> <:minion:610656093680697366> \
<@&570459958123167745> <:minion:610656093680697366> <:minion:610656093680697366>""", embed=embed)

    @minions.command(aliases=["il", "ilmeg"], brief="Shows the minions map for Il Mheg.", help="""Shows the \
spawning locations of Forgiven Gossip in Il Mheg.""", name="ilmheg", usage="minions ilmheg")
    async def ilmheg(self, ctx, world: str = "See previous post."):
        embed = disnake.Embed(color=MINION_COLOR, title="""The minions of an extraordinarily powerful mark are on \
the hunt for prey...""")
        embed.set_author(icon_url=MINION_ICON_URL, name="Forgiven Gossip")
        embed.set_thumbnail(url=MINION_ICON_URL)
        embed.add_field(inline=True, name="Forgiven Gossip:", value="""`X 06 Y 30`
`X 32 Y 11`
`X 25 Y 22`
`X 24 Y 37`""")
        embed.add_field(inline=True, name="Forgiven Rebellion:", value="`X 13 Y 23`")
        embed.add_field(inline=True, name="World:", value=world)
        embed.add_field(inline=False, name="Map:", value=""":blue_circle: | Forgiven Gossip
:red_circle: | Forgiven Rebellion""")
        embed.set_image(url="https://retahgaming.com/ffxiv/images/shfull/mhegssfull.gif")
        embed.set_footer(icon_url=RG_ICON_URL, text="Maps by RetahGaming.com")
        await ctx.send(content="""<:minion:610656093680697366> <:minion:610656093680697366> \
<@&570459958123167745> <:minion:610656093680697366> <:minion:610656093680697366>""", embed=embed)

    @minions.command(aliases=["kh", "khol", "ko"], brief="Shows the minions map for Kholusia.", help="""Shows the \
spawning locations of Forgiven Gossip in Kholusia.""", name="kholusia", usage="minions kholusia")
    async def kholusia(self, ctx, world: str = "See previous post."):
        embed = disnake.Embed(color=MINION_COLOR, title="""The minions of an extraordinarily powerful mark are on \
the hunt for prey...""")
        embed.set_author(icon_url=MINION_ICON_URL, name="Forgiven Gossip")
        embed.set_thumbnail(url=MINION_ICON_URL)
        embed.add_field(inline=True, name="Forgiven Gossip:", value="""`X 08 Y 29`
`X 12 Y 15`
`X 23 Y 15`
`X 33 Y 32`""")
        embed.add_field(inline=True, name="Forgiven Rebellion:", value="`X 24 Y 37`")
        embed.add_field(inline=True, name="World:", value=world)
        embed.add_field(inline=False, name="Map:", value=""":blue_circle: | Forgiven Gossip
:red_circle: | Forgiven Rebellion""")
        embed.set_image(url="https://retahgaming.com/ffxiv/images/shfull/kholusiassfull.gif")
        embed.set_footer(icon_url=RG_ICON_URL, text="Maps by RetahGaming.com")
        await ctx.send(content="""<:minion:610656093680697366> <:minion:610656093680697366> \
<@&570459958123167745> <:minion:610656093680697366> <:minion:610656093680697366>""", embed=embed)

    @minions.command(aliases=["ll", "lake"], brief="Shows the minions map for Lakeland.", help="""Shows the \
spawning locations of Forgiven Gossip in Lakeland.""", name="lakeland", usage="minions lakeland")
    # Aliases are out of alphabetical order on purpose here.
    async def lakeland(self, ctx, world: str = "See previous post."):
        embed = disnake.Embed(color=MINION_COLOR, title="""The minions of an extraordinarily powerful mark are on \
the hunt for prey...""")
        embed.set_author(icon_url=MINION_ICON_URL, name="Forgiven Gossip")
        embed.set_thumbnail(url=MINION_ICON_URL)
        embed.add_field(inline=True, name="Forgiven Gossip:", value="""`X 10 Y 25`
`X 13 Y 10`
`X 33 Y 12`
`X 30 Y 36`""")
        embed.add_field(inline=True, name="Forgiven Rebellion:", value="`X 23 Y 22`")
        embed.add_field(inline=True, name="World:", value=world)
        embed.add_field(inline=False, name="Map:", value=""":blue_circle: | Forgiven Gossip
:red_circle: | Forgiven Rebellion""")
        embed.set_image(url="https://retahgaming.com/ffxiv/images/shfull/lakelandssfull.gif")
        embed.set_footer(icon_url=RG_ICON_URL, text="Maps by RetahGaming.com")
        await ctx.send(content="""<:minion:610656093680697366> <:minion:610656093680697366> \
<@&570459958123167745> <:minion:610656093680697366> <:minion:610656093680697366>""", embed=embed)

    @minions.command(aliases=["rk", "rak_tika", "rak'tika", "rak", "rg", "rt"], brief="""Shows the minions map for \
the Rak'tika Greatwood.""", help="""Shows the spawning locations of Forgiven Gossip in the Rak'tika Greatwood.""",
                     # Aliases are also out of order on purpose here.
                     name="raktika", usage="minions raktika")
    async def raktika(self, ctx, world: str = "See previous post."):
        embed = disnake.Embed(color=MINION_COLOR, title="""The minions of an extraordinarily powerful mark are on \
the hunt for prey...""")
        embed.set_author(icon_url=MINION_ICON_URL, name="Forgiven Gossip")
        embed.set_thumbnail(url=MINION_ICON_URL)
        embed.add_field(inline=True, name="Forgiven Gossip:", value="""`X 15 Y 36`
`X 05 Y 22`
`X 19 Y 22`
`X 30 Y 13`""")
        embed.add_field(inline=True, name="Forgiven Rebellion:", value="`X 24 Y 37`")
        embed.add_field(inline=True, name="World:", value=world)
        embed.add_field(inline=False, name="Map:", value=""":blue_circle: | Forgiven Gossip
:red_circle: | Forgiven Rebellion""")
        embed.set_image(url="https://retahgaming.com/ffxiv/images/shfull/greatwoodssfull.gif")
        embed.set_footer(icon_url=RG_ICON_URL, text="Maps by RetahGaming.com")
        await ctx.send(content="""<:minion:610656093680697366> <:minion:610656093680697366> \
<@&570459958123167745> <:minion:610656093680697366> <:minion:610656093680697366>""", embed=embed)

    @minions.command(aliases=["tm", "temp", "tmp"], brief="Shows the minions map for the Tempest.", help="""Shows the \
spawning locations of Forgiven Gossip in the Tempest.""", name="tempest", usage="minions tempest")
    # And here.
    async def tempest(self, ctx, world: str = "See previous post."):
        embed = disnake.Embed(color=MINION_COLOR, title="""The minions of an extraordinarily powerful mark are on \
the hunt for prey...""")
        embed.set_author(icon_url=MINION_ICON_URL, name="Forgiven Gossip")
        embed.set_thumbnail(url=MINION_ICON_URL)
        embed.add_field(inline=True, name="Forgiven Gossip:", value="""`X 08 Y 07`
`X 25 Y 09`
`X 38 Y 14`
`X 34 Y 30`""")
        embed.add_field(inline=True, name="Forgiven Rebellion:", value="`X 13 Y 22`")
        embed.add_field(inline=True, name="World:", value=world)
        embed.add_field(inline=False, name="Map:", value=""":blue_circle: | Forgiven Gossip
:red_circle: | Forgiven Rebellion""")
        embed.set_image(url="https://retahgaming.com/ffxiv/images/shfull/tempestssfull.gif")
        embed.set_footer(icon_url=RG_ICON_URL, text="Maps by RetahGaming.com")
        await ctx.send(content="""<:minion:610656093680697366> <:minion:610656093680697366> \
<@&570459958123167745> <:minion:610656093680697366> <:minion:610656093680697366>""", embed=embed)


def setup(bot):
    bot.add_cog(Hunt(bot))
