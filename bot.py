import discord
from discord.ext import commands
import asyncio
import os
from aiohttp import web

# --- الإعدادات ---
# سيتم قراءة التوكن من إعدادات Render لحمايته
TOKEN = os.getenv('DISCORD_TOKEN')
MUTE_ROLE_NAME = "Among Manger"

intents = discord.Intents.default()
intents.members = True
intents.voice_states = True
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

# --- واجهة الأزرار ---
class MuteControlView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Mute All (كتم الجميع)", style=discord.ButtonStyle.danger, custom_id="mute_all_btn")
    async def mute_all(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.voice:
            await interaction.response.send_message("❌ يجب أن تكون في غرفة صوتية لتنفيذ هذا الأمر.", ephemeral=True)
            return
        if not interaction.user.guild_permissions.mute_members:
            await interaction.response.send_message("❌ ليس لديك صلاحية كتم الأعضاء.", ephemeral=True)
            return

        channel = interaction.user.voice.channel
        mute_role = discord.utils.get(interaction.guild.roles, name=MUTE_ROLE_NAME)
        muted_count = 0

        for member in channel.members:
            if not member.bot and not member.voice.mute:
                try:
                    await member.edit(mute=True)
                    if mute_role:
                        await member.add_roles(mute_role)
                    muted_count += 1
                except discord.Forbidden:
                    pass

        await interaction.response.send_message(f"✅ تم كتم **{muted_count}** عضو في نفس الغرفة.", ephemeral=True)

    @discord.ui.button(label="Unmute All (إلغاء الكتم)", style=discord.ButtonStyle.success, custom_id="unmute_all_btn")
    async def unmute_all(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.voice:
            await interaction.response.send_message("❌ يجب أن تكون في غرفة صوتية لتنفيذ هذا الأمر.", ephemeral=True)
            return
        if not interaction.user.guild_permissions.mute_members:
            await interaction.response.send_message("❌ ليس لديك صلاحية كتم الأعضاء.", ephemeral=True)
            return

        channel = interaction.user.voice.channel
        mute_role = discord.utils.get(interaction.guild.roles, name=MUTE_ROLE_NAME)
        unmuted_count = 0

        for member in channel.members:
            if not member.bot and member.voice.mute:
                try:
                    await member.edit(mute=False)
                    if mute_role and mute_role in member.roles:
                        await member.remove_roles(mute_role)
                    unmuted_count += 1
                except discord.Forbidden:
                    pass

        await interaction.response.send_message(f"✅ تم إلغاء كتم **{unmuted_count}** عضو.", ephemeral=True)

@bot.event
async def on_ready():
    bot.add_view(MuteControlView())
    print(f'تم تسجيل الدخول باسم {bot.user}')

@bot.command(name='setup_mute')
@commands.has_permissions(administrator=True)
async def setup_mute(ctx):
    embed = discord.Embed(
        title="🎮 لوحة تحكم أمونق ميوت",
        description="اضغط على الأزرار بالأسفل للتحكم في كتم اللاعبين في الغرفة الصوتية الحالية.",
        color=discord.Color.blue()
    )
    await ctx.send(embed=embed, view=MuteControlView())

# --- سيرفر ويب وهمي لإبقاء Render سعيداً ---
async def handle(request):
    return web.Response(text="Bot is running!")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    # Render سيعطينا منفذ (Port) تلقائياً
    port = int(os.getenv('PORT', 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()

# --- تشغيل البوت والسيرفر معاً ---
async def main():
    await start_web_server()
    await bot.start(TOKEN)

if __name__ == '__main__':
    asyncio.run(main())