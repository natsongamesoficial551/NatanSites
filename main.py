import discord
from discord.ext import commands
import asyncio
import logging
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from config import *
from database import init_db

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ── Servidor web embutido (Render precisa de porta aberta) ────────────

class PingHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"NatanSites Bot - Online!")
    def log_message(self, format, *args):
        pass

def iniciar_servidor_web():
    servidor = HTTPServer(("0.0.0.0", 8080), PingHandler)
    logger.info("🌐 Servidor web interno iniciado na porta 8080")
    servidor.serve_forever()

async def autoping():
    """Ping a cada 10 minutos para manter o Render acordado."""
    import aiohttp
    await asyncio.sleep(60)
    while True:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("http://localhost:8080") as resp:
                    logger.info(f"🏓 Autoping OK — status {resp.status}")
        except Exception as e:
            logger.warning(f"⚠️ Autoping falhou: {e}")
        await asyncio.sleep(600)

# ── Bot ───────────────────────────────────────────────────────────────

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.guilds = True


class NatanBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # Inicia o banco de dados SQLite antes de qualquer coisa
        init_db()

        cogs = [
            "cogs.regras", "cogs.anuncios", "cogs.apresentacoes",
            "cogs.loja", "cogs.compras", "cogs.projetos",
            "cogs.suporte", "cogs.zoacao", "cogs.free", "cogs.logs",
        ]
        for cog in cogs:
            try:
                await self.load_extension(cog)
                logger.info(f"✅ Cog carregado: {cog}")
            except Exception as e:
                logger.error(f"❌ Erro ao carregar {cog}: {e}")

        await self.tree.sync()
        logger.info("✅ Slash commands sincronizados!")
        self.loop.create_task(autoping())

    async def on_ready(self):
        logger.info(f"🤖 NatanSites Bot online como {self.user} (ID: {self.user.id})")
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="NatanSites | Serviço de Sites"
            )
        )
        await self.auto_setup()

    async def auto_setup(self):
        await asyncio.sleep(2)
        guild = self.get_guild(GUILD_ID)
        if not guild:
            logger.error("❌ Guild não encontrada!")
            return
        logger.info("🔄 Iniciando auto-setup das mensagens fixas...")
        for name, cog_obj in self.cogs.items():
            if hasattr(cog_obj, "auto_setup"):
                try:
                    await cog_obj.auto_setup(guild)
                except Exception as e:
                    logger.error(f"Erro no auto_setup de {name}: {e}")


bot = NatanBot()

if __name__ == "__main__":
    t = threading.Thread(target=iniciar_servidor_web, daemon=True)
    t.start()
    bot.run(BOT_TOKEN)
