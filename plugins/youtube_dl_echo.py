#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# (c) Shrimadhav U K | X-Noid | @DC4_WARRIOR

# the logging things
import logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
import requests, urllib.parse, filetype, os, time, shutil, tldextract, asyncio, json, math
from PIL import Image
# the secret configuration specific things
if bool(os.environ.get("WEBHOOK", False)):
    from sample_config import Config
else:
    from config import Config
# the Strings used for this "thing"

from translation import Translation
logging.getLogger("pyrogram").setLevel(logging.WARNING)
from pyrogram import filters
from pyrogram import Client as Clinton
from database.add import add_user_to_database
from helper_funcs.display_progress import humanbytes
from helper_funcs.help_uploadbot import DownLoadFile
from helper_funcs.display_progress import progress_for_pyrogram, humanbytes, TimeFormatter
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import UserNotParticipant
from helper_funcs.ran_text import random_char
from plugins.timegap import check_time_gap

@Clinton.on_message(filters.private & filters.regex(pattern=".*https.*"))
async def echo(bot, update):
    if Config.UPDATE_CHANNEL:
        try:
            user = await bot.get_chat_member(Config.UPDATE_CHANNEL, update.chat.id)
            if user.status == "kicked":
              await bot.edit_message_text(text=Translation.BANNED_USER_TEXT, message_id=fmsg.message_id)
              return
        except UserNotParticipant:
            await bot.edit_message_text(chat_id=update.chat.id, text=Translation.FORCE_SUBSCRIBE_TEXT, message_id=fmsg.message_id, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(text="😎 Join Channel 😎", url=f"https://telegram.me/{Config.UPDATE_CHANNEL}")]]))
            return
        except Exception:
            await bot.edit_message_text(chat_id=update.chat.id, text=Translation.SOMETHING_WRONG, message_id=fmsg.message_id)
            return
        if str(update.from_user.id) in Config.ADL_BOT_RQ:
            current_time = time.time()
            previous_time = Config.ADL_BOT_RQ[str(update.from_user.id)]
            process_max_timeout = round(Config.PROCESS_MAX_TIMEOUT/60)
            present_time = round(Config.PROCESS_MAX_TIMEOUT-(current_time - previous_time))
            Config.ADL_BOT_RQ[str(update.from_user.id)] = time.time()
            if round(current_time - previous_time) < Config.PROCESS_MAX_TIMEOUT:
                await bot.edit_message_text(chat_id=update.chat.id, text=Translation.FREE_USER_LIMIT_Q_SZE.format(process_max_timeout, present_time), disable_web_page_preview=True, parse_mode="html", message_id=fmsg.message_id)
                return
        else:
            Config.ADL_BOT_RQ[str(update.from_user.id)] = time.time()
    await add_user_to_database(bot, update)
    logger.info(update.from_user)
    url = update.text
    youtube_dl_username = None
    youtube_dl_password = None
    file_name = None
    print(url)
    if "|" in url:
        url_parts = url.split("|")
        if len(url_parts) == 2:
            url = url_parts[0]
            file_name = url_parts[1]
        elif len(url_parts) == 4:
            url = url_parts[0]
            file_name = url_parts[1]
            youtube_dl_username = url_parts[2]
            youtube_dl_password = url_parts[3]
        else:
            for entity in update.entities:
                if entity.type == "text_link":
                    url = entity.url
                elif entity.type == "url":
                    o = entity.offset
                    l = entity.length
                    url = url[o:o + l]
        if url is not None:
            url = url.strip()
        if file_name is not None:
            file_name = file_name.strip()
        # https://stackoverflow.com/a/761825/4723940
        if youtube_dl_username is not None:
            youtube_dl_username = youtube_dl_username.strip()
        if youtube_dl_password is not None:
            youtube_dl_password = youtube_dl_password.strip()
        logger.info(url)
        logger.info(file_name)
    else:
        for entity in update.entities:
            if entity.type == "text_link":
                url = entity.url
            elif entity.type == "url":
                o = entity.offset
                l = entity.length
                url = url[o:o + l]
    if Config.HTTP_PROXY != "":
        command_to_exec = [
            "yt-dlp",
            "--no-warnings",
            "--youtube-skip-dash-manifest",
            "-j",
            url,
            "--proxy", Config.HTTP_PROXY
        ]
    else:
        command_to_exec = [
            "yt-dlp",
            "--no-warnings",
            "--youtube-skip-dash-manifest",
            "-j",
            url
        ]
    if youtube_dl_username is not None:
        command_to_exec.append("--username")
        command_to_exec.append(youtube_dl_username)
    if youtube_dl_password is not None:
        command_to_exec.append("--password")
        command_to_exec.append(youtube_dl_password)
    logger.info(command_to_exec)
    chk = await bot.send_message(
            chat_id=update.chat.id,
            text=f'Processing Your Link ⌛',
            disable_web_page_preview=True,
            reply_to_message_id=update.message_id
          )
    process = await asyncio.create_subprocess_exec(
        *command_to_exec,
        # stdout must a pipe to be accessible as process.stdout
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    # Wait for the subprocess to finish
    stdout, stderr = await process.communicate()
    e_response = stderr.decode().strip()
    logger.info(e_response)
    t_response = stdout.decode().strip()
    #logger.info(t_response)
    # https://github.com/rg3/youtube-dl/issues/2630#issuecomment-38635239
    if e_response and "nonnumeric port" not in e_response:
        # logger.warn("Status : FAIL", exc.returncode, exc.output)
        error_message = e_response.replace("please report this issue on https://yt-dl.org/bug . Make sure you are using the latest version; see  https://yt-dl.org/update  on how to update. Be sure to call youtube-dl with the --verbose flag and include its complete output.", "")
        if "This video is only available for registered users." in error_message:
            error_message += Translation.SET_CUSTOM_USERNAME_PASSWORD
        await chk.delete()
        time.sleep(1)
        await bot.send_message(
            chat_id=update.chat.id,
            text=Translation.NO_VOID_FORMAT_FOUND.format(str(error_message)),
            reply_to_message_id=update.message_id,
            parse_mode="html",
            disable_web_page_preview=True
        )
        return False
    if t_response:
        # logger.info(t_response)
        x_reponse = t_response
        if "\n" in x_reponse:
            x_reponse, _ = x_reponse.split("\n")
        response_json = json.loads(x_reponse)
        randem = random_char(5)
        save_ytdl_json_path = Config.DOWNLOAD_LOCATION + \
            "/" + str(update.from_user.id) + f'{randem}' + ".json"
        with open(save_ytdl_json_path, "w", encoding="utf8") as outfile:
            json.dump(response_json, outfile, ensure_ascii=False)
        # logger.info(response_json)
        inline_keyboard = []
        duration = None
        if "duration" in response_json:
            duration = response_json["duration"]
        if "formats" in response_json:
            for formats in response_json["formats"]:
                format_id = formats.get("format_id")
                format_string = formats.get("format_note")
                if format_string is None:
                    format_string = formats.get("format")
                format_ext = formats.get("ext")
                approx_file_size = ""
                if "filesize" in formats:
                    approx_file_size = humanbytes(formats["filesize"])
                cb_string_video = "{}|{}|{}|{}".format(
                    "video", format_id, format_ext, randem)
                cb_string_file = "{}|{}|{}|{}".format(
                    "file", format_id, format_ext, randem)
                if format_string is not None and not "audio only" in format_string:
                    ikeyboard = [InlineKeyboardButton("🎥 Video", callback_data="(cb_string_video).encode("UTF-8")||{format_ext}||{format_string}||{approx_file_size}"), InlineKeyboardButton("Document", callback_data="(cb_string_file).encode("UTF-8")||{format_ext}||{format_string}||{approx_file_size}")]
                    """if duration is not None:
                        cb_string_video_message = "{}|{}|{}|{}|{}".format(
                            "vm", format_id, format_ext, ran, randem)
                        ikeyboard.append(
                            InlineKeyboardButton(
                                "VM",
                                callback_data=(
                                    cb_string_video_message).encode("UTF-8")
                            )
                        )"""
                else:
                    # special weird case :\
                    ikeyboard = [
                        InlineKeyboardButton(
                            "🎥 Video [" +
                            "] ( " +
                            approx_file_size + " )",
                            callback_data=(cb_string_video).encode("UTF-8")
                        ),
                        InlineKeyboardButton(
                            "🗃️ File [" +
                            "] ( " +
                            approx_file_size + " )",
                            callback_data=(cb_string_file).encode("UTF-8")
                        )
                    ]
                inline_keyboard.append(ikeyboard)
            if duration is not None:
                cb_string_64 = "{}|{}|{}|{}".format("audio", "64k", "mp3", randem)
                cb_string_128 = "{}|{}|{}|{}".format("audio", "128k", "mp3", randem)
                cb_string = "{}|{}|{}|{}".format("audio", "320k", "mp3", randem)
                inline_keyboard.append([
                    InlineKeyboardButton(
                        "🎸 Mp3 " + "(" + "64 kbps" + ")", callback_data=cb_string_64.encode("UTF-8")),
                    InlineKeyboardButton(
                        "🎸 Mp3 " + "(" + "128 kbps" + ")", callback_data=cb_string_128.encode("UTF-8"))
                ])
                inline_keyboard.append([
                    InlineKeyboardButton(
                        "🎸 Mp3 " + "(" + "320 kbps" + ")", callback_data=cb_string.encode("UTF-8"))
                ])
                inline_keyboard.append([                 
                    InlineKeyboardButton(
                        "♨️ CLOSE", callback_data='close')               
                ])
        else:
            format_id = response_json["format_id"]
            format_ext = response_json["ext"]
            cb_string_file = "{}|{}|{}|{}".format(
                "file", format_id, format_ext, randem)
            cb_string_video = "{}|{}|{}|{}".format(
                "video", format_id, format_ext, randem)
            inline_keyboard.append([
                InlineKeyboardButton(
                    "SVideo",
                    callback_data=(cb_string_video).encode("UTF-8")
                ),
                InlineKeyboardButton(
                    "DFile",
                    callback_data=(cb_string_file).encode("UTF-8")
                )
            ])
            cb_string_file = "{}={}={}".format(
                "file", format_id, format_ext)
            cb_string_video = "{}={}={}".format(
                "video", format_id, format_ext)
            inline_keyboard.append([
                InlineKeyboardButton(
                    "video",
                    callback_data=(cb_string_video).encode("UTF-8")
                ),
                InlineKeyboardButton(
                    "file",
                    callback_data=(cb_string_file).encode("UTF-8")
                )
            ])
        reply_markup = InlineKeyboardMarkup(inline_keyboard)
        await chk.delete(True)
        await bot.send_message(
            chat_id=update.chat.id,
            text=Translation.FORMAT_SELECTION + "\n" + Translation.SET_CUSTOM_USERNAME_PASSWORD,
            reply_markup=reply_markup,
            parse_mode="html",
            reply_to_message_id=update.message_id
        )
    else:
        # fallback for nonnumeric port a.k.a seedbox.io
        inline_keyboard = []
        cb_string_file = "{}={}={}".format(
            "file", "LFO", "NONE")
        cb_string_video = "{}={}={}".format(
            "video", "OFL", "ENON")
        inline_keyboard.append([
            InlineKeyboardButton(
                "SVideo",
                callback_data=(cb_string_video).encode("UTF-8")
            ),
            InlineKeyboardButton(
                "DFile",
                callback_data=(cb_string_file).encode("UTF-8")
            )
        ])
        reply_markup = InlineKeyboardMarkup(inline_keyboard)
        await chk.delete(True)
        await bot.send_message(
            chat_id=update.chat.id,
            text=Translation.FORMAT_SELECTION,
            reply_markup=reply_markup,
            parse_mode="html",
            reply_to_message_id=update.message_id
        )
