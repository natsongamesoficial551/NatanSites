import discord
from discord.ext import commands
from discord import app_commands
import logging, asyncio
from config import *

logger = logging.getLogger(__name__)


# ── View do canal de ticket ──────────────────────────────────────────

class FecharTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="🔒  Fechar Ticket",
        style=discord.ButtonStyle.danger,
        custom_id="fechar_ticket_btn"
    )
    async def fechar_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Verifica se é admin
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Apenas administradores podem fechar tickets.", ephemeral=True)
            return

        await interaction.response.send_message("🔒 Fechando ticket em 5 segundos...")
        await asyncio.sleep(5)

        # Log antes de deletar
        canal_log = interaction.guild.get_channel(CH_LOGS)
        if canal_log:
            embed = discord.Embed(
                title="📋 Log — Ticket Fechado",
                description=(
                    f"**Canal:** {interaction.channel.name}\n"
                    f"**Fechado por:** {interaction.user.mention}"
                ),
                color=COR_ERRO
            )
            embed.timestamp = discord.utils.utcnow()
            await canal_log.send(embed=embed)

        try:
            await interaction.channel.delete(reason=f"Ticket fechado por {interaction.user.display_name}")
        except Exception as e:
            logger.error(f"Erro ao fechar ticket: {e}")


# ── View do canal de suporte (botão "Chamar Suporte") ────────────────

class SuporteView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="📩  Chamar Suporte",
        style=discord.ButtonStyle.primary,
        custom_id="chamar_suporte_btn"
    )
    async def chamar_suporte(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        user = interaction.user

        # Verifica se usuário já tem ticket aberto
        ticket_nome = f"ticket-{user.name.lower().replace(' ', '-')}"
        canal_existente = discord.utils.get(guild.channels, name=ticket_nome)
        if canal_existente:
            await interaction.response.send_message(
                f"⚠️ Você já tem um ticket aberto: {canal_existente.mention}", ephemeral=True
            )
            return

        await interaction.response.send_message("✅ Criando seu ticket...", ephemeral=True)

        # Permissões do canal de ticket
        categoria = guild.get_channel(CAT_SUPORTE)
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: discord.PermissionOverwrite(
                view_channel=True, send_messages=True, read_message_history=True
            ),
        }
        # Adiciona permissão para admins
        for role in guild.roles:
            if role.permissions.administrator:
                overwrites[role] = discord.PermissionOverwrite(
                    view_channel=True, send_messages=True, read_message_history=True
                )

        try:
            ticket_canal = await guild.create_text_channel(
                name=ticket_nome,
                category=categoria,
                overwrites=overwrites,
                reason=f"Ticket aberto por {user.display_name}"
            )
        except Exception as e:
            logger.error(f"Erro ao criar canal de ticket: {e}")
            return

        # Envia mensagem inicial no ticket
        embed = discord.Embed(
            title="🎫  Ticket de Suporte",
            description=(
                f"Olá, {user.mention}! 👋\n\n"
                "Seja bem-vindo ao seu ticket de suporte!\n"
                "Descreva sua dúvida ou problema com detalhes e aguarde o atendimento.\n\n"
                "⏱️ Um administrador irá atendê-lo em breve.\n\n"
                "*Quando o atendimento for concluído, o administrador fechará este ticket.*"
            ),
            color=COR_SUPORTE
        )
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.set_footer(text="NatanDEV | Suporte Técnico")
        embed.timestamp = discord.utils.utcnow()

        view = FecharTicketView()
        await ticket_canal.send(content=f"{user.mention}", embed=embed, view=view)

        # Log
        canal_log = guild.get_channel(CH_LOGS)
        if canal_log:
            log = discord.Embed(
                title="📋 Log — Ticket Aberto",
                description=f"**Usuário:** {user.mention}\n**Canal:** {ticket_canal.mention}",
                color=COR_SUPORTE
            )
            log.timestamp = discord.utils.utcnow()
            await canal_log.send(embed=log)


# ── Cog Principal ────────────────────────────────────────────────────

class Suporte(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Registra views persistentes para sobreviver a reinicializações
        bot.add_view(SuporteView())
        bot.add_view(FecharTicketView())

    async def enviar_suporte(self, guild: discord.Guild):
        """Apaga mensagem antiga do bot e envia embed fixo de suporte"""
        canal = guild.get_channel(CH_SUPORTE)
        if not canal:
            return

        # Limpa mensagens antigas do bot
        try:
            async for msg in canal.history(limit=20):
                if msg.author == self.bot.user:
                    await msg.delete()
                    await asyncio.sleep(0.3)
        except Exception as e:
            logger.error(f"Erro ao limpar canal suporte: {e}")

        embed = discord.Embed(
            title="🛠️  Central de Suporte — NatanDEV",
            description=(
                "Precisa de ajuda? Nosso time está pronto para te atender!\n\n"
                "**Clique no botão abaixo para abrir um ticket de suporte.**\n\n"
                "📌 *Descreva bem sua dúvida ou problema ao abrir o ticket.*\n"
                "⏱️ *Respondemos o mais rápido possível.*"
            ),
            color=COR_SUPORTE
        )
        embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
        embed.add_field(
            name="📋  Como funciona?",
            value=(
                "1️⃣ Clique em **📩 Chamar Suporte**\n"
                "2️⃣ Um canal privado será criado só para você\n"
                "3️⃣ Descreva sua necessidade\n"
                "4️⃣ Aguarde o atendimento do administrador"
            ),
            inline=False
        )
        embed.set_footer(text="NatanDEV | Serviço de Sites")
        embed.timestamp = discord.utils.utcnow()

        view = SuporteView()
        await canal.send(embed=embed, view=view)
        logger.info("✅ Embed de suporte enviado.")

    async def auto_setup(self, guild: discord.Guild):
        await self.enviar_suporte(guild)

    @app_commands.command(name="setup-suporte", description="[ADM] Reenvia o embed de suporte com botão.")
    @app_commands.checks.has_permissions(administrator=True)
    async def setup_suporte(self, interaction: discord.Interaction):
        if interaction.channel_id != CH_CONTROLE:
            await interaction.response.send_message(f"❌ Use no canal <#{CH_CONTROLE}>.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)
        await self.enviar_suporte(interaction.guild)
        await interaction.followup.send("✅ Embed de suporte atualizado!", ephemeral=True)


async def setup(bot):
    await bot.add_cog(Suporte(bot))
