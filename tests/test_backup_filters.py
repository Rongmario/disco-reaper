from datetime import date
from types import SimpleNamespace

import pytest

from src.core.backup_database import BackupDatabase
from src.core.configuration import BackupFilters
from src.core.exporter import DiscordExporter
from src.core.utils import load_media_exclude, snowflake_from_date


def _msg(author_id=1, bot=False, webhook_id=None, content=""):
    return SimpleNamespace(
        author=SimpleNamespace(id=author_id, bot=bot),
        webhook_id=webhook_id,
        content=content,
    )


def test_snowflake_from_date():
    assert snowflake_from_date(date(2015, 1, 1)) == 0
    sf = snowflake_from_date(date(2020, 1, 1))
    assert (sf >> 22) + 1420070400000 == 1577836800000


def test_is_filtered():
    exp = DiscordExporter(reader=None, filters=BackupFilters(
        exclude_users=[42], exclude_bots=True, exclude_patterns=[r"(?i)^!roll\b"]
    ))
    assert exp.is_filtered(_msg(author_id=42))
    assert exp.is_filtered(_msg(bot=True))
    assert exp.is_filtered(_msg(webhook_id=7))
    assert exp.is_filtered(_msg(content="!ROLL d20"))
    assert not exp.is_filtered(_msg(content="rolling along"))


def test_load_media_exclude(tmp_path):
    (tmp_path / "media_exclude.txt").write_text(
        "123456789\n# a comment line\nattachments/ABCDEF.png  # dupe meme\n\n", encoding="utf-8"
    )
    assert load_media_exclude(tmp_path) == {"123456789", "abcdef"}
    assert load_media_exclude(tmp_path / "missing") == set()


@pytest.mark.asyncio
async def test_cutoff_moves_start_point():
    calls = []

    class Reader:
        async def get_channel(self, channel_id):
            return SimpleNamespace(name="general")

        async def fetch_message_history(self, channel_id, after_id=None):
            calls.append(after_id)
            return
            yield

    cutoff = date(2020, 1, 1)
    exp = DiscordExporter(Reader(), filters=BackupFilters(after_date=cutoff))
    await exp.export_channel_messages(1)
    assert calls == [snowflake_from_date(cutoff)]


@pytest.mark.asyncio
async def test_links_mode_and_exclusion_skip_download():
    async def save_method(path):
        raise AssertionError("links mode must not download")

    exp = DiscordExporter(reader=None, filters=BackupFilters(media_mode="links"))
    exp.media_exclude = {"2"}
    kept = await exp._process_media(1, "https://cdn/a.png", "a.png", size=5, save_method=save_method)
    assert kept["local_hash"] is None and kept["url"] == "https://cdn/a.png"
    assert await exp._process_media(2, "https://cdn/b.png", "b.png", save_method=save_method) is None


@pytest.mark.asyncio
async def test_download_pending_media(tmp_path):
    class Reader:
        async def download_attachment_urls(self, urls):
            return {u: b"image-bytes" for u in urls if "gone" not in u}

    exp = DiscordExporter(Reader(), base_dir=tmp_path, filters=BackupFilters())
    exp.export_path = tmp_path
    exp.attachments_path = tmp_path / "attachments"
    exp.attachments_path.mkdir()
    exp.db = BackupDatabase(tmp_path / "backup.db")
    exp.media_exclude = {"3"}
    exp.db.save_messages_batch([{
        "id": "10", "channel_id": "1", "author_id": "1", "content": "", "timestamp": "",
        "type": 0, "message_reference": None, "is_pinned": 0, "extra_data": None,
        "custom_display_name": None, "custom_avatar_url": None,
        "attachments": [
            {"id": str(i), "filename": f"{i}.png", "size": 0, "url": f"https://cdn/{name}.png",
             "content_type": "image/png", "local_hash": None}
            for i, name in ((1, "ok"), (2, "gone"), (3, "excluded"))
        ],
    }])

    assert await exp.download_pending_media() == 1
    assert [a["id"] for a in exp.db.get_pending_attachments()] == [2, 3]
    rows = exp.db.get_media_manifest()
    assert [bool(r["local_file"]) for r in rows] == [True, False, False]
