"""Run the standalone Discord music bot."""

import logging
import os
import socket
import sys
from pathlib import Path

import discord
from discord.ext import commands
from dotenv import load_dotenv


LOGGER = logging.getLogger(__name__)


def acquire_single_instance_lock(port=49200):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind(("127.0.0.1", port))
        return s
    except OSError:
        return None


class MusicBot(commands.Bot):
    async def setup_hook(self):
        await self.load_extension("cogs.music")
        guild_id = os.getenv("GUILD_ID")
        if guild_id:
            guild = discord.Object(id=int(guild_id))
            self.tree.copy_global_to(guild=guild)
            synced = await self.tree.sync(guild=guild)
            LOGGER.info("Synced %s commands to guild %s", len(synced), guild_id)
        else:
            synced = await self.tree.sync()
            LOGGER.info("Synced %s global commands", len(synced))

    async def on_ready(self):
        LOGGER.info("Logged in as %s", self.user)
        # Tu dong dong bo ngay lap tuc len cac server bot dang tham gia de lenh xuat hien ngay
        for guild in self.guilds:
            try:
                self.tree.copy_global_to(guild=guild)
                synced = await self.tree.sync(guild=guild)
                LOGGER.info("Auto-synced %s commands to server: '%s' (%s)", len(synced), guild.name, guild.id)
            except Exception as exc:
                LOGGER.warning("Could not sync commands to guild %s: %s", guild.id, exc)


def main():
    lock = acquire_single_instance_lock()
    if not lock:
        print("\n" + "=" * 65)
        print("[CANH BAO] Bot da dang chay trong mot cua so khac tren may!")
        print("Vui long tat cua so cu truoc khi mo cua so moi de tranh xung dot.")
        print("=" * 65 + "\n")
        sys.exit(1)

    load_dotenv(Path(__file__).with_name(".env"))
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        raise RuntimeError("DISCORD_TOKEN is required; see .env.example")

    logging.basicConfig(level=logging.INFO)
    intents = discord.Intents.default()
    bot = MusicBot(command_prefix=commands.when_mentioned, intents=intents)
    try:
        bot.run(token)
    finally:
        if lock:
            lock.close()


if __name__ == "__main__":
    main()
