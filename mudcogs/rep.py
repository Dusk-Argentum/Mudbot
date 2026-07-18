import disnake
from disnake.ext import commands
from disnake.ext.commands import CheckFailure, MissingAnyRole  # Imports the exception that is thrown if the user
# attempting to invoke a command doesn't have the correct role or uses the command in the incorrect channel.


class Rep(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # @staticmethod
    # async def cog_slash_command_check(inter: ApplicationCommandInteraction):  # The check mentioned in the above
    #     # comment.
    #     if inter.data.name in ["conductor", "spawner"] and "rolerequest" not in inter.channel.name:  # Throws a
    #         # CheckFailure exception if the command used is either /conductor or /spawner, and it is used outside a
    #         # role request ticket.
    #         raise CheckFailure
    #     return inter.data.name in ["conductor", "spawner"] and "rolerequest" in inter.channel.name

    @commands.slash_command(description="""REP/MOD. Grants the Conductor role to the mentioned Member. \
Only functions in Tickets.""", name="conductor")  # Note the "REP/MOD"; this is the easiest way I could convey to people
    # that they shouldn't use commands for roles above theirs. They'll error anyway, but the API, for whatever reason,
    # does not allow developers to define commands that shouldn't show up when the / button is hit on a keyboard.
    # It allows it on a per-server level, but doesn't let me define checks at the programming level to hide them...
    # Why?
    @commands.contexts(guild=True)
    @commands.has_any_role("Nutty Rep", "Nutty Moderator")
    async def conductor(self, inter, member: disnake.Member):  # Takes a Member as an argument, which can be done
        # via a Mention or with the Member's ID.
        conductor = disnake.utils.get(inter.guild.roles, name="Conductor")
        await member.add_roles(conductor)  # Adds the retrieved Conductor role to the Member.
        embed = disnake.Embed(color=disnake.Color(0x3b9da5),
                              description=f"Go forth and conduct, {member.mention}.",
                              title="Thank you for your service!")  # 🫡 Good luck staying out of the drama, soldier.
        embed.set_author(icon_url=self.bot.user.avatar.url, name=self.bot.user.name)
        embed.set_thumbnail(
            url="https://cdn.discordapp.com/emojis/593901072423321617.webp?size=48")  # Sets the thumbnail for this
        # embed as the A Rank emoji from AH.
        embed.set_footer(icon_url=inter.guild.icon.url, text=inter.guild.name)  # Uses the current guild's icon and
        # name in the footer.
        await inter.response.send_message(delete_after=300, embed=embed)

    @commands.slash_command(description="""REP/MOD. Grants the Spawner role to the mentioned Member. \
Only functions in Tickets.""", name="spawner")
    @commands.contexts(guild=True)
    @commands.has_any_role("Nutty Rep", "Nutty Moderator")
    async def spawner(self, inter, member: disnake.Member):
        spawner = disnake.utils.get(inter.guild.roles, name="Spawner")
        await member.add_roles(spawner)
        embed = disnake.Embed(color=disnake.Color(0x3b9da5),
                              description=f"Go forth and spawn, {member.mention}.",
                              title="Thank you for your service!")
        embed.set_author(icon_url=self.bot.user.avatar.url, name=self.bot.user.name)
        embed.set_thumbnail(
            url="https://cdn.discordapp.com/emojis/758323900219523082.webp?size=48")  # Sets the thumbnail for this
        # embed as the S Rank emoji from AH.
        embed.set_footer(icon_url=inter.guild.icon.url, text=inter.guild.name)
        await inter.response.send_message(delete_after=300, embed=embed)


def setup(bot):
    bot.add_cog(Rep(bot))
