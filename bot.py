import discord
from discord.ext import commands
import asyncio
import os
from aiohttp import web

# --- الإعدادات ---
TOKEN = os.getenv('DISCORD_TOKEN')
MUTE_ROLE_NAME = "AMONG US MANAGER"

intents = discord.Intents.default()
intents.members = True
intents.voice_states = True
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

# --- واجهة الأزرار (Buttons) ---
class MuteControlView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Mute All (كتم الجميع)", style=discord.ButtonStyle.danger, custom_id="mute_all_btn")
    async def mute_all(self, interaction: discord.Interaction, button: discord.ui.Button):
        # 1. التحقق من وجود المستخدم في غرفة صوتية
        if not interaction.user.voice:
            await interaction.response.send_message("❌ يجب أن تكون في غرفة صوتية لتنفيذ هذا الأمر.", ephemeral=True)
            return
        
        # 2. التحقق من أن المستخدم يمتلك رول المدير
        target_role = discord.utils.get(interaction.guild.roles, name=MUTE_ROLE_NAME)
        if not target_role or target_role not in interaction.user.roles:
            await interaction.response.send_message(f"❌ يجب أن تمتلك رول '{MUTE_ROLE_NAME}' لاستخدام هذا الزر.", ephemeral=True)
            return

        channel = interaction.user.voice.channel
        muted_count = 0

        # 3. كتم جميع الأعضاء في الغرفة (ما عدا من ضغط الزر)
        for member in channel.members:
            if not member.bot and member != interaction.user and not member.voice.mute:
                try:
                    await member.edit(mute=True)
                    muted_count += 1
                except discord.Forbidden:
                    pass

        await interaction.response.send_message(f"✅ تم كتم **{muted_count}** عضو في الغرفة (باستثناء أنت).", ephemeral=True)

    @discord.ui.button(label="Unmute All (إلغاء الكتم)", style=discord.ButtonStyle.success, custom_id="unmute_all_btn")
    async def unmute_all(self, interaction: discord.Interaction, button: discord.ui.Button):
        # 1. التحقق من وجود المستخدم في غرفة صوتية
        if not interaction.user.voice:
            await interaction.response.send_message("❌ يجب أن تكون في غرفة صوتية لتنفيذ هذا الأمر.", ephemeral=True)
            return
        
        # 2. التحقق من أن المستخدم يمتلك رول المدير
        target_role = discord.utils.get(interaction.guild.roles, name=MUTE_ROLE_NAME)
        if not target_role or target_role not in interaction.user.roles:
            await interaction.response.send_message(f"❌ يجب أن تمتلك رول '{MUTE_ROLE_NAME}' لاستخدام هذا الزر.", ephemeral=True)
            return

        channel = interaction.user.voice.channel
        unmuted_count = 0

        # 3. إلغاء كتم جميع الأعضاء في الغرفة
        for member in channel.members:
            if not member.bot and member.voice.mute:
                try:
                    await member.edit(mute=False)
                    unmuted_count += 1
                except discord.Forbidden:
                    pass

        await interaction.response.send_message(f"✅ تم إلغاء كتم **{unmuted_count}** عضو في الغرفة.", ephemeral=True)

# --- عند تشغيل البوت ---
@bot.event
async def on_ready():
    bot.add_view(MuteControlView())
    print(f'✅ تم تسجيل الدخول بنجاح باسم {bot.user}')

# --- أمر إرسال لوحة التحكم ---
@bot.command(name='setup_mute')
@commands.has_permissions(administrator=True)
async def setup_mute(ctx):
    embed = discord.Embed(
        title="🎮 لوحة تحكم أمونق ميوت",
        description=f"فقط من يمتلك رول **{MUTE_ROLE_NAME}** يمكنه استخدام هذه الأزرار. عند الضغط على Mute All، سيتم كتم جميع من في غرفتك (ما عداك).",
        color=discord.Color.blue()
    )
    await ctx.send(embed=embed, view=MuteControlView())

# --- سيرفر ويب وهمي لإبقاء Render مستيقظاً ---
async def handle(request):
    return web.Response(text="Bot is running!")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv('PORT', 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    print(f"🌐 Web server started on port {port}")

# --- تشغيل البوت والسيرفر معاً ---
async def main():
    await start_web_server()
    
    while True:
        try:
            print("⏳ جاري محاولة الاتصال بديسكورد...")
            await bot.start(TOKEN)
        except discord.errors.HTTPException as e:
            if e.status == 429:
                print("⚠️ تحذير: تم حظر الـ IP مؤقتاً من قبل ديسكورد (خطأ 429).")
                print("⏳ سننتظر 10 دقائق قبل محاولة الاتصال مرة أخرى...")
                await asyncio.sleep(600)
            else:
                print(f"❌ خطأ HTTP غير متوقع: {e}")
                await asyncio.sleep(60)
        except Exception as e:
            print(f"❌ خطأ غير متوقع: {e}")
            await asyncio.sleep(60)

if __name__ == '__main__':
    asyncio.run(main())
