import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import discord
from discord.ext import commands

from cogs.music import MusicPlayer, YTDL, YTDLSource, is_playlist_url, is_url
from main import MusicBot


class MusicHelpersTest(unittest.TestCase):
    def test_format_duration(self):
        self.assertEqual(MusicPlayer.format_duration(61), "01m 01s")
        self.assertEqual(MusicPlayer.format_duration(3661), "1h 01m 01s")
        self.assertEqual(MusicPlayer.format_duration(None), "unknown duration")

    def test_url_detection(self):
        self.assertTrue(is_url("https://www.youtube.com/watch?v=abc"))
        self.assertFalse(is_url("tavern ambience music"))
        self.assertFalse(is_url("javascript:alert(1)"))
        self.assertTrue(is_playlist_url("https://www.youtube.com/playlist?list=PL123"))
        self.assertTrue(is_playlist_url("https://music.youtube.com/playlist?list=PL123"))
        self.assertFalse(is_playlist_url("https://www.youtube.com/watch?v=abc&list=PL123"))
        self.assertFalse(is_playlist_url("https://www.youtube.com/watch?v=abc"))


class YTDLSourceTest(unittest.IsolatedAsyncioTestCase):
    async def test_load_metadata_uses_first_valid_entry(self):
        requester = SimpleNamespace(mention="@player")
        source = YTDLSource(requester)
        result = {
            "entries": [
                None,
                {
                    "title": "Tavern",
                    "webpage_url": "https://example.test/video",
                    "duration": 123,
                    "url": "https://stream.test/old",
                },
            ]
        }
        with patch.object(YTDL, "extract", AsyncMock(return_value=result)):
            await source.load_metadata("query")
        self.assertEqual(source.title, "Tavern")
        self.assertEqual(source.duration, "02m 03s")
        self.assertEqual(source.webpage_url, "https://example.test/video")

    async def test_refresh_stream_url_reextracts_at_playback_time(self):
        requester = SimpleNamespace(mention="@player")
        source = YTDLSource(
            requester,
            webpage_url="https://example.test/video",
            title="Old title",
            duration=1,
        )
        result = {
            "title": "Current title",
            "duration": 125,
            "url": "https://stream.test/fresh",
        }
        with patch.object(YTDL, "extract", AsyncMock(return_value=result)) as extract:
            stream_url = await source.refresh_stream_url()
        extract.assert_awaited_once_with("https://example.test/video")
        self.assertEqual(stream_url, "https://stream.test/fresh")
        self.assertEqual(source.title, "Current title")
        self.assertEqual(source.duration, "02m 05s")

    def test_ytdl_source_from_data_notify_flag(self):
        requester = SimpleNamespace(mention="@player")
        data = {"title": "Sample Song", "webpage_url": "https://example.com/song", "duration": 180}
        source_normal = YTDLSource.from_data(requester, data)
        self.assertTrue(source_normal.notify)

        source_silent = YTDLSource.from_data(requester, data, notify=False)
        self.assertFalse(source_silent.notify)


class PlaylistEmbedTest(unittest.TestCase):
    def setUp(self):
        from cogs.music import Music
        self.bot = SimpleNamespace(user=SimpleNamespace(display_avatar=SimpleNamespace(url="https://bot.test/avatar.png")))
        self.cog = Music(self.bot)
        self.ctx = SimpleNamespace(
            author=SimpleNamespace(
                display_name="Tester",
                display_avatar=SimpleNamespace(url="https://user.test/avatar.png"),
            )
        )

    def test_build_playlist_embeds_small(self):
        sources = [
            YTDLSource(self.ctx.author, webpage_url=f"https://yt.test/{i}", title=f"Track {i}", duration=120)
            for i in range(1, 6)
        ]
        embeds = self.cog.build_playlist_embeds(
            self.ctx,
            playlist_title="Small Mix",
            playlist_url="https://yt.test/playlist?list=123",
            sources=sources,
            total_found=5,
        )
        self.assertEqual(len(embeds), 1)
        self.assertIn("Small Mix", embeds[0].description)
        self.assertIn("Track 1", embeds[0].description)
        self.assertIn("Track 5", embeds[0].description)
        self.assertIn("Chế độ phát yên tĩnh", embeds[0].description)
        self.assertEqual(embeds[0].author.name, "Playlist Added (5 tracks) 🎶")

    def test_build_playlist_embeds_large_respects_discord_limits(self):
        sources = [
            YTDLSource(self.ctx.author, webpage_url=f"https://yt.test/{i}", title=f"Long Track Title Number {i} With Extra Details", duration=215)
            for i in range(1, 101)
        ]
        embeds = self.cog.build_playlist_embeds(
            self.ctx,
            playlist_title="Huge 100 Track Playlist",
            playlist_url="https://yt.test/playlist?list=large",
            sources=sources,
            total_found=100,
        )
        self.assertGreaterEqual(len(embeds), 1)
        self.assertLessEqual(len(embeds), 10)

        total_chars = 0
        for embed in embeds:
            desc = embed.description or ""
            self.assertLessEqual(len(desc), 4096)
            total_chars += len(desc)
            if embed.title:
                total_chars += len(embed.title)
            if embed.author and embed.author.name:
                total_chars += len(embed.author.name)
            if embed.footer and embed.footer.text:
                total_chars += len(embed.footer.text)

        self.assertLessEqual(total_chars, 6000)
        self.assertIn("Track Title Number 1", embeds[0].description)


class BotSetupTest(unittest.IsolatedAsyncioTestCase):
    async def test_music_cog_registers_all_slash_commands(self):
        bot = MusicBot(
            command_prefix=commands.when_mentioned,
            intents=discord.Intents.default(),
        )
        try:
            await bot.load_extension("cogs.music")
            self.assertEqual(
                {command.name for command in bot.tree.get_commands()},
                {"join", "leave", "loop", "np", "pause", "play", "playlist", "queue", "resume", "skip"},
            )
        finally:
            await bot.close()


if __name__ == "__main__":
    unittest.main()
