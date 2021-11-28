from datetime import datetime, timezone


import disnake
from disnake.ext import commands
from disnake.ext.commands import MemberNotFound, MissingAnyRole


import json


from mudcogs import cog_tasks


class Rep(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        rep = disnake.utils.get(ctx.guild.roles, name="Nutty Rep")
        mod = disnake.utils.get(ctx.guild.roles, name="Nutty Moderator")
        if rep not in ctx.author.roles:
            if mod not in ctx.author.roles:
                raise MissingAnyRole([1])
        return rep in ctx.author.roles or mod in ctx.author.roles

    @commands.command(aliases=["conduct"], brief="Adds Conductor to the mentioned member.", help="""Adds the \
Conductor role to the mentioned member. Only usable in tickets.""", name="conductor", usage="conductor <mention>")
    @cog_tasks.is_allowed_channel()
    @commands.guild_only()
    async def conductor(self, ctx, member: disnake.Member = None):
        if member is None:
            raise MemberNotFound("member")
        if member not in ctx.channel.members:
            await ctx.send("""That member is not in this channel. Please confirm you have the correct member.""")
            return
        conductor = disnake.utils.get(ctx.guild.roles, name="Conductor")
        await member.add_roles(conductor)
        await ctx.message.add_reaction("👍")

    @commands.command(aliases=["early", "ep"], brief="Sets the early pull complaint timer.", help="""Sets the early \
pull complaint timer.""", name="early_pull", usage="early_pull")  # THERE WILL BE MORE.
    @commands.guild_only()
    async def early_pull(self, ctx):
        with open("complaint_log.json", "r") as complaint_log:
            data = json.load(complaint_log)
        last_complaint = datetime.strptime(str(data["complaint_log"]["last_complaint"]), "%Y-%m-%d %H:%M:%S")
        current_duration = int(str((datetime.strptime(str(datetime.now(timezone.utc)).split(".")[0],
                                                      "%Y-%m-%d %H:%M:%S") - last_complaint).total_seconds()).split(".")
                               [0])
        longest_duration = int(data["complaint_log"]["longest_duration"])
        if current_duration > longest_duration:
            longest_duration = str(current_duration)
            longest_duration_update = {"longest_duration": longest_duration}
            data["complaint_log"].update(longest_duration_update)
        last_complaint_update = {"last_complaint": str(datetime.now(timezone.utc)).split(".")[0]}
        data["complaint_log"].update(last_complaint_update)
        with open("complaint_log.json", "w") as complaint_log:
            complaint_log.seek(0)
            json.dump(data, complaint_log, indent=4)
            complaint_log.truncate()
        embed = disnake.Embed(color=disnake.Color(0x3b9da5), description="""Please remember that Aether Hunts \
cannot control whether people pull marks early. Sometimes, this happens by accident. Other times, this is done by \
people beyond the mod team's jurisdiction. Regardless, please be advised that there will be additional S Rank \
marks in the future.""", title="Early pull complaint detected!")
        embed.set_author(icon_url=self.bot.user.avatar.url, name=self.bot.user.name)
        embed.set_thumbnail(url=ctx.guild.icon.url)
        days = divmod(current_duration, 86400)
        hours = divmod(days[1], 3600)
        minutes = divmod(hours[1], 60)
        seconds = divmod(minutes[1], 1)
        embed.add_field(inline=True, name="Current:", value=f"""We have gone \
{days[0]} day{"" if days[0] == 1 else "s"}, {hours[0]} hour{"" if hours[0] == 1 else "s"}, \
{minutes[0]} minute{"" if minutes[0] == 1 else "s"}, and {seconds[0]} second{"" if seconds[0] == 1 else "s"} \
since the last logged complaint.""")
        days = divmod(longest_duration, 86400)
        hours = divmod(days[1], 3600)
        minutes = divmod(hours[1], 60)
        seconds = divmod(minutes[1], 1)
        embed.add_field(inline=True, name="Record:", value=f"""Our record between logged complaints is {days[0]} \
day{"" if days[0] == 1 else "s"}, {hours[0]} hour{"" if days[0] == 1 else "s"}, {minutes[0]} minute\
{"" if minutes[0] == 1 else "s"}, and {seconds[0]} second{"" if seconds[0] == 1 else "s"}.""")
        embed.set_footer(icon_url=ctx.guild.icon.url, text=ctx.guild.name)
        await ctx.send(embed=embed)

    @commands.command(aliases=["spawn"], brief="Adds Spawner to the mentioned member.", help="""Adds the \
Spawner role to the mentioned member. Only usable in tickets.""", name="spawner", usage="spawner <mention>")
    @cog_tasks.is_allowed_channel()
    @commands.guild_only()
    async def spawner(self, ctx, member: disnake.Member = None):
        if member is None:
            raise MemberNotFound("member")
        if member not in ctx.channel.members:
            await ctx.send("""That member is not in this channel. Please confirm you have the correct member.""")
            return
        spawner = disnake.utils.get(ctx.guild.roles, name="Spawner")
        await member.add_roles(spawner)
        await ctx.message.add_reaction("👍")


def setup(bot):
    bot.add_cog(Rep(bot))
