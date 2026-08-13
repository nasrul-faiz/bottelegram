# (©)Codexbotz
# Recode by @mrismanaziz
# t.me/SharingUserbot & t.me/Lunatic0de

import asyncio
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from pyrogram import Client, filters
from pyrogram.errors import FloodWait
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from bot import Bot
from config import ADMINS, CHANNEL_ID, DISABLE_CHANNEL_BUTTON, LOGGER
from helper_func import encode


def save_generated_link(link: str, title: str = "Generated link", description: str = ""):
    try:
        path = Path(os.environ.get("BOT_LINKS_PATH", "generated_links.json"))
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            with path.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
        else:
            data = []
        if not isinstance(data, list):
            data = []
        record = {
            "id": (data[0]["id"] if data else 0) + 1,
            "title": title,
            "link": link,
            "description": description,
            "source": "telegram",
            "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
        }
        data.insert(0, record)
        with path.open("w", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2)
    except Exception as exc:
        LOGGER(__name__).warning(f"[SAVE_LINK] gagal menyimpan link: {exc}")


@Bot.on_message(
    filters.private
    & filters.user(ADMINS)
    & ~filters.command(
        [
            "start",
            "users",
            "broadcast",
            "ping",
            "uptime",
            "batch",
            "logs",
            "genlink",
            "delvar",
            "getvar",
            "setvar",
            "speedtest",
            "update",
            "stats",
            "vars",
            "id",
        ]
    )
)
async def channel_post(client: Client, message: Message):
    LOGGER(__name__).info(f"[CHANNEL_POST] Media received from {message.from_user.id}")
    
    # Check if CHANNEL_ID is configured
    if not client.db_channel:
        await message.reply_text("❌ <b>CHANNEL_ID belum dikonfigurasi!</b>\n\nBot memerlukan CHANNEL_ID yang valid untuk berfungsi.")
        return
    
    try:
        reply_text = await message.reply_text("<code>Tunggu Sebentar...</code>")
        LOGGER(__name__).info("[CHANNEL_POST] Reply sent successfully")
    except Exception as e:
        LOGGER(__name__).error(f"[CHANNEL_POST] Failed to send reply: {e}")
        return
    
    try:
        LOGGER(__name__).info(f"[CHANNEL_POST] Copying message to channel {client.db_channel.id}")
        post_message = await message.copy(
            chat_id=client.db_channel.id, disable_notification=True
        )
        LOGGER(__name__).info(f"[CHANNEL_POST] Message copied successfully, message_id: {post_message.id}")
    except FloodWait as e:
        LOGGER(__name__).warning(f"[CHANNEL_POST] FloodWait: sleeping for {e.value}s")
        await asyncio.sleep(e.value)
        try:
            post_message = await message.copy(
                chat_id=client.db_channel.id, disable_notification=True
            )
        except Exception as retry_error:
            LOGGER(__name__).error(f"[CHANNEL_POST] Retry failed: {retry_error}")
            await reply_text.edit_text(f"<b>❌ Error (Retry):</b> <code>{str(retry_error)}</code>")
            return
    except Exception as e:
        LOGGER(__name__).error(f"[CHANNEL_POST] Copy error: {e}", exc_info=True)
        await reply_text.edit_text(f"<b>❌ Error:</b> <code>{str(e)}</code>")
        return
    
    try:
        converted_id = post_message.id * abs(client.db_channel.id)
        string = f"get-{converted_id}"
        base64_string = await encode(string)
        link = f"https://t.me/{client.username}?start={base64_string}"
        LOGGER(__name__).info(f"[CHANNEL_POST] Link generated: {link}")

        reply_markup = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "🔁 Share Link", url=f"https://telegram.me/share/url?url={link}"
                    )
                ]
            ]
        )

        save_generated_link(link=link, title="Telegram generated link", description="Link dibuat otomatis dari kiriman media")
        await reply_text.edit_text(
            f"<b>Link Sharing File Berhasil Di Buat :</b>\n\n{link}",
            reply_markup=reply_markup,
        )
        LOGGER(__name__).info("[CHANNEL_POST] Response sent to user")
    except Exception as e:
        LOGGER(__name__).error(f"[CHANNEL_POST] Edit response error: {e}", exc_info=True)
        await reply_text.edit_text(f"<b>❌ Error saat membuat link:</b> <code>{str(e)}</code>")

    if not DISABLE_CHANNEL_BUTTON:
        try:
            await post_message.edit_reply_markup(reply_markup)
        except FloodWait as e:
            await asyncio.sleep(e.value)
            await post_message.edit_reply_markup(reply_markup)
        except Exception:
            pass


@Bot.on_message(filters.channel & filters.incoming & filters.chat(CHANNEL_ID))
async def new_post(client: Client, message: Message):

    if DISABLE_CHANNEL_BUTTON:
        return

    converted_id = message.id * abs(client.db_channel.id)
    string = f"get-{converted_id}"
    base64_string = await encode(string)
    link = f"https://t.me/{client.username}?start={base64_string}"
    reply_markup = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🔁 Share Link", url=f"https://telegram.me/share/url?url={link}"
                )
            ]
        ]
    )
    try:
        await message.edit_reply_markup(reply_markup)
    except FloodWait as e:
        await asyncio.sleep(e.value)
        await message.edit_reply_markup(reply_markup)
    except Exception:
        pass
