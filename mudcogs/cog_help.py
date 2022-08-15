import disnake
from disnake.ext import commands
from disnake.ext.commands import MissingAnyRole, NotOwner

from mudbot import PREFIX, VERSION


class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=["h"], brief="Shows commands.",
                      help="Lists all commands, their aliases, and their functions.", name="help",
                      usage="help (module)")
    @commands.guild_only()
    async def help_(self, ctx, module: str = None):  # Function name defined with an underscore to avoid naming conflict
        # with default help command.
        embed = disnake.Embed(color=disnake.Color(0x3b9da5),
                              description=f"""{'To view in-depth information on a module, use '
                                               f'`{PREFIX}help [module]`, eg. '
                                               f'`{PREFIX}help "Verification"`.' if module is None else ''}
Arguments are surrounded with **<**pointy brackets**>**, while subcommands are surrounded with \
**[**square brackets**]**.
Optional arguments are surrounded in **(**parenthesis**)**; these arguments can be omitted with no loss of function.
An **argument** causes a specific function, while a **subcommand** is a list of further functions.""",
                              title=f"{self.bot.user.name}'s Commands:")  # Let me know if you spot any command usage
        # snippets that do not adhere to this role. I kind of lost the plot with what convention I was using at some
        # point.
        embed.set_author(icon_url=self.bot.user.avatar.url, name=self.bot.user.name)
        embed.set_thumbnail(url=self.bot.user.avatar.url)
        if module is None:  # Functions in this block execute if the module argument is not provided.
            for cog in self.bot.cogs:
                admin = disnake.utils.get(ctx.guild.roles, name="Admin")
                hunter = disnake.utils.get(ctx.guild.roles, name="Licensed Hunter")
                mod = disnake.utils.get(ctx.guild.roles, name="Nutty Moderator")
                rep = disnake.utils.get(ctx.guild.roles, name="Nutty Rep")
                if admin not in ctx.author.roles and cog == "Admin":
                    continue
                if hunter not in ctx.author.roles and cog == "Hunt":
                    continue
                if mod not in ctx.author.roles and cog == "Mod":
                    continue
                if rep not in ctx.author.roles and cog == "Rep":  # Functions in this block execute if the Rep role
                    # is not in the author's roles.
                    if mod in ctx.author.roles and cog == "Rep":  # But executes anyway if Mod is in it.
                        pass
                    else:
                        continue  # Essentially stops the gated modules from appearing in the help.
                if ctx.author.id != self.bot.owner_id and cog == "Owner":
                    continue
                commands = []
                if not self.bot.get_cog(cog).get_commands():  # Functions in this block prevent commands that are not
                    # in the cog from appearing under that cog.
                    continue
                for command in self.bot.get_cog(cog).get_commands():
                    commands.append(f"""►**`{command.name}`** (Alias{"es" if len(command.aliases) > 1 else ""}: `\
{"` | `".join(command.aliases)}`)
{command.brief}
Usage: `{PREFIX}{command.usage}`\n""")
                    continue
                embed.add_field(inline=False, name=f"Module | **{cog}**", value="".join(commands))
                continue
        elif module is not None:  # Functions in this block execute if the module is provided.
            for cog in self.bot.cogs:  # Functions in this block essentially check that the cog exists.
                if cog.lower() == module.lower():
                    cog = cog
                    break
                elif cog.lower() != module.lower():
                    continue
            else:
                await ctx.send(f"The module `{module}` was not found. To view a list of modules, use `{PREFIX}help`.")
                return
            admin = disnake.utils.get(ctx.guild.roles, name="Admin")
            mod = disnake.utils.get(ctx.guild.roles, name="Nutty Moderator")
            owner = await self.bot.fetch_user(self.bot.owner_id)
            rep = disnake.utils.get(ctx.guild.roles, name="Nutty Rep")
            if cog == "Admin" and admin not in ctx.author.roles:
                raise MissingAnyRole([1])
            elif cog == "Mod" and mod not in ctx.author.roles:
                raise MissingAnyRole([1])
            elif cog == "Owner" and ctx.author.id != owner.id:
                raise NotOwner
            elif cog == "Rep" and rep not in ctx.author.roles:
                if mod not in ctx.author.roles:
                    raise MissingAnyRole([1])
            for command in self.bot.get_cog(cog).get_commands():  # Functions in this block scrumble together a list of
                # commands in that cog and some of their subcommands/arguments.
                arguments = []
                subcommands = []
                for subcommand in self.bot.get_cog(cog).walk_commands():
                    if subcommand.root_parent is None:
                        continue
                    if subcommand.root_parent is not None and subcommand.root_parent.name is not command.name:
                        continue
                    if subcommand.root_parent is not None:
                        if isinstance(subcommand, disnake.ext.commands.Group):
                            subcommands.append(f"`{subcommand.name}`")
                        elif isinstance(subcommand, disnake.ext.commands.Command):
                            arguments.append(f"`{subcommand.name}`")
                        continue
                arguments.sort()
                subcommands.sort()
                newline = "\n"
                embed.add_field(inline=False,
                                name=f"""►**`{command.name}`** (Alias{"es" if len(command.aliases) > 1 else ""}: `\
{"` | `".join(command.aliases)}`)""", value=f"""{command.help}\
{f"{newline}" if len(arguments) > 0 else ""}\
{f"► Argument{'s' if len(arguments) > 1 else ''}: {' | '.join(arguments)}" if len(arguments) > 0 else ""}\
{f"{newline}" if len(subcommands) > 0 else ""}\
{f"► Subcommand{'s' if len(subcommands) > 1 else ''}: {' | '.join(subcommands)}" if len(subcommands) > 0 else ""}
► Usage: `{PREFIX}{command.usage}`""")
        owner = await self.bot.fetch_user(self.bot.owner_id)
        embed.set_footer(icon_url=owner.avatar.url, text=f"""Developer: {owner.name} | {VERSION}
Bot avatar by @pixel__toast on Twitter.""")
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Help(bot))
