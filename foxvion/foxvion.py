import asyncio
from ctypes import Union
import datetime
from typing import Dict, List, Optional
import typing
import discord
from discord.ext import commands
from discord import app_commands, Member
import re
import math
from discord.utils import get
from discord import SelectOption, ui
import json
import random
from typing import Union
import os
import requests
from PIL import Image, ImageDraw, ImageFont
import imghdr
from discord.ui import View, select, Button, Modal, TextInput
from discord import Embed
import deepl
from enum import Enum
import aiohttp
from discord import Embed, ButtonStyle
from discord.ui import View, Button
import functools
from functools import partial
import psutil
from bs4 import BeautifulSoup
from io import BytesIO
from datetime import datetime, timedelta
import urllib
import string
import pytz
import sys
from dateutil.parser import parse

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())
bot.remove_command("help")

bot.session = aiohttp.ClientSession()


@bot.event
async def on_ready():
    print("BOTオンライン")
    try:
        synced = await bot.tree.sync()
        print(f"コマンドの同期が完了しました 数{len(synced)}個")
    except Exception as e:
        print(f"エラー: {e}")

    # ボットのアクティビティを設定
    activity = discord.Activity(type=discord.ActivityType.listening, name="/help｜Lem0n&Koala")
    await bot.change_presence(status=discord.Status.idle, activity=activity)

# ----------------------------------------------------------------------------------------
#一般コマンド
# 計算機
@bot.tree.command(name="calculation", description="計算ができます")
async def calculation(interaction: discord.Interaction, formula: str):
    """
    :param formula: 数式を入力してください　また使用できる記号は -+*/()  です
    """
    try:
        # 式を評価して計算する
        result = eval(formula)
        # 結果を整形する
        formatted_result = "{:,}".format(result)
        # レスポンスを作成する
        response = discord.Embed(
            title="計算機",
            description=f"{formula}の計算結果\n```\n{formatted_result}```",
            color=0xFFD700,
        )
        response.set_thumbnail(url="https://cdn.discordapp.com/attachments/1101747131519348856/1104523987637256252/9501f9ea8c339cda.png")
        # メッセージを返信する
        await interaction.response.send_message(embed=response, ephemeral=False)
    except Exception:
        # エラーが発生した場合はエラーメッセージを返す
        response = discord.Embed(
            title="エラー", description="計算中にエラーが起きました", color=0xFF0000
        )
        response.set_thumbnail(url="https://cdn.discordapp.com/attachments/1101747131519348856/1104523987637256252/9501f9ea8c339cda.png")
        # メッセージを返信する
        await interaction.response.send_message(embed=response, ephemeral=True)

# ----------------------------------------------------------------------------------------
# 絵文字
COLORS = {
    (0, 0, 0): "⬛",
    (0, 0, 255): "🟦",
    (255, 0, 0): "🟥",
    (255, 255, 0): "🟨",
    (190, 100, 80): "🟫",
    (255, 165, 0): "🟧",
    (160, 140, 210): "🟪",
    (255, 255, 255): "⬜",
    (0, 255, 0): "🟩",
}


def euclidean_distance(c1, c2):
    r1, g1, b1 = c1
    r2, g2, b2 = c2
    d = ((r2 - r1) ** 2 + (g2 - g1) ** 2 + (b2 - b1) ** 2) ** 0.5

    return d


def find_closest_emoji(color):
    c = sorted(list(COLORS), key=lambda k: euclidean_distance(color, k))
    return COLORS[c[0]]


def emojify_image(img, size=14):
    WIDTH, HEIGHT = (size, size)
    small_img = img.resize((WIDTH, HEIGHT), Image.NEAREST)

    emoji = ""
    small_img = small_img.load()
    for y in range(HEIGHT):
        for x in range(WIDTH):
            emoji += find_closest_emoji(small_img[x, y])
        emoji += "\n"
    return emoji


@bot.tree.command(name="pictogram", description="指定された画像を絵文字に変換します")
async def pictogram(interaction: discord.Interaction, image: str, size: int = 14):
    """
    :param image: 絵文字に変換したい画像のURLを入力してください
    :param size: 画像のサイズを指定してください1~43
    """
    try:
        response = requests.get(image)
        response.raise_for_status()
        content_type = response.headers["Content-Type"]
        if "image" not in content_type:
            raise ValueError
    except (requests.exceptions.RequestException, ValueError):
        embed = discord.Embed(
            title="エラー",
            description="`image`の引用が不適切です\n`image`には画像のURLを入力してください",
            color=0xFF0000,
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    if size > 43:
        embed = discord.Embed(
            title="エラー",
            description="`size`の引用が不適切です\n`size`は1~43の数字を指定してください",
            color=0xFF0000,
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    def get_emojified_image(image):
        r = requests.get(image, stream=True)
        image = Image.open(r.raw).convert("RGB")
        res = emojify_image(image, size)

        if size > 14:
            res = f"```{res}```"
        return res

    result = await bot.loop.run_in_executor(None, get_emojified_image, image)
    await interaction.response.send_message(result)

# ----------------------------------------------------------------------------------------
# 翻訳コマンド
DEEPL_API_KEY = "93dac26d-bd6a-e492-946d-9cc04ad37978:fx"


class Language(Enum):
    ENGLISH = "EN"
    JAPANESE = "JA"
    PORTUGUESE = "PT"
    CHINESE = "ZH"
    KOREAN = "KO"
    RUSSIAN = "RU"
    GERMAN = "DE"
    SPANISH = "ES"

    def __str__(self):
        return f"{self.name} ({self.value})"

    @classmethod
    def from_name(cls, name: str):
        for lang in cls:
            if lang.name.lower() == name.lower() or lang.value.lower() == name.lower():
                return lang
        raise ValueError(f"{name} is not a valid language")


@bot.tree.command(name="trans", description="メッセージを翻訳します")
async def trans(
    interaction: discord.Interaction,
    message: str,
    source_lang: Language,
    target_lang: Language,
):
    """
    :param message: 翻訳する内容を入力してください
    :param source_lang: 翻訳前の言語を選択してください
    :param target_lang: 翻訳先の言語を選択して下さい
    """
    try:
        source_lang = source_lang.value
        target_lang = target_lang.value
    except KeyError:
        return await interaction.response.send_message("言語が不正です。")

    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "auth_key": DEEPL_API_KEY,
        "text": message,
        "source_lang": source_lang,
        "target_lang": target_lang,
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "https://api-free.deepl.com/v2/translate", headers=headers, data=data
        ) as resp:
            if resp.status != 200:
                return await interaction.response.send_message(
                    f"翻訳エラーが発生しました (ステータスコード: {resp.status})"
                )
            result = await resp.json()
            translated_text = result.get("translations")[0].get("text")

            embed = discord.Embed(title="メッセージの翻訳｜translation", color=0xFFD700)
            embed.add_field(
                name="翻訳前のメッセージ｜before translation", value=message, inline=True
            )
            embed.add_field(
                name="翻訳前の言語｜Language before", value=source_lang, inline=True
            )
            embed.add_field(name="\n", value="\n", inline=False)
            embed.add_field(
                name="翻訳後のメッセージ｜after translation", value=translated_text, inline=True
            )
            embed.add_field(
                name="翻訳後の言語｜Language after ", value=target_lang, inline=True
            )
            embed.add_field(
                name="翻訳者｜Translated by ", value=interaction.user.mention, inline=False
            )

            await interaction.response.send_message(embed=embed)
            
# ----------------------------------------------------------------------------------------
# VALORANTsetting
class playerOptions(Enum):
    Laz = "Laz"
    Crow = "Crow"
    Dep = "Dep"
    SugarZ3ro = " SugarZ3ro"
    TENNN = "TENNN"
    Neth = "Neth"
    Meiy = "Meiy"
    Derialy = "Derialy"
    Bazz = "Bazz"
    Minty = "Minty"
    Fisker = "Fisker"
    Something = "Something"
    Vici = "Vici"
    Seoldam = "Seoldam"
    TenZ = "TenZ"
    Shroud = "Shroud"
    FNS = "FNS"
    Victor = "Victor"
    Yay = "Yay"
    Aspas = "Aspas"
    ScreaM = "ScreaM"
    Stax = "Stax"
    Rb = "Rb"
    BuZz = "BuZz"
    Jinggg = "Jinggg"


@bot.tree.command(
    name="valorant-setting", description="valoantのプロプレイヤーのデバイスや設定等を確認できます"
)
async def valorant_setting(interaction: discord.Interaction, player: playerOptions):
    """
    :param player: プレイヤーを選択できます
    """
    if player == playerOptions.Laz:
        embed = discord.Embed(title="VALORANT setting", color=0xFF0000)
        embed.add_field(
            name="ユーザー情報",
            value="player:Laz\nTwitter:[@lazvell](https://twitter.com/lazvell)",
        )
        embed.set_thumbnail(url="https://as2.ftcdn.net/v2/jpg/03/71/01/31/1000_F_371013119_o87usHtqx06jK5IQ3sywV3cMslyx34Hi.jpg")
        embed.add_field(
            name="デバイス",
            value="マウス:[GPROX SUPERLIGHT](https://onl.sc/H4Vrw5R)\nキーボード:[G913TKL](https://onl.sc/qAxCVzG)",
            inline=False,
        )
        embed.add_field(name="感度", value="DPI:800\nゲーム内感度:0.355", inline=False)
        embed.add_field(
            name="クロスヘア",
            value="```0;P;0;C;1;S;1;P;O;1;F;0;M;1;0t;1;0l;2;0v;2;0o;2;0a;1;0f;0;1b;0;A;C;7;H;0;D;1;Z;3;F;0;S;0;M;1;0t;3;0l;2;0o;0;0a;0.5;0f;0;1b;0;S;S;0.5;O;1```",
            inline=False,
        )
    elif player == playerOptions.Crow:
        embed = discord.Embed(title="VALORANT setting", color=0xFF0000)
        embed.add_field(
            name="ユーザー情報",
            value="player:Crow\nTwitter:[@no960fps](https://twitter.com/no960fps)",
        )
        embed.set_thumbnail(url="https://as2.ftcdn.net/v2/jpg/03/71/01/31/1000_F_371013119_o87usHtqx06jK5IQ3sywV3cMslyx34Hi.jpg")
        embed.add_field(
            name="デバイス",
            value="マウス:[ZYGEN Np-01g](https://www.vaxee.co/jp/product.php)\nキーボード:[G913TKL](https://onl.sc/qAxCVzG)",
            inline=False,
        )
        embed.add_field(name="感度", value="DPI:400\nゲーム内感度:0.447", inline=False)
        embed.add_field(
            name="クロスヘア",
            value="```0;S;1;P;O;1;F;0;0t;1;0l;1;0o;1;0a;1;0f;0;1b;0;S;C;0;S;0.5;O;1```",
            inline=False,
        )
    elif player == playerOptions.Dep:
        embed = discord.Embed(title="VALORANT setting", color=0xFF0000)
        embed.add_field(
            name="ユーザー情報",
            value="player:Dep\nTwitter:[@Dep_ow](https://twitter.com/Dep_ow)",
        )
        embed.set_thumbnail(url="https://as2.ftcdn.net/v2/jpg/03/71/01/31/1000_F_371013119_o87usHtqx06jK5IQ3sywV3cMslyx34Hi.jpg")
        embed.add_field(
            name="デバイス",
            value="マウス:[Viper V2 Pro](https://onl.sc/sG4b2sN)\nキーボード:[CORSAIR K100 RGB](https://onl.sc/U57KWUz)",
            inline=False,
        )
        embed.add_field(name="感度", value="DPI:400\nゲーム内感度:0.9", inline=False)
        embed.add_field(
            name="クロスヘア",
            value="```0;S;1;P;O;0.1;F;0;S;0;0t;1;0l;2;0o;1;0a;1;0f;0;1b;0```",
            inline=False,
        )
    elif player == playerOptions.SugarZ3ro:
        embed = discord.Embed(title="VALORANT setting", color=0xFF0000)
        embed.add_field(
            name="ユーザー情報",
            value="player:SugarZ3ro\nTwitter:[@SugarZ3roVL](https://twitter.com/SugarZ3roVL)",
        )
        embed.set_thumbnail(url="https://as2.ftcdn.net/v2/jpg/03/71/01/31/1000_F_371013119_o87usHtqx06jK5IQ3sywV3cMslyx34Hi.jpg")
        embed.add_field(
            name="デバイス",
            value="マウス:[GPROX SUPERLIGHT](https://onl.sc/WuQGX3P)\nキーボード:[G913TKL](https://onl.sc/qAxCVzG)",
            inline=False,
        )
        embed.add_field(name="感度", value="DPI:800\nゲーム内感度:0.25", inline=False)
        embed.add_field(
            name="クロスヘア",
            value="```0;P;C;1;O;1;F;0;0t;1;0l;2;0o;2;0a;1;0f;0;1b;0```",
            inline=False,
        )
    elif player == playerOptions.TENNN:
        embed = discord.Embed(title="VALORANT setting", color=0xFF0000)
        embed.add_field(
            name="ユーザー情報",
            value="player:TENNN\nTwitter:[@tenhakyou](https://twitter.com/tenhakyou)",
        )
        embed.set_thumbnail(url="https://as2.ftcdn.net/v2/jpg/03/71/01/31/1000_F_371013119_o87usHtqx06jK5IQ3sywV3cMslyx34Hi.jpg")
        embed.add_field(
            name="デバイス",
            value="マウス:[GPROX SUPERLIGHT](https://onl.sc/WuQGX3P)\nキーボード:[G913TKL](https://onl.sc/qAxCVzG)",
            inline=False,
        )
        embed.add_field(name="感度", value="DPI:800\nゲーム内感度:0.28", inline=False)
        embed.add_field(
            name="クロスヘア", value="```0;P;H;0;0l;4;0o;0;0a;1;0f;0;1b;0```", inline=False
        )
    elif player == playerOptions.Neth:
        embed = discord.Embed(title="VALORANT setting", color=0xFF0000)
        embed.add_field(
            name="ユーザー情報",
            value="player:Neth\nTwitter:[@neth_vz](https://twitter.com/neth_vz)",
        )
        embed.set_thumbnail(url="https://as2.ftcdn.net/v2/jpg/03/71/01/31/1000_F_371013119_o87usHtqx06jK5IQ3sywV3cMslyx34Hi.jpg")
        embed.add_field(
            name="デバイス",
            value="マウス:[G703h](https://onl.sc/QKF3Qn7)\nキーボード:[G913TKL](https://onl.sc/qAxCVzG)",
            inline=False,
        )
        embed.add_field(name="感度", value="DPI:800\nゲーム内感度:0.4", inline=False)
        embed.add_field(
            name="クロスヘア",
            value="```0;P;0;S;1;P;C;4;H;0;F;0;0t;5;0l;1;0o;2;0a;1;0f;0;1b;0;A;O;1;D;1;Z;3;F;0;S;0;0b;0;1b;0;S;S;0;O;1```",
            inline=False,
        )
    elif player == playerOptions.Meiy:
        embed = discord.Embed(title="VALORANT setting", color=0xFF0000)
        embed.add_field(
            name="ユーザー情報",
            value="player:Meiy\nTwitter:[@meiyfps](https://twitter.com/meiyfps)",
        )
        embed.set_thumbnail(url="https://as2.ftcdn.net/v2/jpg/03/71/01/31/1000_F_371013119_o87usHtqx06jK5IQ3sywV3cMslyx34Hi.jpg")
        embed.add_field(
            name="デバイス",
            value="マウス:[GPRO X SUPERLIGHT](https://onl.sc/WuQGX3P)\nキーボード:[Ducky One2 Mini](https://onl.sc/eGCWpV6)",
            inline=False,
        )
        embed.add_field(name="感度", value="DPI:800\nゲーム内感度:0.4", inline=False)
        embed.add_field(
            name="クロスヘア",
            value="```0;S;1;P;O;1;D;1;0b;0;1b;0;S;C;0;S;1.031;O;1```",
            inline=False,
        )
    elif player == playerOptions.Derialy:
        embed = discord.Embed(title="VALORANT setting", color=0xFF0000)
        embed.add_field(
            name="ユーザー情報",
            value="player:Derialy\nTwitter:[@derialy](https://twitter.com/derialy)",
        )
        embed.set_thumbnail(url="https://as2.ftcdn.net/v2/jpg/03/71/01/31/1000_F_371013119_o87usHtqx06jK5IQ3sywV3cMslyx34Hi.jpg")
        embed.add_field(
            name="デバイス",
            value="マウス:[Viper V2 Pro](https://onl.sc/1gyKGBm)\nキーボード:[Huntsman V2](https://onl.sc/MY7v16k)",
            inline=False,
        )
        embed.add_field(name="感度", value="DPI:1600\nゲーム内感度:0.125", inline=False)
        embed.add_field(name="クロスヘア", value="```情報がありません```", inline=False)
    elif player == playerOptions.Bazz:  #
        embed = discord.Embed(title="VALORANT setting", color=0xFF0000)
        embed.add_field(
            name="ユーザー情報",
            value="player:Bazz\nTwitter:[@bazz900](https://twitter.com/bazz900)",
        )
        embed.set_thumbnail(url="https://as2.ftcdn.net/v2/jpg/03/71/01/31/1000_F_371013119_o87usHtqx06jK5IQ3sywV3cMslyx34Hi.jpg")
        embed.add_field(
            name="デバイス",
            value="マウス:[GPRO X SUPERLIGHT](https://amzn.asia/d/57vIYey)\nキーボード:[Alloy origins core](https://amzn.asia/d/17dR7e7)",
            inline=False,
        )
        embed.add_field(name="感度", value="DPI:800\nゲーム内感度:0.485", inline=False)
        embed.add_field(name="クロスヘア", value="```情報がありません```", inline=False)
    elif player == playerOptions.Minty:  #
        embed = discord.Embed(title="VALORANT setting", color=0xFF0000)
        embed.add_field(
            name="ユーザー情報",
            value="player:Minty\nTwitter:[@MintyVL](https://twitter.com/MintyVL)",
        )
        embed.set_thumbnail(url="https://as2.ftcdn.net/v2/jpg/03/71/01/31/1000_F_371013119_o87usHtqx06jK5IQ3sywV3cMslyx34Hi.jpg")
        embed.add_field(
            name="デバイス",
            value="マウス:[G703h](https://amzn.asia/d/0ZA0TUt)\nキーボード:[K65 RAPIDFIRE](https://amzn.asia/d/0o4pJMV)",
            inline=False,
        )
        embed.add_field(name="感度", value="DPI:1600\nゲーム内感度:0.43", inline=False)
        embed.add_field(name="クロスヘア", value="```情報がありません```", inline=False)
    elif player == playerOptions.Fisker:  #
        embed = discord.Embed(title="VALORANT setting", color=0xFF0000)
        embed.add_field(
            name="ユーザー情報",
            value="player:Fisker\nTwitter:[@2ert_fps](https://twitter.com/2ert_fps)",
        )
        embed.set_thumbnail(url="https://as2.ftcdn.net/v2/jpg/03/71/01/31/1000_F_371013119_o87usHtqx06jK5IQ3sywV3cMslyx34Hi.jpg")
        embed.add_field(
            name="デバイス",
            value="マウス:[GPRO X SUPERLIGHT](https://amzn.asia/d/57vIYey)\nキーボード:[APEX PRO TKL](https://amzn.asia/d/59a16gK)",
            inline=False,
        )
        embed.add_field(name="感度", value="DPI:400\nゲーム内感度:0.629", inline=False)
        embed.add_field(name="クロスヘア", value="```情報がありません```", inline=False)
    elif player == playerOptions.Something:  #
        embed = discord.Embed(title="VALORANT setting", color=0xFF0000)
        embed.add_field(
            name="ユーザー情報",
            value="player:Something\nTwitter:[@smthlikeyou11](https://twitter.com/smthlikeyou11)",
        )
        embed.set_thumbnail(url="https://as2.ftcdn.net/v2/jpg/03/71/01/31/1000_F_371013119_o87usHtqx06jK5IQ3sywV3cMslyx34Hi.jpg")
        embed.add_field(
            name="デバイス",
            value="マウス:[GPRO X SUPERLIGHT](https://amzn.asia/d/57vIYey)\nキーボード:[alloy fps](https://amzn.asia/d/hrJBsPH)",
            inline=False,
        )
        embed.add_field(name="感度", value="DPI:1600\nゲーム内感度:0.433", inline=False)
        embed.add_field(name="クロスヘア", value="```情報がありません```", inline=False)
    elif player == playerOptions.Vici:  #
        embed = discord.Embed(title="VALORANT setting", color=0xFF0000)
        embed.add_field(
            name="ユーザー情報",
            value="player:Vici\nTwitter:[@Vici_tty](https://twitter.com/Vici_tty)",
        )
        embed.set_thumbnail(url="https://as2.ftcdn.net/v2/jpg/03/71/01/31/1000_F_371013119_o87usHtqx06jK5IQ3sywV3cMslyx34Hi.jpg")
        embed.add_field(
            name="デバイス",
            value="マウス:[GPRO X SUPERLIGHT](https://amzn.asia/d/57vIYey)\nキーボード:[alloy fps](https://amzn.asia/d/hrJBsPH)",
            inline=False,
        )
        embed.add_field(name="感度", value="DPI:800\nゲーム内感度:0.32", inline=False)
        embed.add_field(name="クロスヘア", value="```情報がありません```", inline=False)
    elif player == playerOptions.Seoldam:  #
        embed = discord.Embed(title="VALORANT setting", color=0xFF0000)
        embed.add_field(
            name="ユーザー情報",
            value="player:Seoldam\nTwitter:[@SeoldamTwit](https://twitter.com/SeoldamTwit)",
        )
        embed.set_thumbnail(url="https://as2.ftcdn.net/v2/jpg/03/71/01/31/1000_F_371013119_o87usHtqx06jK5IQ3sywV3cMslyx34Hi.jpg")
        embed.add_field(
            name="デバイス",
            value="マウス:[GPRO X SUPERLIGHT](https://amzn.asia/d/57vIYey)\nキーボード:[K70 RGB TKL](https://amzn.asia/d/5JNUu8k)",
            inline=False,
        )
        embed.add_field(name="感度", value="DPI:400\nゲーム内感度:0.7", inline=False)
        embed.add_field(
            name="クロスヘア",
            value="```0;C;1;S;1;P;C;5;H;0;M;1;0l;5;0o;2;0a;1;0f;0;1b;0```",
            inline=False,
        )
    elif player == playerOptions.TenZ:  #
        embed = discord.Embed(title="VALORANT setting", color=0xFF0000)
        embed.add_field(
            name="ユーザー情報",
            value="player:TenZ\nTwitter:[@TenZOfficial](https://twitter.com/TenZOfficial)",
        )
        embed.set_thumbnail(url="https://as2.ftcdn.net/v2/jpg/03/71/01/31/1000_F_371013119_o87usHtqx06jK5IQ3sywV3cMslyx34Hi.jpg")
        embed.add_field(
            name="デバイス",
            value="マウス:[finalmouse starlight-12](https://amzn.asia/d/4oto3jU)\nキーボード:[Alloy Origins Core](https://amzn.asia/d/6ED3eyA)",
            inline=False,
        )
        embed.add_field(name="感度", value="DPI:1600\nゲーム内感度:0.22", inline=False)
        embed.add_field(
            name="クロスヘア",
            value="```0;S;1;P;C;5;H;0;M;1;0l;4;0o;2;0a;1;0f;0;1b;0;S;C;4;O;1```",
            inline=False,
        )
    elif player == playerOptions.Shroud:  #
        embed = discord.Embed(title="VALORANT setting", color=0xFF0000)
        embed.add_field(
            name="ユーザー情報",
            value="player:Shroud\nTwitter:[@shroud](https://twitter.com/shroud)",
        )
        embed.set_thumbnail(url="https://as2.ftcdn.net/v2/jpg/03/71/01/31/1000_F_371013119_o87usHtqx06jK5IQ3sywV3cMslyx34Hi.jpg")
        embed.add_field(
            name="デバイス",
            value="マウス:[GPROX ShroundEdition](https://amzn.asia/d/c9s3bQs)\nキーボード:[G913TKL](https://amzn.asia/d/aOkpmuT)",
            inline=False,
        )
        embed.add_field(name="感度", value="DPI:400\nゲーム内感度:0.8", inline=False)
        embed.add_field(
            name="クロスヘア",
            value="```0;P;C;4;H;0;F;0;0l;5;0o;0;0a;1;0f;0;1b;0```",
            inline=False,
        )
    elif player == playerOptions.FNS:  #
        embed = discord.Embed(title="VALORANT setting", color=0xFF0000)
        embed.add_field(
            name="ユーザー情報", value="player:FNS\nTwitter:[@FNS](https://twitter.com/FNS)"
        )
        embed.set_thumbnail(url="https://as2.ftcdn.net/v2/jpg/03/71/01/31/1000_F_371013119_o87usHtqx06jK5IQ3sywV3cMslyx34Hi.jpg")
        embed.add_field(
            name="デバイス",
            value="マウス:[GPRO X SUPERLIGHT](https://amzn.asia/d/fyJJQpP)\nキーボード:[K95 RGB PLATINUM](https://amzn.asia/d/6JOQy5V)",
            inline=False,
        )
        embed.add_field(name="感度", value="DPI:800\nゲーム内感度:0.283", inline=False)
        embed.add_field(
            name="クロスヘア", value="```0;P;H;0;F;0;0l;4;0a;1;0f;0;1b;0```", inline=False
        )
    elif player == playerOptions.Victor:  #
        embed = discord.Embed(title="VALORANT setting", color=0xFF0000)
        embed.add_field(
            name="ユーザー情報",
            value="player:Victor\nTwitter:[@victorwong](https://twitter.com/victorwong)",
        )
        embed.set_thumbnail(url="https://as2.ftcdn.net/v2/jpg/03/71/01/31/1000_F_371013119_o87usHtqx06jK5IQ3sywV3cMslyx34Hi.jpg")
        embed.add_field(
            name="デバイス",
            value="マウス:[G703h](https://amzn.asia/d/iPzA965)\nキーボード:[K70 RGB TKL](https://amzn.asia/d/iogF1co)",
            inline=False,
        )
        embed.add_field(name="感度", value="DPI:800\nゲーム内感度:0.283", inline=False)
        embed.add_field(
            name="クロスヘア", value="```0;P;H;0;F;0;0l;4;0a;1;0f;0;1b;0```", inline=False
        )
    elif player == playerOptions.Yay:  #
        embed = discord.Embed(title="VALORANT setting", color=0xFF0000)
        embed.add_field(
            name="ユーザー情報", value="player:Yay\nTwitter:[@yay](https://twitter.com/yay)"
        )
        embed.set_thumbnail(url="https://as2.ftcdn.net/v2/jpg/03/71/01/31/1000_F_371013119_o87usHtqx06jK5IQ3sywV3cMslyx34Hi.jpg")
        embed.add_field(
            name="デバイス",
            value="マウス:[GPRO X SUPERLIGHT](https://amzn.asia/d/fyJJQpP)\nキーボード:[G913TKL](https://amzn.asia/d/iWhKRCk)",
            inline=False,
        )
        embed.add_field(name="感度", value="DPI:800\nゲーム内感度:0.27", inline=False)
        embed.add_field(
            name="クロスヘア",
            value="```0;P;H;0;F;0;0l;4;0o;0;0a;1;0f;0;1b;0```",
            inline=False,
        )
    elif player == playerOptions.Aspas:  #
        embed = discord.Embed(title="VALORANT setting", color=0xFF0000)
        embed.add_field(
            name="ユーザー情報",
            value="player:Aspas\nTwitter:[@loud_aspas](https://twitter.com/loud_aspas)",
        )
        embed.set_thumbnail(url="https://as2.ftcdn.net/v2/jpg/03/71/01/31/1000_F_371013119_o87usHtqx06jK5IQ3sywV3cMslyx34Hi.jpg")
        embed.add_field(
            name="デバイス",
            value="マウス:[VAXX XE](https://www.vaxee.co/jp/product.php?act=view&id=196)\nキーボード:[G913TKL](https://amzn.asia/d/iWhKRCk)",
            inline=False,
        )
        embed.add_field(name="感度", value="DPI:800\nゲーム内感度:0.4", inline=False)
        embed.add_field(
            name="クロスヘア", value="```0;P;C;5;O;1;D;1;Z;3;F;0;0b;0;1b;0```", inline=False
        )
    elif player == playerOptions.ScreaM:  #
        embed = discord.Embed(title="VALORANT setting", color=0xFF0000)
        embed.add_field(
            name="ユーザー情報",
            value="player:ScreaM\nTwitter:[@ScreaM_](https://twitter.com/ScreaM_)",
        )
        embed.set_thumbnail(url="https://as2.ftcdn.net/v2/jpg/03/71/01/31/1000_F_371013119_o87usHtqx06jK5IQ3sywV3cMslyx34Hi.jpg")
        embed.add_field(
            name="デバイス",
            value="マウス:[Finalmouse Ultralight 2](https://amzn.asia/d/4ahiUUT)\nキーボード:[alloy fps](https://amzn.asia/d/hZvO51b)",
            inline=False,
        )
        embed.add_field(name="感度", value="DPI:400\nゲーム内感度:0.965", inline=False)
        embed.add_field(
            name="クロスヘア",
            value="```0;P;C;5;O;0.286;D;1;F;0;0t;0;0l;0;0o;0;0a;1;0f;0;1b;0```",
            inline=False,
        )
    elif player == playerOptions.Stax:  #
        embed = discord.Embed(title="VALORANT setting", color=0xFF0000)
        embed.add_field(
            name="ユーザー情報",
            value="player:Stax\nTwitter:[@staxVLRT](https://twitter.com/staxVLRT)",
        )
        embed.set_thumbnail(url="https://as2.ftcdn.net/v2/jpg/03/71/01/31/1000_F_371013119_o87usHtqx06jK5IQ3sywV3cMslyx34Hi.jpg")
        embed.add_field(
            name="デバイス",
            value="マウス:[ZOWIE EC2](https://amzn.asia/d/7ydncME)\nキーボード:[Huntsman V2](https://amzn.asia/d/ijuPoEm)",
            inline=False,
        )
        embed.add_field(name="感度", value="DPI:400\nゲーム内感度:0.45", inline=False)
        embed.add_field(
            name="クロスヘア",
            value="```0;P;C;4;H;0;F;0;S;0;0l;4;0o;2;0a;1;0f;0;1b;0```",
            inline=False,
        )
    elif player == playerOptions.Rb:  #
        embed = discord.Embed(title="VALORANT setting", color=0xFF0000)
        embed.add_field(
            name="ユーザー情報",
            value="player:Stax\nTwitter:[@staxVLRT](https://twitter.com/staxVLRT)",
        )
        embed.set_thumbnail(url="https://as2.ftcdn.net/v2/jpg/03/71/01/31/1000_F_371013119_o87usHtqx06jK5IQ3sywV3cMslyx34Hi.jpg")
        embed.add_field(
            name="デバイス",
            value="マウス:[GPRO X SUPERLIGHT](https://amzn.asia/d/fyJJQpP)\nキーボード:[GPROX](https://onl.sc/AA2jDyR)",
            inline=False,
        )
        embed.add_field(name="感度", value="DPI:800\nゲーム内感度:0.275", inline=False)
        embed.add_field(
            name="クロスヘア",
            value="```0;P;C;5;H;0;F;0;0l;4;0o;2;0a;1;0f;0;1b;0```",
            inline=False,
        )
    elif player == playerOptions.BuZz:  #
        embed = discord.Embed(title="VALORANT setting", color=0xFF0000)
        embed.add_field(
            name="ユーザー情報",
            value="player:BuZz\nTwitter:[@Buzz_kr](https://twitter.com/Buzz_kr)",
        )
        embed.set_thumbnail(url="https://as2.ftcdn.net/v2/jpg/03/71/01/31/1000_F_371013119_o87usHtqx06jK5IQ3sywV3cMslyx34Hi.jpg")
        embed.add_field(
            name="デバイス",
            value="マウス:[zowie s2](https://amzn.asia/d/9ir2Nht)\nキーボード:[Huntsman V2](https://amzn.asia/d/4nMkLrq)",
            inline=False,
        )
        embed.add_field(name="感度", value="DPI:400\nゲーム内感度:0.57", inline=False)
        embed.add_field(
            name="クロスヘア",
            value="```0;P;C;5;O;1;F;0;0t;1;0l;2;0o;2;0a;1;0f;0;1b;0```",
            inline=False,
        )
    elif player == playerOptions.Jinggg:
        embed = discord.Embed(title="VALORANT setting", color=0xFF0000)
        embed.add_field(
            name="ユーザー情報",
            value="player:Jinggg\nTwitter:[@Jingggxd](https://twitter.com/Jingggxd)",
        )
        embed.set_thumbnail(url="https://as2.ftcdn.net/v2/jpg/03/71/01/31/1000_F_371013119_o87usHtqx06jK5IQ3sywV3cMslyx34Hi.jpg")
        embed.add_field(
            name="デバイス",
            value="マウス:[finalmouse starlight-12](https://amzn.asia/d/frekhLE)\nキーボード:[Alloy origins core](https://amzn.asia/d/5Zp0Me0)",
            inline=False,
        )
        embed.add_field(name="感度", value="DPI:1600\nゲーム内感度:0.2", inline=False)
        embed.add_field(
            name="クロスヘア",
            value="```0;S;1;P;C;1;O;1;0t;1;0l;2;0o;2;0a;1;0f;0;1b;0;S;C;5```",
            inline=False,
        )
    await interaction.response.send_message(embed=embed)
    
# ----------------------------------------------------------------------------------------
#サイコロ
@bot.tree.command(name="dice", description="サイコロを振ります")
async def getdice(interaction: discord.Interaction, count: typing.Optional[int] = 1):
    """
    :param count: フルサイコロの数を1~10の間で指定できます
    """
    if count < 1 or count > 10:
        error_embed = discord.Embed(title="エラー", color=0xFF0000,description="`count`の引数が不正です\n`count`では1~10の整数を入力してください")
        await interaction.response.send_message(embed=error_embed,ephemeral=True)
        return
    
    dice_list = [discord.PartialEmoji(name='number1', id=1104161427574493284),discord.PartialEmoji(name='number2', id=1104161424923693066),discord.PartialEmoji(name='number3', id=1104161422776221768),discord.PartialEmoji(name='number4', id=1104161429390643260),discord.PartialEmoji(name='number5', id=1104161419022315530),discord.PartialEmoji(name='number6', id=1104161421396287500)]
    dice_results = [str(random.choice(dice_list)) for _ in range(count)]
    user = interaction.user.mention
    thumbnail_url = "https://cdn.discordapp.com/attachments/1101747131519348856/1104156246833111211/5130295.png"

    embed = discord.Embed(title="<a:pinkdice:1104157383904723004> サイコロ <a:pinkdice:1104157383904723004> ", color=0xFFD700)
    embed.set_thumbnail(url=thumbnail_url)
    embed.add_field(name="ユーザー", value=user, inline=False)
    embed.add_field(name="結果", value=" ".join(dice_results), inline=False)

    await interaction.response.send_message(embed=embed)
    
# ----------------------------------------------------------------------------------------
#ランダム
@bot.tree.command(name="random", description="複数の内容からランダムで一つ選びます")
async def random_choice(interaction: discord.Interaction, content: str):
    """
    :param content: 抽選する内容を指定できます『,』カンマ区切り
    """
    if content is None:
        await interaction.response.send_message("抽選する内容を入力してください")
        return
    
    choices = content.split(",")
    if len(choices) < 2:
        error_embed = discord.Embed(title="エラー", color=0xFF0000,description="`content`の引数が不正です\n`content`では少なくとも2つ以上の抽選内容を入力してください\n抽選内容は「,」区切りで指定出来ます")
        await interaction.response.send_message(embed=error_embed,ephemeral=True)
        return
    
    result = random.choice(choices)
    embed = discord.Embed(title="ランダム", color=0xFFD700)
    embed.add_field(name="抽選内容", value=r"```" + '\n'.join(choices) + r"```", inline=False)
    embed.add_field(name="結果", value=result, inline=False)
    await interaction.response.send_message(embed=embed)
    
# ----------------------------------------------------------------------------------------
# 猫
@bot.tree.command(name="cat", description="猫のGIFをランダムで送信します")
async def cat(interaction: discord.Interaction):
    # ランダムでGIFを選択
    gifs = [
        "https://media.tenor.com/OJ3YmQ57_vIAAAAS/jambo-jschlatt.gif",
        "https://media.tenor.com/dteyPLcdJJkAAAAM/cats-love.gif",
        "https://media.tenor.com/7r-BGEoIohkAAAAM/meme-cat.gif",
        "https://media.tenor.com/WzI5--49rKgAAAAM/cat.gif",
        "https://media.tenor.com/FFfFI5OA5-IAAAAM/elliot-katt.gif",
        "https://media.tenor.com/-DY1sCSEXqUAAAAM/sad-cat.gif",
        "https://media.tenor.com/Ro5LGkOGGS0AAAAM/cat-catdriving.gif",
        "https://media.tenor.com/yybmSYAC6wsAAAAM/cat-funny-cat-memes.gif",
        "https://media.tenor.com/OeswMjtpFdQAAAAM/cat.gif",
        "https://media.tenor.com/Zg4IASBSaUEAAAAM/cat.gif",
        "https://media.tenor.com/aVC6ggUOKGIAAAAM/lets-chat-cats.gif",
        "https://media.tenor.com/l37il_hI3tEAAAAM/smilecat.gif",
        "https://media.tenor.com/OeswMjtpFdQAAAAM/cat.gif",
        "https://media.tenor.com/Zuq7vCIAeCYAAAAM/cat-close-door.gif",
        "https://media.tenor.com/2v1aDCelTJgAAAAM/cat-cats.gif",
        "https://media.tenor.com/3hNFj_XibiYAAAAM/cat.gif",
        "https://media.tenor.com/w_0kE14Tr7gAAAAM/cat.gif",
        "https://media.tenor.com/ObyK0WXilXUAAAAM/kitty-cat.gif",
        "https://media.tenor.com/zrpyKEyxZGwAAAAM/fat-cat-laser-eyes.gif",
        "https://media.tenor.com/AVY7rXFI9_MAAAAM/cute-cute-cat.gif",
        "https://media.tenor.com/fWXyb86dSWMAAAAM/ok-cat.gif",
        "https://media.tenor.com/EYx8vYWMJTEAAAAM/cat-sad.gif",
        "https://media.tenor.com/qavWfVh55fsAAAAM/cat-cute-cat.gif",
        "https://media.tenor.com/Ao9O4SGI-cQAAAAM/sleep-cat-two-cat.gif",
        "https://media.tenor.com/NjF-4LBl_SsAAAAM/cat-sad.gif",
        "https://media.tenor.com/pONKfKjvep4AAAAM/cat-shocked.gif",
        "https://media.tenor.com/P9DFtD3HjcwAAAAM/cat-cats-love.gif",
        "https://media.tenor.com/uu9seSBtPaEAAAAM/sad-cat.gif",
        "https://media.tenor.com/XAJx1NnLN50AAAAM/this-cat-is-d-d-cat.gif",
        "https://media.tenor.com/bpDg0P2EmF8AAAAM/zane-zane-romeave.gif",
        "https://media.tenor.com/LRkzjK1AHRIAAAAM/this-cat.gif",
        "https://media.tenor.com/4C_BSADmzGIAAAAM/cat.gif",
        "https://media.tenor.com/UQXJ79S4ObUAAAAM/cat-calico-cat.gif",
        "https://media.tenor.com/7iZ3GSJtRZ4AAAAM/cat-wtf-cat.gif",
        "https://media.tenor.com/3s-xdJ9XuhwAAAAM/love-cat-love-cats.gif",
        "https://media.tenor.com/MUSE-PBz4V8AAAAM/this-cat-is-d-this-cat-is-r.gif",
        "https://media.tenor.com/jbg4khfGnIYAAAAM/depressed-cat-no-image-perms.gif",
        "https://media.tenor.com/z2IqVLn-acMAAAAM/meme.gif",
        "https://media.tenor.com/JTWkLQyjzWYAAAAM/peach-peach-cat.gif",
        "https://media.tenor.com/JFb7OjmNcewAAAAM/cat-thinking.gif",
        "https://media.tenor.com/W1QGtsHhNlMAAAAM/party-cats.gif",
        "https://media.tenor.com/Ox1McvWB6dUAAAAM/cat-cats.gif",
        "https://media.tenor.com/VdIKn05yIh8AAAAM/cat-sleep.gif",
        "https://media.tenor.com/nazD56q3aTgAAAAM/dianbo-cat.gif",
        "https://media.tenor.com/zTh0V1eURRQAAAAM/nom-nom-cat-cat-food.gif",
        "https://media.tenor.com/aIPmD6Nsnt8AAAAM/cat-cats.gif",
        "https://media.tenor.com/nb8KJP1uMOYAAAAM/kiss-cat.gif",
        "https://media.tenor.com/ju6iJbm2gCIAAAAM/cat-cats.gif",
        "https://media.tenor.com/4qCbTQdhgCcAAAAM/this-cat-is-ee.gif",
        "https://media.tenor.com/_4nl1Qq1RKcAAAAM/partying-cat-party.gif",
        "https://media.tenor.com/eDyQ50PxkhoAAAAM/5lettermwordsry.gif",
        "https://media.tenor.com/53c7rNc8wZ0AAAAM/cat-cats.gif",
    ]
    gif = random.choice(gifs)

    # 埋め込みメッセージを作成
    embed = discord.Embed(
        title="<a:pinkcat:1104535759677046835>にゃーん<a:pinkcat:1104535759677046835>", description=f"{interaction.user.mention}ニャニャ！！", color=0xFFD700
    )
    embed.set_image(url=gif)

    # 埋め込みメッセージを送信
    await interaction.response.send_message(embed=embed)

# ----------------------------------------------------------------------------------------
# 犬
@bot.tree.command(name="dog", description="犬のGIFをランダムで送信します")
async def dog(interaction: discord.Interaction):
    # ランダムでGIFを選択
    gifs = [
        "https://media.tenor.com/MINogBSXIpcAAAAM/dog.gif",
        "https://media.tenor.com/Nfct9RreQfUAAAAM/dog-meme.gif",
        "https://media.tenor.com/8cACB90A-3gAAAAM/dog.gif",
        "https://media.tenor.com/mum4Jou2LFEAAAAM/dog-cute.gif",
        "https://media.tenor.com/tDaIKZXmXR4AAAAM/cute-dog-doggy.gif",
        "https://media.tenor.com/N2tYUtIr8mMAAAAM/dog.gif",
        "https://media.tenor.com/lBpPIVojebAAAAAM/puppytalesphotos-puppytales.gif",
        "https://media.tenor.com/qwoJPWA9Qj4AAAAM/dog-funny.gif",
        "https://media.tenor.com/Y1DBcZPPmAgAAAAM/dog.gif",
        "https://media.tenor.com/-VlEOvAd794AAAAM/dog-swing.gif",
        "https://media.tenor.com/JiRMdcRMYgoAAAAM/bellebows-happy-dog.gif",
        "https://media.tenor.com/nEsdZ0qa6QcAAAAM/dog.gif",
        "https://media.tenor.com/0gKQdjnZDLkAAAAM/dog-funny-dog.gif",
        "https://media.tenor.com/W3rSpAy5GGkAAAAM/dog.gif",
        "https://media.tenor.com/L-BFYVDXGKAAAAAM/woah-dog.gif",
        "https://media.tenor.com/oqV4uQja1z4AAAAM/puppytalesphotos-puppytales.gif",
        "https://media.tenor.com/K0QNIySkzdEAAAAM/dog-smile-eeyeyy1.gif",
        "https://media.tenor.com/YGDMt2ZOFlsAAAAM/dog.gif",
        "https://media.tenor.com/SrxboPIzd7QAAAAM/leadvirgo-dogs.gif",
        "https://media.tenor.com/EGxqLQTh9yIAAAAM/satisfied-viralhog.gif",
        "https://media.tenor.com/M3F6UcaCUTQAAAAM/dog-funny.gif",
        "https://media.tenor.com/JHAtTk7HhOoAAAAM/cute-dog.gif",
        "https://media.tenor.com/x5COXUq1c2YAAAAM/koollua-dog.gif",
        "https://media.tenor.com/-OEaVta-W10AAAAM/dogs-cute-dogs.gif",
        "https://media.tenor.com/iVyz08Z9JWwAAAAM/dog.gif",
        "https://media.tenor.com/6h5zUckDYgIAAAAM/dog.gif",
        "https://media.tenor.com/j7tf7BOQifIAAAAM/laughing-dog-dog.gif",
        "https://media.tenor.com/uWQ72vKSAV4AAAAM/dog.gif",
        "https://media.tenor.com/SohCbAxqOqIAAAAM/dog-what-the-dog-doin.gif",
        "https://media.tenor.com/H04kLkyt_tUAAAAM/dog-little-dog.gif",
        "https://media.tenor.com/zM4rRDMGUaoAAAAM/the-name-of-this-dog-dog.gif",
        "https://media.tenor.com/BUFH4d5J23UAAAAM/sus-dog.gif",
        "https://media.tenor.com/bGOhVBvg9_kAAAAM/talking-dog-meme.gif",
        "https://media.tenor.com/T4W-AtAUegYAAAAM/byuntear-sad-dog.gif",
        "https://media.tenor.com/hmywIR2hsz0AAAAM/sad-depressed.gif",
        "https://media.tenor.com/7abiFyWYHSMAAAAM/rbag-reds-bar-and-grill.gif",
        "https://media.tenor.com/i-7XQw1mvqQAAAAM/dog.gif",
        "https://media.tenor.com/JaZOYveLE6kAAAAM/puppytalesphotos-puppytales.gif",
        "https://media.tenor.com/i8sYqYjUjE8AAAAM/discord.gif",
        "https://media.tenor.com/CC8y6oQXPLkAAAAM/bumby-wool.gif",
        "https://media.tenor.com/SyFHEqGaUCwAAAAM/veeunus-hug.gif",
        "https://media.tenor.com/OktC7kS1xeEAAAAM/happy-dog-dog.gif",
        "https://media.tenor.com/EBj-WHdPgLkAAAAM/dog-hug.gif",
    ]
    gif = random.choice(gifs)

    # 埋め込みメッセージを作成
    embed = discord.Embed(
        title="<:cutedog:1104536109947551816>ワンワン<:cutedog:1104536109947551816>", description=f"{interaction.user.mention}ワンワン！！", color=0xFFD700
    )
    embed.set_image(url=gif)

    # 埋め込みメッセージを送信
    await interaction.response.send_message(embed=embed)


# ----------------------------------------------------------------------------------------
# ループ
@bot.tree.command(name="loop", description="ループするGIFをランダムで送信します")
async def loop(interaction: discord.Interaction):
    # ランダムでGIFを選択
    gifs = [
        "https://media.tenor.com/-sL5lSwzQSkAAAAj/rolling-cute.gif",
        "https://media.tenor.com/Xk5vnzCZBjUAAAAM/loop.gif",
        "https://media.tenor.com/IkAda59JrXEAAAAM/loop.gif",
        "https://media.tenor.com/tCOZGCqtI-0AAAAM/edmas-loop.gif",
        "https://media.tenor.com/0gsHPjo_B-oAAAAM/train-loop.gif",
        "https://media.tenor.com/j0PamBdd-ygAAAAM/yes-loop.gif",
        "https://media.tenor.com/-u6hqGSNgrIAAAAM/never-ending-doge.gif",
        "https://media.tenor.com/PHRc1OzoLqcAAAAM/blender-loop.gif",
        "https://media.tenor.com/dNZqfhQPmw0AAAAM/loop-run.gif",
        "https://media.tenor.com/5Stx8Dcz3RIAAAAM/fall-scream.gif",
        "https://media.tenor.com/VfvJNrJ4tSoAAAAM/headbang-perfectloop.gif",
        "https://media.tenor.com/lL1JlYi4O1kAAAAM/loop.gif",
        "https://media.tenor.com/GDi1kIVtcYcAAAAM/patrick-shocked.gif",
        "https://media.tenor.com/A4T9nucP3dkAAAAM/sweatsmile-infinite-loop.gif",
        "https://media.tenor.com/x9YNm69S6vIAAAAM/sean-watson-loop.gif",
        "https://media.tenor.com/KmrG9W-KGsEAAAAM/cat-yawn.gif",
        "https://media.tenor.com/qv8JmWKsgowAAAAM/blender-satisfying.gif",
        "https://media.tenor.com/rhHtWPATmRgAAAAM/loop-satisfying.gif",
        "https://media.tenor.com/BKQreHi3C6oAAAAM/discord-satisfying.gif",
        "https://media.tenor.com/-0s0ZOCr_3kAAAAM/pogchamp-loop.gif",
        "https://media.tenor.com/7eoLPlS3VpwAAAAM/slicing-satisfying.gif",
        "https://media.tenor.com/VUDkGyFt9p8AAAAM/catgen.gif",
        "https://media.tenor.com/NFe9gDxhN6UAAAAM/slicing-satisfying.gif",
        "https://media.tenor.com/tNHib2Y6B1QAAAAM/whoa-loop.gif",
        "https://media.tenor.com/aFrOLqshRL0AAAAM/perfect-loop-animation.gif",
        "https://media.tenor.com/MKxbEPAUDwIAAAAM/slavoljub-slagalica.gif",
        "https://media.tenor.com/YhTTGAttqSYAAAAM/infinite-loop-looping.gif",
        "https://media.tenor.com/rU51A48PrXwAAAAM/slicing-satisfying.gif",
        "https://media.tenor.com/GAmPDn4_RHgAAAAM/slab-oddly-statisfying.gif",
        "https://media.tenor.com/_XRR1kvQAc8AAAAM/slicing-satisfying.gif",
        "https://media.tenor.com/m87mdzFbC3oAAAAM/digibyte-dgb.gif",
        "https://media.tenor.com/1pxfDm6nMcsAAAAM/slicing-satisfying.gif",
        "https://media.tenor.com/7Co5XDxkOgMAAAAM/roller-coaster-loop.gif",
        "https://media.tenor.com/n9LtXz1HBqMAAAAM/slicing-satisfying.gif",
        "https://media.tenor.com/emYU3uAb4pIAAAAM/slicing-satisfying.gif",
        "https://media.tenor.com/Xtq9NUC1slcAAAAM/slicing-satisfying.gif",
        "https://media.tenor.com/WDC0uCWW_8kAAAAM/doge-loop.gif",
        "https://media.tenor.com/Sq8rjB9k1uEAAAAM/loop-open-mouth.gif",
        "https://media.tenor.com/V-mte5V2P2QAAAAM/slicing-satisfying.gif",
    ]
    gif = random.choice(gifs)

    # 埋め込みメッセージを作成
    embed = discord.Embed(
        title="<a:load:1102601827985412187> <a:load:1102601827985412187> Loop <a:load:1102601827985412187> <a:load:1102601827985412187>  ",
        description=f"<a:load:1102601827985412187> {interaction.user.mention} <a:load:1102601827985412187>",
        color=0xFFD700,
    )
    embed.set_image(url=gif)

    # 埋め込みメッセージを送信
    await interaction.response.send_message(embed=embed)


# ----------------------------------------------------------------------------------------
# アニメ
@bot.tree.command(name="anime", description="アニメのGIFをランダムで送信します")
async def loop(interaction: discord.Interaction):
    # ランダムでGIFを選択
    gifs = [
        "https://media.tenor.com/Oq1PYVh8AKAAAAAM/anime-lol.gif",
        "https://media.tenor.com/FGkrBiI4RCwAAAAM/ruka-sarashina-rent-a-girlfriend.gif",
        "https://media.tenor.com/o39q7qPq24gAAAAM/k-on-yui.gif",
        "https://media.tenor.com/GNSQOSM8IEUAAAAM/what-you-can-do-when-your-bored.gif",
        "https://media.tenor.com/pCuNY8zzJIsAAAAM/jujutsu-kaisen-gojo.gif",
        "https://media.tenor.com/7OTX6eSjjdcAAAAM/bozo-anime.gif",
        "https://media.tenor.com/QcvGepJbzYIAAAAM/anime-tumblr.gif",
        "https://media.tenor.com/qvvKGZhH0ysAAAAM/anime-girl.gif",
        "https://media.tenor.com/pF3s48bhdIsAAAAM/marin-kitagawa-anime-shy.gif",
        "https://media.tenor.com/Pb1TfZhr-OQAAAAM/spy-x-family-anya.gif",
        "https://media.tenor.com/kaRCm9ELxKgAAAAM/menhera-chan-chibi.gif",
        "https://media.tenor.com/8V9XeqNjpx4AAAAM/lol-anime-lol.gif",
        "https://media.tenor.com/gOsu5V-Y_i4AAAAM/shiki-mori-shikimoris-not-just-cute.gif",
        "https://media.tenor.com/x4TPrE9RvQgAAAAM/marin-marin-kitagawa.gif",
        "https://media.tenor.com/PGXshKPAUh4AAAAM/my-dress-up-darling-anime-love.gif",
        "https://media.tenor.com/LL72w7b7VnoAAAAM/kawaii-anime-girl.gif",
        "https://media.tenor.com/n-TmmTy2NdkAAAAM/%D0%BD%D0%B0%D0%B0%D0%B2%D1%83.gif",
        "https://media.tenor.com/9h_fq-S77_QAAAAM/kunoichi-tsubaki-no-mune-no-uchi-ninja.gif",
        "https://media.tenor.com/vCoQdHF0Sc0AAAAM/cute-anime-anime-girl.gif",
        "https://media.tenor.com/FkPTDE9bfhIAAAAM/dance-anime.gif",
        "https://media.tenor.com/XNP23mZA8G8AAAAM/megumin-konosuba.gif",
        "https://media.tenor.com/sj48RNNlFmwAAAAM/meme-anime.gif",
        "https://media.tenor.com/fndaS1mT7zcAAAAM/k-on-tired.gif",
        "https://media.tenor.com/S9BeEboyTk4AAAAM/anime-dance.gif",
        "https://media.tenor.com/nRgKRE4hEK8AAAAM/oshi-no-ko-anime.gif",
        "https://media.tenor.com/ioE5GE2aWiAAAAAM/oshi-no-ko-ai-hoshino.gif",
        "https://media.tenor.com/cwRlsPhQWVQAAAAM/oshi-no-ko-anime.gif",
        "https://media.tenor.com/CVekliXadvgAAAAM/ai-ruby.gif",
        "https://media.tenor.com/_ViOfohOysUAAAAM/ai-frame-gesture.gif",
        "https://media.tenor.com/9GtYOAcWbzYAAAAM/oshi-no-ko-anime.gif",
        "https://media.tenor.com/giUO2-235vAAAAAM/megumin-staff.gif",
        "https://media.tenor.com/Yp2RMCv6zJwAAAAM/nice-bakuretsu.gif",
        "https://media.tenor.com/7eWRtQE4DMEAAAAM/konosuba-kazuma.gif",
        "https://media.tenor.com/2CoAwNOjrDYAAAAM/aqua-konosuba.gif",
        "https://media.tenor.com/M0vhrMefn2cAAAAM/konosuba-megumin.gif",
        "https://media.tenor.com/rgH7ck0GdCoAAAAM/aqua-konosuba.gif",
        "https://media.tenor.com/uFKdpQunTQIAAAAM/wut-nani.gif",
        "https://media.tenor.com/c2xPqFVtyP0AAAAM/tensura-slime.gif",
        "https://media.tenor.com/5Bh7cvnFxjcAAAAM/rimuru-rimuru-tempest.gif",
        "https://media.tenor.com/IgF05mgl2HQAAAAM/rimuru-tensura.gif",
        "https://media.tenor.com/q40szdrj0pwAAAAM/jaisondragneel.gif",
        "https://media.tenor.com/3yenJmgmpm8AAAAM/tensura-rimuru.gif",
        "https://media.tenor.com/VUYT8-8_58AAAAAM/chika-kaguya-sama.gif",
        "https://media.tenor.com/AJWb_NMmEbkAAAAM/shock-kaguya-sama.gif",
        "https://media.tenor.com/Io5GoqpQmwsAAAAM/kaguya-sama-love-is-war-kaguya-sama.gif",
        "https://media.tenor.com/C6oMVvWINnQAAAAM/scarred-kaguya-sama-wa-kokurasetai-tensai-tachi-no-renai-zunousen.gif",
        "https://media.tenor.com/7UsfS4_MbGYAAAAM/random-gif.gif",
        "https://media.tenor.com/3bk7CFRCYFQAAAAM/kaguya-sama-kaguya.gif",
        "https://media.tenor.com/rd1GhSzbY6kAAAAM/dance-chika-fujiwara.gif",
        "https://media.tenor.com/IkFTBvSoRsAAAAAM/love-is-war-shijo.gif",
        "https://media.tenor.com/A35QpXkHdsMAAAAM/martin-martin-mu%C3%B1oz.gif",
        "https://media.tenor.com/pqRmConhCTUAAAAM/who-are-you-the-quintessential-quintuplets.gif",
        "https://media.tenor.com/0d2DoeaBXhoAAAAM/quintuplet-nino.gif",
        "https://media.tenor.com/2gipFBsGpWYAAAAM/avishay-yotsuba.gif",
        "https://media.tenor.com/I66JwpeuZ5gAAAAM/itsuki-gotoubun.gif",
        "https://media.tenor.com/mpm52wI2tZ4AAAAM/ichika.gif",
        "https://media.tenor.com/SCo7LfX56YEAAAAM/lycoris-recoil.gif",
        "https://media.tenor.com/W3wUoMhulrwAAAAM/lycoris-recoil-lycoris.gif",
        "https://media.tenor.com/EnCUFSXCYu4AAAAM/lycoris-recoil-takina.gif",
        "https://media.tenor.com/n_RaZkvRolcAAAAM/lycoris-recoil.gif",
        "https://media.tenor.com/zpvUIus_vOgAAAAM/anime-girl.gif",
        "https://media.tenor.com/oVzmIW9PtGUAAAAM/lycoris-recoil-pyon.gif",
        "https://media.tenor.com/1M0eqGYNeYkAAAAM/lycoris-recoil-kurumi.gif",
        "https://media.tenor.com/e-gxOAhgKrMAAAAM/lycoris-recoil-lycoris.gif",
        "https://media.tenor.com/ApLIxL3noCMAAAAM/lycoris-recoil.gif",
        "https://media.tenor.com/m70JD337OkoAAAAM/lycoris-recoil-falyn898.gif",
        "https://media.tenor.com/ifacgHYNzOwAAAAM/lycoris-recoil-lyco-reco.gif",
        "https://media.tenor.com/3Ov_pUxfvNMAAAAM/rezero-shinimodori.gif",
        "https://media.tenor.com/fES1vW2Chd0AAAAM/betelgeuse-rezero.gif",
        "https://media.tenor.com/TfBhmHrm9wUAAAAM/anime-rgb.gif",
        "https://media.tenor.com/omMgRMjESeAAAAAM/subaru-re-zero-subaru.gif",
        "https://media.tenor.com/2IASsV3yHAQAAAAM/rem-rezero.gif",
        "https://media.tenor.com/a1V-3ctKdQ0AAAAM/rem-rezero.gif",
        "https://media.tenor.com/pvC6pnVx754AAAAM/emilia-re-zero.gif",
        "https://media.tenor.com/N5P_gmNE_w0AAAAM/re-zero-bunny.gif",
        "https://media.tenor.com/S0lEz3VPDScAAAAM/re-zero-pack.gif",
        "https://media.tenor.com/CKCQXTH5474AAAAM/ram-rezero.gif",
        "https://media.tenor.com/BN8h8P2137UAAAAM/re-zero-rezero-new-episode.gif",
        "https://media.tenor.com/AZAM4zlj6fEAAAAM/re-zero-rezero-new-episode.gif",
        "https://media.tenor.com/LoG04blAZPgAAAAM/emilia-re-zero.gif",
        "https://media.tenor.com/LwkfcswxPWMAAAAM/emilia-re-zero.gif",
        "https://media.tenor.com/Ks9QR2hAWe4AAAAM/wave-re-zero.gif",
        "https://media.tenor.com/JF8FSAShdIkAAAAM/rem-re-zero.gif",
        "https://media.tenor.com/lMWrYYozYXsAAAAM/petra-leyte-re-zero.gif",
        "https://media.tenor.com/a9TmA0XFEvkAAAAM/otto-re-zero.gif",
        "https://media.tenor.com/FmA4HfQkeNkAAAAM/subaru-blushing.gif",
        "https://media.tenor.com/AJrPXQyoNCQAAAAM/kanokari-anime-wave.gif",
        "https://media.tenor.com/S4VttfqoZ7EAAAAM/kanokari.gif",
        "https://media.tenor.com/lVLQH01Pd1MAAAAM/mami-mami-chan.gif",
        "https://media.tenor.com/0AR8_wkrUZwAAAAM/ruka-sarashina-dance.gif",
        "https://media.tenor.com/X-zCUfMWkVwAAAAM/rent-a-girlfriend.gif",
        "https://media.tenor.com/Uj4Q2JMifngAAAAM/kanokari-cute.gif",
        "https://media.tenor.com/NhzH8I55cooAAAAM/mami-mami-nanami.gif",
        "https://media.tenor.com/O_qnc6aGTLsAAAAM/ruka-sarashina.gif",
        "https://media.tenor.com/evn-uhMws-gAAAAM/depressed-kanokari.gif",
        "https://media.tenor.com/FelFruAglKIAAAAM/tehe-kanokari.gif",
        "https://media.tenor.com/KBa1FWvqq5YAAAAM/korosensei-food.gif",
        "https://media.tenor.com/GizFlj0rxAsAAAAM/marfex-theroosterpl.gif",
        "https://media.tenor.com/xA0mrtcvSY0AAAAM/nisekoi-falselove.gif",
        "https://media.tenor.com/QRGdRr48IToAAAAM/nisekoi-kirisaki.gif",
        "https://media.tenor.com/U8CaM7McGFcAAAAM/chitoge-kirisaki-nisekoi.gif",
        "https://media.tenor.com/VMnk6q_zssMAAAAM/tsugumi-nisekoi.gif",
        "https://media.tenor.com/I7tBO1PIN7wAAAAM/nisekoi.gif",
        "https://media.tenor.com/spXITumbE_YAAAAM/wataten-watashi-ni-tenshi-ga-maiorita.gif",
        "https://media.tenor.com/WAN2hrkXYEQAAAAM/yui-saikawa-tantei-wa-mou.gif",
        "https://media.tenor.com/3rll_IAA-QIAAAAM/tantei-wa-mou-shindeiru-anime.gif",
        "https://media.tenor.com/XWNerRWtvVwAAAAM/siesta-the-detective-is-alredy-dead.gif",
        "https://media.tenor.com/YbDSumvHd6sAAAAM/siesta.gif",
        "https://media.tenor.com/RH-8gQ-wepkAAAAM/yui-saikawa.gif",
        "https://media.tenor.com/NoSvqo-BCGQAAAAM/tanmoshi-siesta.gif",
        "https://media.tenor.com/blaQJlxG7-8AAAAM/jun-suzuki-k-on.gif",
        "https://media.tenor.com/WKuVrtLxxGQAAAAM/hi-hana-bftg.gif",
        "https://media.tenor.com/vAs8iwWPhXsAAAAM/jpnope-keion.gif",
        "https://media.tenor.com/b4q7SEhzRDIAAAAM/yui-kon.gif",
        "https://media.tenor.com/lPVf0QcafhEAAAAM/stop-right-there-buster-nope.gif",
        "https://media.tenor.com/Va9cw2f3jXYAAAAM/ritsu-k-on-k-on.gif",
        "https://media.tenor.com/M2NXbyGZbF0AAAAM/k-on-ritsu.gif",
        "https://media.tenor.com/vCTdyUPZuxIAAAAM/keion-mio.gif",
        "https://media.tenor.com/4s9uLphwstQAAAAM/kise-ryouta-kuroko-no-basket.gif",
        "https://media.tenor.com/dEWXDp-VcjcAAAAM/kuroko.gif",
        "https://media.tenor.com/XbtnuDEJIq8AAAAM/kurokos-basketball-tetsuya-kuroko.gif",
        "https://media.tenor.com/ZPsp8R9BTi0AAAAM/kuroko-ui.gif",
        "https://media.tenor.com/usVwiGktYVwAAAAM/akashi-kuroko-no-basket.gif",
        "https://media.tenor.com/uY5aNx6wfloAAAAM/kuroko-no-basket.gif",
        "https://media.tenor.com/CZb3jSFXlUIAAAAM/spy-x-family-spy-family.gif",
        "https://media.tenor.com/wMi0r9NNRakAAAAM/bocchi-bocchi-the-rock.gif",
        "https://media.tenor.com/ldzbuOgkO-0AAAAM/bocchitherock-bocchi.gif",
        "https://media.tenor.com/BcAehZRbQVAAAAAM/bocchitherock-bocchi.gif",
        "https://media.tenor.com/vD4J7J3JTnUAAAAM/bocchitherock-bocchi.gif",
        "https://media.tenor.com/_AXDpoIGQC8AAAAM/bocchi-bocchi-the-rock.gif",
        "https://media.tenor.com/GnUw9ARx__sAAAAM/bocchi-the-rock-hitori-gotou.gif",
        "https://media.tenor.com/VKg1dYV9kfAAAAAM/kitaikuyo-bocchitherockgif.gif",
        "https://media.tenor.com/0dL_cmsP2YUAAAAM/bocchi-the-rock-kita-ikuyo.gif",
        "https://media.tenor.com/2j9K2DyI7eoAAAAM/bocchi-the-rock-girl-band.gif",
        "https://media.tenor.com/4HUbyxlGYEgAAAAM/bocchi-the-rock-bocchi-the-rock-gif.gif",
        "https://media.tenor.com/F-DX5nEzGgAAAAAM/bocchi-the-rock-kita-ikuyo.gif",
        "https://media.tenor.com/u4hi8fg2M_YAAAAM/no-sleep-spongebob-squarepants.gif",
        "https://media.tenor.com/ujb7n3KxxCwAAAAM/bocchi-bocchi-the-rock.gif",
        "https://media.tenor.com/NmNnFu53lG4AAAAM/bocchi-bocchi-the-rock.gif",
        "https://media.tenor.com/YomyOuGpetMAAAAM/bocchi-bocchi-the-rock.gif",
        "https://media.tenor.com/nDYUMpz_DkEAAAAM/anime.gif",
        "https://media.tenor.com/829fpQqmKDYAAAAM/chika-chika-anime.gif",
    ]
    gif = random.choice(gifs)

    # 埋め込みメッセージを作成
    embed = discord.Embed(
        title="<a:bouncingheart:1104160783778201630> アニメ <a:bouncingheart:1104160783778201630>",
        description=f"<a:bouncingheart:1104160783778201630> {interaction.user.mention} <a:bouncingheart:1104160783778201630>",
        color=0xFFD700,
    )
    embed.set_image(url=gif)

    # 埋め込みメッセージを送信
    await interaction.response.send_message(embed=embed)
    
# ----------------------------------------------------------------------------------------
# 埋め込みメッセージ
@bot.tree.command(name="embedded", description="埋め込みメッセージを作成します")
async def embedded_command(
    interaction: discord.Interaction,
    title: str,
    message: str,
    color: str = "#000000",
    thumbnail_url: str = None,
    image: str = None,
):
    """
    :param title: 埋め込みメッセージのタイトルを指定してください
    :param message: 埋め込みメッセージのメッセージ内容を指定できます　また『,』カンマを使用することで改行ができます
    :param color: 埋め込みメッセージの色を16進数でカラーを選択できます　例 #ff0000 #0000ff #ffff00
    :param thumbnail_url: 画像URLでサムネイルを指定できます
    :param image: 埋め込みメッセージに追加する画像を指定できます
    """

    # カラーコードのチェックを行います
    if not color.startswith("#"):
        error_embed = discord.Embed(title="エラー", color=0xFF0000)
        error_embed.add_field(
            name="",
            value="`color`の引用が不適切です\n`color`は16進数で指定してください。\nまた16進数は以下のサイトを参照してください\n[カラーコード一覧](https://www.colordic.org/)",
        )
        await interaction.response.send_message(embed=error_embed, ephemeral=True)
        return

    # カラーコードを 16 進数から 10 進数に変換します
    color_int = int(color[1:], 16)

    # 埋め込みを作成します
    embed = discord.Embed(title=title, color=color_int)

    # メッセージを埋め込みに追加します
    messages = [line.strip() for line in message.split(",")]
    message_list = [message for message in messages if message]
    message_string = "\n".join(message_list)[:1024]
    embed.add_field(name="\u200b", value=message_string, inline=False)

    # サムネイルを追加します
    if thumbnail_url:
        # URLが画像かどうかをチェックします
        if not thumbnail_url.startswith("http"):
            error_embed = discord.Embed(title="エラー", color=0xFF0000)
            error_embed.add_field(
                name="",
                value="`thumbnail_url`の引用が不適切です\n`thumbnail_url`には画像のURLを入力してください",
            )
            await interaction.response.send_message(embed=error_embed, ephemeral=True)
            return

        response = requests.get(thumbnail_url, stream=True)
        content_type = response.headers.get("Content-Type")
        if not imghdr.what(None, response.content):
            error_embed = discord.Embed(title="エラー", color=0xFF0000)
            error_embed.add_field(
                name="",
                value="`thumbnail_url`の引用が不適切です\n`thumbnail_url`には画像のURLを入力してください",
            )
            await interaction.response.send_message(embed=error_embed, ephemeral=True)
            return
        embed.set_thumbnail(url=thumbnail_url)
        
    # サムネイルを追加します
    if image:
        # URLが画像かどうかをチェックします
        if not image.startswith("http"):
            error_embed = discord.Embed(title="エラー", color=0xFF0000)
            error_embed.add_field(
                name="",
                value="`image`の引用が不適切です\n`image`には画像のURLを入力してください",
            )
            await interaction.response.send_message(embed=error_embed, ephemeral=True)
            return

        response = requests.get(image, stream=True)
        content_type = response.headers.get("Content-Type")
        if not imghdr.what(None, response.content):
            error_embed = discord.Embed(title="エラー", color=0xFF0000)
            error_embed.add_field(
                name="",
                value="`image`の引用が不適切です\n`image`には画像のURLを入力してください",
            )
            await interaction.response.send_message(embed=error_embed, ephemeral=True)
            return

    if image:  # imageが指定されている場合、埋め込みメッセージに画像を追加
        embed.set_image(url=image)

    # 埋め込みを送信します
    await interaction.response.send_message(embed=embed)
    
# ----------------------------------------------------------------------------------------
# BOTに関するフィードバック
class BotFeedbackModal(Modal, title="BOT Feedback"):
    requirement = TextInput(
        label="要件",
        placeholder="例:バグの報告",
        style=discord.TextStyle.short,
        min_length=5,
        max_length=50,
        required=True,
    )
    detail = TextInput(
        label="詳細",
        placeholder="例:バグの再現手順等",
        style=discord.TextStyle.long,
        min_length=15,
        max_length=500,
        required=False,
    )

    async def on_submit(self, ctx: discord.Interaction):
        guild = bot.get_guild(1099541502012702792)  # サーバーIDを指定する
        channel = guild.get_channel(1099551169849860219)  # チャンネルIDを指定する
        user = ctx.user
        user_avatar = user.avatar.url if user.avatar else user.default_avatar.url

        embed = Embed(title="Bot Feedback", color=0xFFD700)
        embed.set_thumbnail(url=user_avatar)
        embed.add_field(name="送信者", value=f"```\n{user.name}#{user.discriminator}\n{user.id}\n```", inline=False)
        embed.add_field(name="要件", value=f"```\n{self.requirement.value}\n```", inline=False)
        embed.add_field(name="詳細", value=f"```\n{self.detail.value if self.detail.value else 'なし'}\n```", inline=False)
        await channel.send(embed=embed)
        
        await ctx.response.send_message(embed=Embed(title="送信完了", description="Botへフィードバックを送信しました", color=0x00FF00), ephemeral=True)

@bot.tree.command(name="bot-feedback", description="開発者にバグやリクエスト等の報告を送信できます")
async def bot_feedback(interaction: discord.Interaction):
    await interaction.response.send_modal(BotFeedbackModal())

# ----------------------------------------------------------------------------------------
# 代理メッセージ
class anonymousdmModal(Modal, title="anonymousdm"):
    user_id = TextInput(
        label="ユーザーID", placeholder="例:01201079229", style=discord.TextStyle.short
    )
    requirement = TextInput(
        label="要件", placeholder="例:警告", style=discord.TextStyle.short
    )
    detail = TextInput(
        label="詳細",
        placeholder="例:次荒らしたらBANします",
        style=discord.TextStyle.long,
        max_length=1000,
    )

    async def on_submit(self, ctx: discord.Interaction):
        try:
            user = await bot.fetch_user(int(self.user_id.value))
            embed = Embed(title="匿名メッセージ", color=0xFFD700)
            embed.add_field(
                name="要件", value=f"\n{self.requirement.value}\n", inline=False
            )
            embed.add_field(name="詳細", value=f"\n{self.detail.value}\n", inline=False)
            await user.send(embed=embed)

            log_server_id = 1099541502012702792  # ログを送信するサーバーID
            log_channel_id = 1099557002423836753  # ログを送信するチャンネルID
            log_server = bot.get_guild(log_server_id)
            if log_server and log_channel_id:
                log_channel = log_server.get_channel(log_channel_id)
                if log_channel:
                    log_embed = Embed(title="匿名メッセージログ", color=0xFFD700)
                    log_embed.add_field(
                        name="要件", value=f"\n{self.requirement.value}\n", inline=False
                    )
                    log_embed.add_field(
                        name="内容", value=f"\n{self.detail.value}\n", inline=False
                    )
                    log_embed.add_field(
                        name="送信者", value=f"\n{ctx.user.mention}\n", inline=True
                    )
                    log_embed.add_field(
                        name="受信者", value=f"\n{user.mention}\n", inline=True
                    )
                    await log_channel.send(embed=log_embed)
                else:
                    raise ValueError(f"ログを送信するチャンネルIDが無効です: {log_channel_id}")

            await ctx.response.send_message(
                embed=Embed(
                    title="送信完了",
                    description=f"{user.mention}にメッセージを送信しました。",
                    color=0x00FF00,
                ),
                ephemeral=True,
            )
        except Exception:
            await ctx.response.send_message(
                embed=Embed(
                    title="エラー",
                    description="ユーザーにメッセージを送信できませんでした。以下の点を確認してください。\nBOTと受信ユーザーがサーバーを共有している\nユーザーIDを正しく入力している",
                    color=0xFF0000,
                ),
                ephemeral=True,
            )

@bot.tree.command(name="anonymous-dm", description="BOTが代理で指定したユーザーのDMにメッセージを送信します")
async def anonymousdm(interaction: discord.Interaction):
    await interaction.response.send_modal(anonymousdmModal())
# ----------------------------------------------------------------------------------------
# パスワードジェネレーター
class TextOptions(Enum):
    BASIC = "basic"
    ALL = "all"


@bot.tree.command(name="password-generator", description="ランダムな英数字記号の含まれたパスワードを生成します")
async def password_generator(
    interaction: discord.Interaction,
    pieces: int = 1,
    word: int = 0,
    text: TextOptions = TextOptions.BASIC,
):
    """
    :param pieces: 作成する文字列の数を指定できます
    :param word: 作成する文字列の文字数を指定できます
    :param text: 作成する文字列の使用可能な記号を指定できます All=全ての記号 basic=!?-_%&@$
    """
    if pieces > 30:
        # `pieces`の引数が30を超えていた場合、エラーメッセージを送信して処理を終了する
        embed = discord.Embed(
            title="エラー",
            description="`pieces`の引用が不正です\n`pieces`は30以下の数字を入力してください",
            color=0xFF0000,
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    if word > 15:
        # `word`の引数が15を超えていた場合、エラーメッセージを送信して処理を終了する
        embed = discord.Embed(
            title="エラー",
            description="`word`の引用が不正です\n`word`は15以下の数字を入力してください",
            color=0xFF0000,
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    if text == TextOptions.BASIC:
        punctuation = "!?-_%&@$"
    elif text == TextOptions.ALL:
        punctuation = string.punctuation
    else:
        # `text`の引数がEnumに定義された値以外の場合、エラーメッセージを送信して処理を終了する
        embed = discord.Embed(
            title="エラー",
            description="`text`の引用が不正です\n`text`は'basic'か'all'を入力してください",
            color=0xFF0000,
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    # ランダムな英数字記号の文字列を生成する
    passwords = []
    for i in range(pieces):
        if word > 0:
            password = "".join(
                random.choices(
                    string.ascii_letters + string.digits + punctuation, k=word
                )
            )
        else:
            password = "".join(
                random.choices(
                    string.ascii_letters + string.digits + punctuation,
                    k=random.randint(7, 12),
                )
            )
        passwords.append(password)

    # 生成したパスワードを埋め込み形式で実行したユーザーにのみ見えるメッセージで返す
    embed = discord.Embed(
        title="以下がランダムに生成されたパスワードです",
        description="```" + "\n".join(passwords) + "```",
        color=0xFFD700,
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)
    
# ----------------------------------------------------------------------------------------
#ブックマーク保存
@bot.tree.command(name="bookmark", description="あなたの保存したい情報を保存する事が出来ます")
async def bookmark(interaction: discord.Interaction, title: str, content: str):
    """
    :param title: ブックマークを管理するタイトルを指定できます
    :param content: ブックマークの内容を指定できます
    """

    if len(title) > 30:
        # タイトルが30文字を超えている場合のエラーメッセージを送信
        embed = discord.Embed(title="エラー", description=f"`title`が長すぎます\n`title`は30文字以内にしてください", color=0xFF0000)
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    if len(content) > 300:
        # コンテンツが300文字を超えている場合のエラーメッセージを送信
        embed = discord.Embed(title="エラー", description=f"`content`が長すぎます\n`content`は300文字以内にしてください", color=0xFF0000)
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    author_id = interaction.user.id
    with open("bookmark.txt", "r", encoding="utf-8") as f:
        for line in f:
            user_id, bookmark_title, _ = line.split(",")
            if user_id == str(author_id) and bookmark_title == title:
                # 同じユーザーが同じタイトルのブックマークを複数作成しようとした場合のエラーメッセージを送信
                embed = discord.Embed(title="エラー", description=f"既に{title}という名前のブックマークが存在します\n`/bookmark-delete`でブックマークを削除するか`title`を変更してください", color=0xFF0000)
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

    with open("bookmark.txt", "a", encoding="utf-8") as f:
        f.write(f"{author_id},{title},{content}\n")

    # 埋め込みメッセージを作成
    embed = discord.Embed(title="ブックマークに追加しました", color=0xFFD700)
    embed.add_field(name="タイトル", value=f"```\n{title}\n```", inline=False)
    embed.add_field(name="コンテンツ", value=f"```\n{content}\n```", inline=False)

    # メッセージを送信
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="bookmark-get", description="あなたが/bookmarkで保存した内容を確認することが出来ます")
async def get_bookmark(interaction: discord.Interaction, title: str):
    """
    :param title: 取得したいブックマークのタイトルを指定できます
    """

    author_id = interaction.user.id
    bookmarks = []

    try:
        with open("bookmark.txt", "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                user_id, bookmark_title, content = line.split(",")
                if user_id == str(author_id) and bookmark_title == title:
                    bookmarks.append(content)
    except FileNotFoundError:
        pass

    # ブックマークが見つからなかった場合のメッセージ
    if not bookmarks:
            embed = discord.Embed(title="エラー", description=f"{title}という名前のブックマークが見つかりませんでした\n`/bookmark`でブックマークを作成するか`/bookmark-list`で作成済みのブックマークを確認してください", color=0xFF0000)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

    # ブックマークを送信するメッセージを作成
    content = "\n".join(bookmarks)
    embed = discord.Embed(title=f"{title}のブックマーク", description=f"```\n{content}\n```", color=0xFFD700)
    await interaction.response.send_message(embed=embed, ephemeral=True)
    
@bot.tree.command(name="bookmark-list", description="自分が保存したブックマークのタイトル一覧を表示します")
async def bookmark_list(interaction: discord.Interaction):
    author_id = interaction.user.id
    bookmark_titles = []

    try:
        with open("bookmark.txt", "r", encoding="utf-8") as f:
            for line in f:
                user_id, bookmark_title, _ = line.split(",")
                if user_id == str(author_id) and bookmark_title not in bookmark_titles:
                    bookmark_titles.append(bookmark_title)
    except FileNotFoundError:
        pass

    # ブックマークが見つからなかった場合のメッセージ
    if not bookmark_titles:
        embed = discord.Embed(title="エラー", description=f"ブックマークが見つかりませんでした\n`/bookmark`でブックマークを作成してください", color=0xFF0000)
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    # ブックマークのタイトル一覧を送信するメッセージを作成
    content = "\n".join(bookmark_titles)
    embed = discord.Embed(title="ブックマークのタイトル一覧", description=f"```\n{content}\n```", color=0xFFD700)
    await interaction.response.send_message(embed=embed, ephemeral=True)
    

@bot.tree.command(name="bookmark-delete", description="ブックマークを削除します")
async def bookmark_delete(interaction: discord.Interaction, title: str):
    """
    :param title: 削除したいブックマークのタイトルを指定できます
    """
    author_id = interaction.user.id
    lines = []
    is_found = False

    try:
        with open("bookmark.txt", "r", encoding="utf-8") as f:
            for line in f:
                user_id, bookmark_title, content = line.split(",")
                if user_id == str(author_id) and bookmark_title == title:
                    is_found = True
                    continue
                lines.append(line)
    except FileNotFoundError:
        pass

    # ブックマークが見つからなかった場合のメッセージ
    if not is_found:
        embed = discord.Embed(title="エラー", description=f"{title}という名前のブックマークが見つかりませんでした\n`/bookmark`でブックマークを作成するか`/bookmark-list`で作成済みのブックマークを確認してください", color=0xFF0000)
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    # ブックマークをファイルに書き込む
    with open("bookmark.txt", "w", encoding="utf-8") as f:
        for line in lines:
            f.write(line)

    # 削除完了メッセージを送信
    embed = discord.Embed(title="ブックマークを削除しました", description=f"{title}を削除しました", color=0x00ff00)
    await interaction.response.send_message(embed=embed, ephemeral=True)
    return

# ----------------------------------------------------------------------------------------
# about
@bot.tree.command(name="about", description="Botの情報を表示します")
async def about(interaction: discord.Interaction):
    guild: discord.Guild = interaction.guild
    bot_user: discord.User = bot.user
    member: discord.Member = guild.get_member(bot_user.id)

    user_count = sum([guild.member_count for guild in bot.guilds])
    invite_url = f"https://discord.com/api/oauth2/authorize?client_id=1099476548295348255&permissions=8&scope=bot "
    support_server_url = "https://discord.gg/Pz5V7enJ"

    embed = discord.Embed(title="Foxvion", color=0xFFD700)
    embed.add_field(
        name="BOT詳細🤖",
        value=f"`Developer`:[Lemon](https://discord.com/users/1099540620848156775) & [Koala](https://discord.com/users/967347570013790258)\n`ping`:{round(bot.latency * 1000)}ms\n`RAM`:{psutil.Process().memory_info().rss / 1024 ** 2:.2f}MB",
        inline=False,
    )
    embed.add_field(
        name="統計📊",
        value=f"`User`: {user_count}\n`Guilds`: {len(bot.guilds)}",
        inline=False,
    )
    embed.add_field(
        name="リンク🔗",
        value=f"`Invite`:[招待する](https://discord.com/api/oauth2/authorize?client_id=1099476548295348255&permissions=8&scope=bot)",
        inline=False,
    )
    embed.set_thumbnail(url=bot_user.avatar.url)

    view = discord.ui.View()
    invite_button = discord.ui.Button(
        label="サーバーに招待する",
        url="https://discord.com/api/oauth2/authorize?client_id=1099476548295348255&permissions=8&scope=bot",
    )
    view.add_item(invite_button)

    await interaction.response.send_message(embed=embed, view=view)

# ----------------------------------------------------------------------------------------
# userinfo
@bot.tree.command(name="user-info", description="ユーザー情報を表示します")
async def userinfo(interaction: discord.Interaction, user: discord.Member):
    """
    :param user: ユーザーを指定できます
    """
    account_created_at = f"<t:{int(user.created_at.timestamp())}:F>"
    joined_at = f"<t:{int(user.joined_at.timestamp())}:F>"

    embed = discord.Embed(title=f"{user.name}さんの情報", color=0xFFD700)
    if user.avatar:
        embed.set_thumbnail(url=user.avatar.url)
    else:
        embed.set_thumbnail(url=user.default_avatar.url)

    embed.description = f"{user.mention}｜`{user.id}`\n\nアイコンURL: [ここをクリック]({user.avatar.url if user.avatar else user.default_avatar.url})📷"
    embed.add_field(name="アカウント作成日時📅", value=account_created_at, inline=True)
    embed.add_field(name="サーバー参加日時📅", value=joined_at, inline=True)
    embed.add_field(name="ロール🌀", value="\n".join([role.mention for role in user.roles[1:]]) or "なし", inline=False)
    embed.add_field(name="BOT🤖", value="はい" if user.bot else "いいえ", inline=False)

    await interaction.response.send_message(embed=embed)

# ----------------------------------------------------------------------------------------
# guildinfo
@bot.tree.command(name="guild-info", description="サーバー情報を表示します")
async def guildinfo(interaction: discord.Interaction):
    guild = interaction.guild

    created_at = int(guild.created_at.timestamp())
    members_count = len([m for m in guild.members if not m.bot])
    bots_count = len([m for m in guild.members if m.bot])
    text_channels_count = len(guild.text_channels)
    voice_channels_count = len(guild.voice_channels)
    roles = [role for role in guild.roles if not role.is_bot_managed()]
    roles_count = len(roles)
    emojis_count = len(guild.emojis)
    stickers_count = len(await guild.fetch_stickers())

    bans_count = 0
    async for ban in guild.bans():
        bans_count += 1

    embed = discord.Embed(title=f"{guild.name}の情報", color=0xFFD700)
    embed.add_field(name="🐟サーバーネーム", value=f"`{guild.name}`", inline=True)
    embed.add_field(name=":keyboard:サーバーID", value=f"`{guild.id}`", inline=True)
    embed.add_field(name="📅サーバー作成日", value=f"<t:{created_at}:F>", inline=True)
    embed.add_field(name="👤参加しているユーザー数", value=f"`{members_count}`", inline=True)
    embed.add_field(name="🤖参加しているBOT数", value=f"`{bots_count}`", inline=True)
    embed.add_field(name="<a:yellowcrown:1104526607135281173>オーナー", value=f"{guild.owner.mention}", inline=False)
    embed.add_field(name="<a:BAN:1104526341459673088>BANしているユーザー数", value=f"`{bans_count}`", inline=False)
    embed.add_field(name="<:threadg:1104527151182647316>テキストチャンネル数", value=f"`{text_channels_count}`", inline=True)
    embed.add_field(name="<:voiceg:1104527139157585920>ボイスチャンネル数", value=f"`{voice_channels_count}`", inline=True)

    # ロール一覧を追加
    roles_text = ", ".join([f"{role.mention}" for role in roles])
    embed.add_field(name="🌀ロール一覧", value=roles_text, inline=False)

    # BOTロール一覧を追加
    bot_roles = [role for role in guild.roles if role.is_bot_managed()]
    if bot_roles:
        bot_roles_text = ", ".join([f"{role.mention}" for role in bot_roles])
        embed.add_field(name="🤖BOTロール一覧", value=bot_roles_text, inline=False)

    embed.add_field(name="<:bronzeribbon:1104527901069680640>絵文字数", value=f"`{emojis_count}`", inline=True)
    embed.add_field(name="<:goldribbon:1104527897164791898>スタンプ数", value=f"`{stickers_count}`", inline=True)
    guild = interaction.guild
    if guild.icon:
        icon_url = guild.icon.url
        embed.set_thumbnail(url=icon_url)
    else:
         # アイコンが設定されていない場合、デフォルトの画像をサムネイルとして使用
        default_icon_url = "https://cdn.discordapp.com/attachments/1101747131519348856/1108622056343490581/image.png"
        embed.set_thumbnail(url=default_icon_url)

    await interaction.response.send_message(embed=embed)

# ----------------------------------------------------------------------------------------
# チャンネルinfo
@bot.tree.command(name="channel-info", description="指定したチャンネルの情報を表示します")
async def get_channel(
    interaction: discord.Interaction,
    channel: Union[discord.TextChannel, discord.VoiceChannel],
):
    """
    :param channel: 情報を取得したいチャンネルを選択できます
    """
    if isinstance(channel, discord.TextChannel):
        # テキストチャンネルの場合
        embed = discord.Embed(
            title="チャンネル情報",
            description=f"チャンネル:{channel.mention}",
            color=0xFFD700,
        )
        embed.add_field(name="チャンネルの名前", value=f"```{channel.name}```", inline=False)
        embed.add_field(
            name="トピック",
            value=f"```{channel.topic}```" if channel.topic else "なし",
            inline=False,
        )
        embed.add_field(
            name="低速モード",
            value=f"{channel.slowmode_delay}秒" if channel.slowmode_delay else "なし",
            inline=False,
        )
        embed.add_field(
            name="年齢制限", value="あり" if channel.is_nsfw() else "なし", inline=False
        )
        embed.add_field(
            name="アナウンスチャンネル", value="はい" if channel.is_news() else "いいえ", inline=False
        )
        embed.add_field(name="権限", value=f"```{channel.overwrites}```", inline=False)
        guild = interaction.guild
        if guild.icon:
            icon_url = guild.icon.url
            embed.set_thumbnail(url=icon_url)
        else:
             # アイコンが設定されていない場合、デフォルトの画像をサムネイルとして使用
            default_icon_url = "https://cdn.discordapp.com/attachments/1101747131519348856/1108622056343490581/image.png"
            embed.set_thumbnail(url=default_icon_url)

    elif isinstance(channel, discord.VoiceChannel):
        # ボイスチャンネルの場合
        embed = discord.Embed(
            title="Get Channel",
            description=f"チャンネル:{channel.mention}",
            color=0xFFD700,
        )
        embed.add_field(name="チャンネルの名前", value=f"```{channel.name}```", inline=False)
        embed.add_field(
            name="ビットレート", value=f"{channel.bitrate/1000}kbps", inline=False
        )
        embed.add_field(
            name="人数制限",
            value=f"{channel.user_limit}人" if channel.user_limit else "なし",
            inline=False,
        )
        embed.add_field(
            name="年齢制限", value="あり" if channel.is_nsfw() else "なし", inline=False
        )
        embed.add_field(name="権限", value=f"```{channel.overwrites}```", inline=False)
        guild = interaction.guild
        if guild.icon:
            icon_url = guild.icon.url
            embed.set_thumbnail(url=icon_url)
        else:
             # アイコンが設定されていない場合、デフォルトの画像をサムネイルとして使用
            default_icon_url = "https://cdn.discordapp.com/attachments/1101747131519348856/1108622056343490581/image.png"
            embed.set_thumbnail(url=default_icon_url)

    await interaction.response.send_message(embed=embed)

# ----------------------------------------------------------------------------------------
# カテゴリーinfo
@bot.tree.command(name="category-info", description="指定したカテゴリーの詳細を表示します")
async def get_category(
    interaction: discord.Interaction, category: discord.CategoryChannel
):
    """
    :param category: 情報を取得したいカテゴリーを選択できます
    """
    embed = discord.Embed(
        title="カテゴリー情報",
        description=f"カテゴリー:`{category.name}`",
        color=0xFFD700,
    )
    embed.add_field(name="カテゴリーの名前", value=f"```\n{category.name}\n```")
    permissions = "\n".join(
        f"{perm[0]}: {perm[1].pair()} " for perm in category.overwrites.items()
    )
    embed.add_field(name="権限", value=f"```\n{permissions}\n```", inline=False)
    guild = interaction.guild
    if guild.icon:
        icon_url = guild.icon.url
        embed.set_thumbnail(url=icon_url)
    else:
         # アイコンが設定されていない場合、デフォルトの画像をサムネイルとして使用
        default_icon_url = "https://cdn.discordapp.com/attachments/1101747131519348856/1108622056343490581/image.png"
        embed.set_thumbnail(url=default_icon_url)
    await interaction.response.send_message(embed=embed)
    
# ----------------------------------------------------------------------------------------
# 管理者用コマンド
# ボイスログ
CALL_LOG_FILE = "call-log.txt"

@bot.tree.command(name="call-log",description="ボイスチャンネルの通話ログを出力するチャンネルを指定します。")
async def call_log(interaction: discord.Interaction, channel: discord.TextChannel):
    """
    :param channel: 通話のログの出力先を指定できます
    """
    # コマンドを使用したユーザーがチャンネルの管理権限を持っていることを確認
    if not interaction.channel.permissions_for(interaction.user).manage_channels:
        # 管理者権限を持っていない場合、エラーメッセージを送信
        error_embed = discord.Embed(
            title="エラー",
            description="権限を確認出来ませんでした\n このコマンドを実行するには管理者権限が必要です",
            color=0xFF0000,
        )
        await interaction.response.send_message(embed=error_embed, ephemeral=True)
        return
    
    guild_id = channel.guild.id
    with open(CALL_LOG_FILE, "r+") as f:
        lines = f.readlines()
        f.seek(0)
        for line in lines:
            server_id, channel_id = line.strip().split(",")
            if int(server_id) != guild_id:
                f.write(line)
        f.truncate()
        f.write(f"{guild_id},{channel.id}\n")
    embed = discord.Embed(
        title="通話ログ設定完了",
        description=f"通話ログの出力先を{channel.mention}に設定しました。",
        color=0x00FF00,
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)


async def get_voice_log_channel(guild_id):
    voice_log_channel_id = None
    if os.path.exists(CALL_LOG_FILE):
        with open(CALL_LOG_FILE, "r") as f:
            lines = f.readlines()
            for line in lines:
                server_id, channel_id = line.strip().split(",")
                if int(server_id) == guild_id:
                    voice_log_channel_id = int(channel_id)
                    break
    return voice_log_channel_id

@bot.event
async def on_voice_state_update(member, before, after):
    if before.channel != after.channel:
        if after.channel:
            voice_log_channel_id = await get_voice_log_channel(member.guild.id)
            if voice_log_channel_id is not None:
                voice_log_channel = member.guild.get_channel(voice_log_channel_id)
                if voice_log_channel is not None:
                    time_str = f"<t:{int(datetime.now().timestamp())}:F>"
                    embed = discord.Embed(
                        title="通話参加ログ",
                        description=f"ユーザー:{member.mention}\n\nユーザーID:`{member.id}`\n\nチャンネル:{after.channel.mention}\n\n時間: {time_str}",
                        color=0x00FF00,
                    )
                    if member.avatar:
                        embed.set_thumbnail(url=str(member.avatar.url))
                    else:
                        embed.set_thumbnail(url=str(member.default_avatar.url))
                    await voice_log_channel.send(embed=embed)
        elif before.channel:
            voice_log_channel_id = await get_voice_log_channel(member.guild.id)
            if voice_log_channel_id is not None:
                voice_log_channel = member.guild.get_channel(voice_log_channel_id)
                if voice_log_channel is not None:
                    time_str = f"<t:{int(datetime.now().timestamp())}:F>"
                    embed = discord.Embed(
                        title="通話退出ログ",
                        description=f"ユーザー:{member.mention}\n\nユーザーID:`{member.id}`\n\nチャンネル:{before.channel.mention} \n\n時間: {time_str}",
                        color=0xFF0000,
                    )
                    if member.avatar:
                        embed.set_thumbnail(url=str(member.avatar.url))
                    else:
                        embed.set_thumbnail(url=str(member.default_avatar.url))
                    await voice_log_channel.send(embed=embed)
                    
#call-log-delete
@bot.tree.command(name="call-log-delete", description="call-logの設定を削除します")
async def call_log_delete(interaction: discord.Interaction):
    # コマンドを使用したユーザーがチャンネルの管理権限を持っていることを確認
    if not interaction.channel.permissions_for(interaction.user).manage_channels:
        # 管理者権限を持っていない場合、エラーメッセージを送信
        error_embed = discord.Embed(
            title="エラー",
            description="権限を確認出来ませんでした\n このコマンドを実行するには管理者権限が必要です",
            color=0xFF0000,
        )
        await interaction.response.send_message(embed=error_embed, ephemeral=True)
        return
    guild_id = interaction.guild.id
    with open(CALL_LOG_FILE, "r+") as f:
        lines = f.readlines()
        f.seek(0)
        for line in lines:
            server_id, _ = line.strip().split(",")
            if int(server_id) != guild_id:
                f.write(line)
        f.truncate()

    embed = discord.Embed(
        title="call-logの設定を削除しました",
        description="正常に削除しました",
        color=0x00FF00,
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)

# ----------------------------------------------------------------------------------------
# 削除ログ
# 設定情報を読み込む関数
def load_settings():
    settings = {}
    try:
        with open("delete-log.txt", "r") as f:
            for line in f:
                server_id, channel_id = line.strip().split(",")
                settings[int(server_id)] = int(channel_id)
    except FileNotFoundError:
        pass
    return settings

# 設定情報を保存する関数
def save_settings(settings):
    with open("delete-log.txt", "w") as f:
        for server_id, channel_id in settings.items():
            f.write(f"{server_id},{channel_id}\n")

settings = load_settings()

@bot.tree.command(name="delete-log", description="メッセージを削除した際のログの出力先を指定出来ます")
async def delete_log(interaction: discord.Interaction, channel: discord.TextChannel):
    """
    :param channel: メッセージの削除ログの出力先を指定できます
    """
    # コマンドを使用したユーザーがチャンネルの管理権限を持っていることを確認
    if not interaction.channel.permissions_for(interaction.user).manage_channels:
        # 管理者権限を持っていない場合、エラーメッセージを送信
        error_embed = discord.Embed(
            title="エラー",
            description="権限を確認出来ませんでした\n このコマンドを実行するには管理者権限が必要です",
            color=0xFF0000,
        )
        await interaction.response.send_message(embed=error_embed, ephemeral=True)
        return

    settings[channel.guild.id] = channel.id
    save_settings(settings)
    embed = discord.Embed(
        title="削除ログを設定しました",
        description=f"削除ログの出力先を{channel.mention}に指定しました",
        color=0x00FF00,
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.event
async def on_message_delete(message):
    if message.guild.id in settings:
        del_log_channel_id = settings[message.guild.id]
        del_log_channel = message.guild.get_channel(del_log_channel_id)
        if del_log_channel is not None:
            now = datetime.now()
            time_str = f"<t:{int(message.created_at.timestamp())}:F>"
            delete_time_str = f"<t:{int(datetime.now().timestamp())}:F>"
            user_info = f"ユーザー: {message.author.mention}\nユーザーID: `{message.author.id}`"
            message_info = f"メッセージ送信時間: {time_str}\nメッセージ削除時間: {delete_time_str}\nメッセージ送信チャンネル:{message.channel.mention}"
            content = f"{message.content}"
            
            embed = discord.Embed(
                title="メッセージ削除ログ",
                description=user_info,
                color=0xFF0000,
            )
            if message.author.avatar:
                embed.set_thumbnail(url=str(message.author.avatar.url))
            else:
                default_avatar_url = message.author.default_avatar.with_format("png")
                embed.set_thumbnail(url=str(default_avatar_url))
            embed.add_field(name="メッセージ情報", value=message_info, inline=False)
            
            # メッセージ内容の設定
            if message.embeds:
                embed.add_field(name="メッセージ内容", value="```以下の埋め込みメッセージ```", inline=False)
            else:
                embed.add_field(name="メッセージ内容", value=content, inline=False)
            
            # 画像、動画、GIFのコンテンツが含まれている場合の処理
            attachments = message.attachments
            if attachments:
                image_count = 1
                video_count = 1
                gif_count = 1
                other_content = []
                for attachment in attachments:
                    file_type = attachment.filename.split(".")[-1]
                    if file_type in ["png", "jpg", "jpeg", "gif"]:
                        other_content.append(f"画像{image_count}: [ここをクリック]({attachment.url})")
                        image_count += 1
                    elif file_type in ["mp4", "mov", "avi"]:
                        other_content.append(f"動画{video_count}: [ここをクリック]({attachment.url})")
                        video_count += 1
                    elif file_type == "gif":
                        other_content.append(f"GIF{gif_count}: [ここをクリック]({attachment.url})")
                        gif_count += 1
                if other_content:
                    embed.add_field(name="その他のコンテンツ", value="\n".join(other_content), inline=False)
            
            await del_log_channel.send(embed=embed)
            
            # 埋め込みメッセージが削除された場合の処理
            if message.embeds:
                for embed in message.embeds:
                    await del_log_channel.send(embed=embed)
                    
#delete-log-delete
@bot.tree.command(name="delete-log-delete", description="delete-logの設定を削除します")
async def delete_log_delete(interaction: discord.Interaction):
    # コマンドを使用したユーザーがチャンネルの管理権限を持っていることを確認
    if not interaction.channel.permissions_for(interaction.user).manage_channels:
        # 管理者権限を持っていない場合、エラーメッセージを送信
        error_embed = discord.Embed(
            title="エラー",
            description="権限を確認出来ませんでした\n このコマンドを実行するには管理者権限が必要です",
            color=0xFF0000,
        )
        await interaction.response.send_message(embed=error_embed, ephemeral=True)
        return
    server_id = interaction.guild.id
    if server_id in settings:
        del settings[server_id]
        save_settings(settings)
        embed = discord.Embed(
            title="delete-logの設定を削除しました",
            description="正常に削除しました",
            color=0x00ff00,
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
    else:
        embed = discord.Embed(
            title="delete-logの設定を削除しました",
            description="正常に削除しました",
            color=0x00ff00,
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    
# ----------------------------------------------------------------------------------------
# サーバー参加ログ
@bot.tree.command(
    name="welcome-log",
    description="サーバーに参加時に送信するメッセージを作成できます",
)
async def welcome_log(
    interaction: discord.Interaction,
    channel: discord.TextChannel,
    title: str = None,
    message: str = None,
    image: str = None,
):
    """
    :param channel: ログを出力するチャンネルを指定してください
    :param title: メッセージのタイトルを指定できます
    :param message: メッセージの内容を指定できます　また『,』カンマを使用することで改行できます
    :param image: 埋め込みメッセージに画像またはGIFを追加できます　画像またはGIFのURLを入力してください
    """
    # コマンドを使用したユーザーがチャンネルの管理権限を持っていることを確認
    if not interaction.channel.permissions_for(interaction.user).manage_channels:
        # 管理者権限を持っていない場合、エラーメッセージを送信
        error_embed = discord.Embed(
            title="エラー",
            description="権限を確認出来ませんでした\n このコマンドを実行するには管理者権限が必要です",
            color=0xFF0000,
        )
        await interaction.response.send_message(embed=error_embed, ephemeral=True)
        return

    if title is None:
        title = f"{channel.guild.name}へようこそ！！"
    if message is None:
        message = f"{channel.guild.name}に参加しました"

    # message内のカンマを改行文字に変換
    message = message.replace(",", "\n")

    error_message = None
    if image is not None:
        try:
            response = requests.get(image)
            content_type = response.headers.get("Content-Type")
            if "image" not in content_type:
                error_message = f"`image`には画像またはGIFのURLを入力してください"
        except:
            error_message = f"`image`には画像またはGIFのURLを入力してください"

    if error_message is not None:
        embed = discord.Embed(
            title="エラー",
            description=f"`image`の引用が不適切です\n{error_message}",
            color=0xFF0000,
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    # welcome-log.txtに情報を書き込む
    server_id = str(channel.guild.id)
    with open("welcome-log.txt", "r") as f:
        data = f.readlines()
    with open("welcome-log.txt", "w") as f:
        for line in data:
            # 既に同じサーバーの情報があれば上書き
            if json.loads(line)["server_id"] != server_id:
                f.write(line)
        welcome_log_data = {
            "server_id": server_id,
            "channel_id": str(channel.id),
            "title": title,
            "message": message,
            "image": image,
        }
        f.write(json.dumps(welcome_log_data) + "\n")

    embed = discord.Embed(
        title="参加ログを設定しました",
        description=f"参加ログの出力先を{channel.mention}に指定しました",
        color=0x00FF00,
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.event
async def on_member_join(member):
    guild_id = member.guild.id
    with open("welcome-log.txt", "r") as f:
        for line in f:
            welcome_log_data = json.loads(line)
            if welcome_log_data["server_id"] == str(guild_id):
                welcome_log_channel = member.guild.get_channel(int(welcome_log_data["channel_id"]))
                if welcome_log_channel is not None:
                    await asyncio.sleep(1)  # 1秒待つ
                    time_str = f"<t:{int(member.joined_at.timestamp())}:F>"
                    embed = discord.Embed(title=f"{member.guild.name}へようこそ！！", color=0x00FF00)
                    embed.add_field(name="ユーザー", value=f"{member.mention}", inline=False)
                    embed.add_field(name="時間", value=f"{time_str}", inline=False)
                    embed.add_field(name="\u200b", value=f"\n", inline=False)
                    embed.add_field(
                        name=welcome_log_data["title"],
                        value=welcome_log_data["message"],
                        inline=False,
                    )
                    if welcome_log_data["image"] is not None:
                        embed.set_image(url=welcome_log_data["image"])
                    if member.avatar:
                        embed.set_thumbnail(url=member.avatar.url)
                    else:
                        embed.set_thumbnail(url=member.default_avatar.url)
                    await welcome_log_channel.send(embed=embed)
                    await welcome_log_channel.send(f"{member.mention}")
                    
#welcome-log-delete
@bot.tree.command(name="welcome-log-delete",description="welcome-logの設定を削除します",)
async def welcome_log_delete(interaction: discord.Interaction):
    # コマンドを使用したユーザーがチャンネルの管理権限を持っていることを確認
    if not interaction.channel.permissions_for(interaction.user).manage_channels:
        # 管理者権限を持っていない場合、エラーメッセージを送信
        error_embed = discord.Embed(
            title="エラー",
            description="権限を確認出来ませんでした\n このコマンドを実行するには管理者権限が必要です",
            color=0xFF0000,
        )
        await interaction.response.send_message(embed=error_embed, ephemeral=True)
        return
    guild_id = str(interaction.guild.id)
    lines = []
    deleted = False

    with open("welcome-log.txt", "r") as f:
        for line in f:
            welcome_log_data = json.loads(line)
            if welcome_log_data["server_id"] == guild_id:
                deleted = True
            else:
                lines.append(line)

    if deleted:
        with open("welcome-log.txt", "w") as f:
            for line in lines:
                f.write(line)

        embed = discord.Embed(
            title="welcome-logの設定を削除しました",
            description="正常に削除しました",
            color=0x00FF00,
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
    else:
        embed = discord.Embed(
            title="welcome-logの設定を削除しました",
            description="正常に削除しました",
            color=0x00FF00,
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

# ----------------------------------------------------------------------------------------
# サーバー退出メッセージ
@bot.tree.command(
    name="goodbye-log",
    description="サーバー退出時に送信するメッセージを作成できます",
)
async def goodbye_log(
    interaction: discord.Interaction,
    channel: discord.TextChannel,
    title: str = None,
    message: str = None,
    image: str = None,
):
    """
    :param channel: ログを出力するチャンネルを指定してください
    :param title: メッセージのタイトルを指定できます
    :param message: メッセージの内容を指定できます　また『,』カンマを使用することで改行できます
    :param image: 埋め込みメッセージに画像またはGIFを追加できます　画像またはGIFのURLを入力してください
    """
    # コマンドを使用したユーザーがチャンネルの管理権限を持っていることを確認
    if not interaction.channel.permissions_for(interaction.user).manage_channels:
        # 管理者権限を持っていない場合、エラーメッセージを送信
        error_embed = discord.Embed(
            title="エラー",
            description="権限を確認出来ませんでした\n このコマンドを実行するには管理者権限が必要です",
            color=0xFF0000,
        )
        await interaction.response.send_message(embed=error_embed, ephemeral=True)
        return

    if title is None:
        title = f"さようなら"
    if message is None:
        message = f"{channel.guild.name}から退出しました"

    # message内のカンマを改行文字に変換
    message = message.replace(",", "\n")

    error_message = None
    if image is not None:
        try:
            response = requests.get(image)
            content_type = response.headers.get("Content-Type")
            if "image" not in content_type:
                error_message = f"`image`には画像またはGIFのURLを入力してください"
        except:
            error_message = f"`image`には画像またはGIFのURLを入力してください"

    if error_message is not None:
        embed = discord.Embed(
            title="エラー",
            description=f"`image`の引用が不適切です\n{error_message}",
            color=0xFF0000,
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    # goodbye-log.txtに情報を書き込む
    server_id = str(channel.guild.id)
    with open("goodbye-log.txt", "r") as f:
        data = f.readlines()
    with open("goodbye-log.txt", "w") as f:
        for line in data:
            # 既に同じサーバーの情報があれば上書き
            if json.loads(line)["server_id"] != server_id:
                f.write(line)
        goodbye_log_data = {
            "server_id": server_id,
            "channel_id": str(channel.id),
            "title": title,
            "message": message,
            "image": image,
        }
        f.write(json.dumps(goodbye_log_data) + "\n")

    embed = discord.Embed(
        title="退出ログを設定しました",
        description=f"退出ログの出力先を{channel.mention}に指定しました",
        color=0x00FF00,
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.event
async def on_member_remove(member):
    guild_id = member.guild.id
    with open("goodbye-log.txt", "r") as f:
        for line in f:
            goodbye_log_data = json.loads(line)
            if goodbye_log_data["server_id"] == str(guild_id):
                goodbye_log_channel = member.guild.get_channel(int(goodbye_log_data["channel_id"]))
                if goodbye_log_channel is not None:
                    await asyncio.sleep(1)  # 1秒待つ
                    time_str = f"<t:{int(datetime.now().timestamp())}:F>"
                    embed = discord.Embed(title=f"さようなら", color=0xFF0000)
                    embed.add_field(name="ユーザー", value=f"{member.mention}", inline=False)
                    embed.add_field(name="時間", value=f"{time_str}", inline=False)
                    embed.add_field(name="\u200b", value=f"\n", inline=False)
                    embed.add_field(
                        name=goodbye_log_data["title"],
                        value=goodbye_log_data["message"],
                        inline=False,
                    )
                    if goodbye_log_data["image"] is not None:
                        embed.set_image(url=goodbye_log_data["image"])
                    if member.avatar:
                        embed.set_thumbnail(url=member.avatar.url)
                    else:
                        embed.set_thumbnail(url=member.default_avatar.url)
                    await goodbye_log_channel.send(embed=embed)
                    await goodbye_log_channel.send(f"{member.mention}")
                    
#goodbye-log-delete
@bot.tree.command(name="goodbye-log-delete",description="goodbye-logの設定を削除します",)
async def welcome_log_delete(interaction: discord.Interaction):
    # コマンドを使用したユーザーがチャンネルの管理権限を持っていることを確認
    if not interaction.channel.permissions_for(interaction.user).manage_channels:
        # 管理者権限を持っていない場合、エラーメッセージを送信
        error_embed = discord.Embed(
            title="エラー",
            description="権限を確認出来ませんでした\n このコマンドを実行するには管理者権限が必要です",
            color=0xFF0000,
        )
        await interaction.response.send_message(embed=error_embed, ephemeral=True)
        return
    guild_id = str(interaction.guild.id)
    lines = []
    deleted = False

    with open("goodbye-log.txt", "r") as f:
        for line in f:
            welcome_log_data = json.loads(line)
            if welcome_log_data["server_id"] == guild_id:
                deleted = True
            else:
                lines.append(line)

    if deleted:
        with open("goodbye-log.txt", "w") as f:
            for line in lines:
                f.write(line)

        embed = discord.Embed(
            title="goodbye-logの設定を削除しました",
            description="正常に削除しました",
            color=0x00FF00,
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
    else:
        embed = discord.Embed(
            title="goodbye-logの設定を削除しました",
            description="正常に削除しました",
            color=0x00FF00,
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

# ----------------------------------------------------------------------------------------
# ログの削除
@bot.tree.command(name="nuke", description="チャンネルのログを一括削除します")
async def nuke(
    interaction: discord.Interaction,
    channel: Union[discord.TextChannel, discord.VoiceChannel],
):
    """
    :param channel: ログを削除するチャンネルを指定できます
    """
    # コマンドを使用したユーザーがチャンネルの管理権限を持っていることを確認
    if not interaction.channel.permissions_for(interaction.user).manage_channels:
        # 管理者権限を持っていない場合、エラーメッセージを送信
        error_embed = discord.Embed(
            title="エラー",
            description="権限を確認出来ませんでした\n このコマンドを実行するには管理者権限が必要です",
            color=0xFF0000,
        )
        await interaction.response.send_message(embed=error_embed, ephemeral=True)
        return

    category = channel.category
    position = channel.position
    overwrites = channel.overwrites
    channel_name = channel.name

    # チャンネルの削除
    await channel.delete()

    # 新しいチャンネルの作成
    new_channel = await category.create_text_channel(
        channel_name, position=position, overwrites=overwrites
    )

    # 完了メッセージの送信
    embed = discord.Embed(
        title="<a:nuke47:1104539194702975106>Nuke<a:nuke47:1104539194702975106>",
        description=f"{new_channel.mention}のログを正常に削除しました\n\n良かったらほかのサーバーにも招待してね",
        color=0xFFD700,
    )

    # フッターを付けたメッセージを作成
    embed.set_thumbnail(url=bot.user.display_avatar.url)
    embed.set_footer(text="Foxvion")
    view = discord.ui.View()
    button = discord.ui.Button(
        label="サーバーに招待する",
        url="https://discord.com/api/oauth2/authorize?client_id=1099476548295348255&permissions=8&scope=bot",
    )
    view.add_item(button)
    await interaction.response.send_message(embed=embed, view=view)

    # 新しいチャンネルにもメッセージを送信
    new_embed = discord.Embed(
        title="<a:nuke47:1104539194702975106>Nuke<a:nuke47:1104539194702975106>",
        description=f"{new_channel.mention}のログを{interaction.user.mention}が削除しました\n\n良かったらほかのサーバーにも招待してね",
        color=0xFFD700,
    )

    # フッターを付けたメッセージを作成
    new_embed.set_thumbnail(url=bot.user.display_avatar.url)
    new_embed.set_footer(text="Foxvion")
    view = discord.ui.View()
    button = discord.ui.Button(
        label="サーバーに招待する",
        url="https://discord.com/api/oauth2/authorize?client_id=1099476548295348255&permissions=8&scope=bot",
    )
    view.add_item(button)
    await new_channel.send(embed=new_embed, view=view)


# ----------------------------------------------------------------------------------------
# パージ
@bot.tree.command(name="purge", description="指定された数のメッセージを削除します")
async def purge(interaction: discord.Interaction, amount: int):
    """
    :param amount: 削除するメッセージ件数を指定できます
    """
    
    if amount > 500:
        # エラーメッセージを送信
        embed = discord.Embed(
            title="エラー",
            description="`amount`の引用が不正です\n`amount`は1～500の数字を入力してください。",
            color=0xFF0000,
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    # 1. 応答メッセージを送信
    await interaction.response.send_message(f"{amount}件のメッセージを削除します", ephemeral=True)

    # 2. 指定された数のメッセージを削除
    await asyncio.sleep(0.1)
    channel = interaction.channel
    await channel.purge(limit=amount + 1, before=interaction.message)

    # 3. ボタンを追加したメッセージを送信
    bot_icon_url = bot.user.avatar.url
    embed = discord.Embed(
        title="<:Wrong89:1104539836192403466>Purge<:Wrong89:1104539836192403466>",
        description=f"{amount}件のメッセージを削除しました。\n\n良かったらほかのサーバーにも招待してね",
        color=0xFFD700,
    ).set_thumbnail(url=bot_icon_url)
    view = discord.ui.View()
    button = discord.ui.Button(
        label="サーバーに招待する",
        url="https://discord.com/api/oauth2/authorize?client_id=1099476548295348255&permissions=8&scope=bot",
    )
    view.add_item(button)
    await interaction.channel.send(embed=embed, view=view)
    
# ----------------------------------------------------------------------------------------
# チケット
# サーバーごとのユーザーごとのチャンネル数を保持する辞書
server_user_channel_counts = {}

# サーバーごとのmax_channelsを保持する辞書
server_max_channels = {}

@bot.tree.command(name="ticket", description="チケットを作成します")
async def create_ticket(
    interaction: discord.Interaction,
    title: str = None,
    description: str = None,
    color: str = None,
    label: str = None,
    welcome: str = None,
    customer: discord.Role = None,
    max_channels: int = None,
    category: discord.CategoryChannel = None,
    image: str = None,  
):
    """
    :param title: タイトルを変更できます
    :param description: メッセージを変更できます また , を使用することで改行できます
    :param color: カラーを選択できます 指定は16進数で行ってください　例 #000000 #f0f8ff #ffff00
    :param label: ボタンに表示するメッセージを変更できます
    :param welcome: チケット作成時に送信されるメッセージを指定できます また , を使用することで改行できます
    :param customer: チケットを閲覧できるロールを指定できます
    :param max_channels: チケットの作成できる上限を指定できます　またサーバー内のチケット全てに反映されます
    :param category: チケットを作成するカテゴリーを選択できます　選択しない場合はカテゴリー外に作成されます
    :param image: チケットに追加する画像を指定できます
    """

    # コマンドを使用したユーザーがチャンネルの管理権限を持っていることを確認
    if not interaction.channel.permissions_for(interaction.user).manage_channels:
        # 管理者権限を持っていない場合、エラーメッセージを送信
        error_embed = discord.Embed(
            title="エラー",
            description="権限を確認できませんでした。このコマンドを実行するには管理者権限が必要です。",
            color=0xFF0000,
        )
        await interaction.response.send_message(embed=error_embed, ephemeral=True)
        return

    max_channels = max_channels or float("inf")

    # サーバーごとのmax_channelsを取得する
    server_id = interaction.guild.id
    server_max_channels.setdefault(server_id, float("inf"))
    max_channels = min(max_channels, server_max_channels[server_id])

    # サーバーごとのユーザーごとのチャンネル数を取得する
    server_user_channel_counts.setdefault(server_id, {})
    user_id = interaction.user.id
    user_channel_counts = server_user_channel_counts[server_id]
    user_channel_counts.setdefault(user_id, 0)
    
    # サムネイルを追加します
    if image:
        # URLが画像かどうかをチェックします
        if not image.startswith("http"):
            error_embed = discord.Embed(title="エラー", color=0xFF0000)
            error_embed.add_field(
                name="",
                value="`image`の引用が不適切です\n`image`には画像のURLを入力してください",
            )
            await interaction.response.send_message(embed=error_embed, ephemeral=True)
            return

        response = requests.get(image, stream=True)
        content_type = response.headers.get("Content-Type")
        if not imghdr.what(None, response.content):
            error_embed = discord.Embed(title="エラー", color=0xFF0000)
            error_embed.add_field(
                name="",
                value="`image`の引用が不適切です\n`image`には画像のURLを入力してください",
            )
            await interaction.response.send_message(embed=error_embed, ephemeral=True)
            return

    default_embed = discord.Embed(
        title="お問い合わせ",
        description="サポート用のチケットを発行します。<:foxticket:1104540139440578570>\n発行後、メンションしたチャンネルにて質問などをご記入ください。<:foxticket:1104540139440578570>",
        color=0xFFD700,
    )

    if image:  # imageが指定されている場合、埋め込みメッセージに画像を追加
        default_embed.set_image(url=image)

    if title:
        default_embed.title = title
    if description:
        default_embed.description = description.replace(",", "\n")  # 改行を追加
    if color:
        if not color.startswith("#"):
            embed = Embed(
                title="エラー",
                description=f"`color`の引用が不適切です\n`color`は16進数で指定してください。\nまた16進数は以下のサイトを参照してください\n[カラーコード一覧](https://www.colordic.org/)",
                color=0xFF0000,
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        try:
            color_code = int(color.replace("#", ""), 16)
        except ValueError:
            embed = Embed(
                title="エラー",
                description=f"`color`の引用が不適切です\n`color`は16進数で指定してください。\nまた16進数は以下のサイトを参照してください\n[カラーコード一覧](https://www.colordic.org/)",
                color=0xFF0000,
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        else:
            default_embed.color = color_code
    else:
        color_code = 0xFFD700
        default_embed.color = color_code

    async def create_channel(interaction: discord.Interaction):
        # ユーザーが作成したチャンネル数をチェックする
        user_id = interaction.user.id
        channel_count = user_channel_counts.get(user_id, 0)
        if channel_count >= max_channels:
            error_embed = Embed(
                title="エラー",
                description=f"作成できるチケットの上限に来ました。\nほかのチケットを閉じてから再度試してください。<:foxticket:1104540139440578570>",
                color=0xFF0000,
            )
            await interaction.response.send_message(embed=error_embed, ephemeral=True)
            return

        # チャンネルを削除する
        for channel in interaction.guild.text_channels:
            if (
                channel.name.startswith("🎫|")
                and channel.topic == f"Created by {interaction.user.id}"
            ):
                await channel.delete()

        # ユーザーが作成したチャンネル数をカウントする
        user_channel_counts[user_id] = channel_count + 1

        # チャンネルを作成する
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.guild.me: discord.PermissionOverwrite(read_messages=True),
            interaction.user: discord.PermissionOverwrite(read_messages=True),
        }
        if customer:
            overwrites[customer] = discord.PermissionOverwrite(read_messages=True)

        if category:
            channel = await category.create_text_channel(
                f"🎫|{interaction.user.name}", overwrites=overwrites
            )
        else:
            channel = await interaction.guild.create_text_channel(
                f"🎫|{interaction.user.name}", overwrites=overwrites
        )

        # 作成したチャンネルのトピックにユーザーのIDを記入する
        channel_topic = f"Created by {interaction.user.id}"
        await channel.edit(topic=channel_topic)

        # 新たに作成されたチャンネルにメッセージを送信する
        message_embed = Embed(
            title=title or "Ticket",
            description=welcome.replace(",", "\n")
            if welcome
            else "スタッフが来るまでお待ちください",  # 改行を追加
            color=color_code or 0xFFD700,
        )
        close_button = Button(
            label="🔒閉じる", style=ButtonStyle.red, custom_id="close_ticket_channel"
        )
        close_button.callback = delete_channel
        view = View(timeout=None)
        view.add_item(close_button)
        message = await channel.send(embed=message_embed, view=view)
        await channel.send(f"{interaction.user.mention}")
        if customer:
            await channel.send(f"{customer.mention}")

        await interaction.response.edit_message(embed=default_embed)

        message_embed = Embed(
            title="Ticket",
            description=f"チケットを作成しました。\n作成されたチャンネルにて質問などをご記入ください。<:foxticket:1104540139440578570>\n{channel.mention}",
            color=color_code or 0xFFD700,
        )
        message = await interaction.followup.send(embed=message_embed, ephemeral=True)

    button = Button(
        label=label or "🎫チケット発行",
        style=ButtonStyle.green,
        custom_id="create_ticket_channel",
    )
    button.callback = create_channel
    view = View(timeout=None)
    view.add_item(button)
    await interaction.response.send_message(embed=default_embed, view=view)

    async def delete_channel(interaction: discord.Interaction):
        # チャンネルの取得
        channel = interaction.channel

        # チャンネルのトピックからユーザーIDを取得する
        channel_topic = channel.topic
        user_id = int(channel_topic.split("Created by ")[1])

        # チャンネルが削除された場合
        try:
            await channel.delete()
        except discord.NotFound:
            pass
        else:
            # ユーザーが作成したチャンネル数をカウントする
            user_channel_counts[user_id] -= 1

# ----------------------------------------------------------------------------------------
# 認証
@bot.tree.command(name="verify", description="認証パネルを作成します")
async def verify(
    interaction: discord.Interaction,
    role: discord.Role,
    title: str = None,
    message: str = None,
    label: str = None,
    image: str = None,
    thumbnail_url: str = None,
):
    """
    :param role: 付与するロールを指定してください
    :param title: 認証パネルのタイトルを変更できます
    :param message: 認証パネルのメッセージを変更できます　また「,」 を使用することで改行できます
    :param label: 認証パネルのボタンに表示するメッセージを変更できます
    :param image: 認証パネルにに追加する画像を指定できます
    :param thumbnail_url: 認証パネルのサムネイルを指定できます
    """

    # コマンドを使用したユーザーがチャンネルの管理権限を持っていることを確認
    if not interaction.channel.permissions_for(interaction.user).manage_channels:
        # 管理者権限を持っていない場合、エラーメッセージを送信
        error_embed = discord.Embed(
            title="エラー",
            description="権限を確認出来ませんでした\n このコマンドを実行するには管理者権限が必要です",
            color=0xFF0000,
        )
        await interaction.response.send_message(embed=error_embed, ephemeral=True)
        return

    # BOTが指定されたロールを付与できるかどうかを確認
    if not interaction.guild.me.top_role > role:
        # 権限が低い場合、エラーメッセージを送信
        error_embed = discord.Embed(
            title="エラー",
            description="BOTの権限が付与しようとしているロールより低いです\n設定を変更後再度お試しください",
            color=0xFF0000,
        )
        await interaction.response.send_message(embed=error_embed, ephemeral=True)
        return
    
    # サムネイルを追加します
    if thumbnail_url:
        # URLが画像かどうかをチェックします
        if not thumbnail_url.startswith("http"):
            error_embed = discord.Embed(title="エラー", color=0xFF0000)
            error_embed.add_field(
                name="",
                value="`thumbnail_url`の引用が不適切です\n`thumbnail_url`には画像のURLを入力してください",
            )
            await interaction.response.send_message(embed=error_embed, ephemeral=True)
            return

        response = requests.get(thumbnail_url, stream=True)
        content_type = response.headers.get("Content-Type")
        if not imghdr.what(None, response.content):
            error_embed = discord.Embed(title="エラー", color=0xFF0000)
            error_embed.add_field(
                name="",
                value="`thumbnail_url`の引用が不適切です\n`thumbnail_url`には画像のURLを入力してください",
            )
            await interaction.response.send_message(embed=error_embed, ephemeral=True)
            return
        
    # サムネイルを追加します
    if image:
        # URLが画像かどうかをチェックします
        if not image.startswith("http"):
            error_embed = discord.Embed(title="エラー", color=0xFF0000)
            error_embed.add_field(
                name="",
                value="`image`の引用が不適切です\n`image`には画像のURLを入力してください",
            )
            await interaction.response.send_message(embed=error_embed, ephemeral=True)
            return

        response = requests.get(image, stream=True)
        content_type = response.headers.get("Content-Type")
        if not imghdr.what(None, response.content):
            error_embed = discord.Embed(title="エラー", color=0xFF0000)
            error_embed.add_field(
                name="",
                value="`image`の引用が不適切です\n`image`には画像のURLを入力してください",
            )
            await interaction.response.send_message(embed=error_embed, ephemeral=True)
            return

    # 改行が含まれるメッセージをエスケープする
    escaped_message = message.replace(",", "\n") if message else None

    # 認証ボタンを作成
    verify_button = Button(style=ButtonStyle.green, label=label or "✅認証")

    # Embedを作成
    embed = discord.Embed(
        title=title or "<a:Verifyfox:1104540613854101574>ユーザー認証<a:Verifyfox:1104540613854101574>",
        description=escaped_message or "以下の認証ボタンを押して認証を完了してください。\n認証後サーバーが閲覧可能になります。<a:Verifyfox:1104540613854101574>",
        color=0x00FF00,
    )
    
    # 画像をEmbedに追加
    if image:
        embed.set_image(url=image)

    # Embedにサムネイルを追加
    if thumbnail_url:
        embed.set_thumbnail(url=thumbnail_url)

    # Embedにボタンを追加
    view = discord.ui.View(timeout=None)
    view.add_item(verify_button)

    # ボタンが押されたら実行する関数
    async def callback(interaction: discord.Interaction):
        member = interaction.user
        if role in member.roles:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="エラー",
                    description=f"{member.mention}さんは既に認証済みです。<a:Verifyfox:1104540613854101574>",
                    color=0xFF0000,
                ),
                ephemeral=True,
            )
        else:
            await member.add_roles(role)
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="認証完了",
                    description=f"{member.mention}さん認証が完了しました！<a:Verifyfox:1104540613854101574>",
                    color=0x00FF00,
                ),
                ephemeral=True,
            )

    verify_button.callback = callback
    await interaction.response.send_message(embed=embed, view=view, ephemeral=False)

# ----------------------------------------------------------------------------------------
# ロールパネル
@bot.tree.command(name="role-panel", description="ロールパネルを作成します")
async def rolepanel(
    interaction: discord.Interaction,
    role1: discord.Role,
    description1: str = "",
    role2: discord.Role = None,
    description2: str = "",
    role3: discord.Role = None,
    description3: str = "",
    role4: discord.Role = None,
    description4: str = "",
    role5: discord.Role = None,
    description5: str = "",
    role6: discord.Role = None,
    description6: str = "",
    role7: discord.Role = None,
    description7: str = "",
    role8: discord.Role = None,
    description8: str = "",
    role9: discord.Role = None,
    description9: str = "",
    role10: discord.Role = None,
    description10: str = "",
    title: str = "",
    message: str = "",
    secondtitle: str = "",
    label: str = "",
):
    """
    :param role1: 表示するロール1
    :param description1: role1 の説明文
    :param role2: 表示するロール2
    :param description2: role2 の説明文
    :param role3: 表示するロール3
    :param description3: role3 の説明文
    :param role4: 表示するロール4
    :param description4: role4 の説明文
    :param role5: 表示するロール5
    :param description5: role5 の説明文
    :param role6: 表示するロール6
    :param description6: role6 の説明文
    :param role7: 表示するロール7
    :param description7: role7 の説明文
    :param role8: 表示するロール8
    :param description8: role8 の説明文
    :param role9: 表示するロール9
    :param description9: role9 の説明文
    :param role10: 表示するロール10
    :param description10: role10 の説明文
    :param title: ロールパネルに表示するタイトルを変更できます
    :param message: ロールパネルに表示するメッセージを変更できます
    :param secondtitle: ロールパネルに表示する2番目のタイトルを変更できます
    :param label: ロールパネルに表示するセレクトメニューの名前を変更できます
    """

    # コマンドを使用したユーザーがチャンネルの管理権限を持っていることを確認
    if not interaction.channel.permissions_for(interaction.user).manage_channels:
        # 管理者権限を持っていない場合、エラーメッセージを送信
        error_embed = discord.Embed(
            title="エラー",
            description="権限を確認出来ませんでした\n このコマンドを実行するには管理者権限が必要です",
            color=0xFF0000,
        )
        await interaction.response.send_message(embed=error_embed, ephemeral=True)
        return

    # BOTが指定されたロールを付与できるかどうかを確認
    if not (
        interaction.guild.me.top_role > role1
        and (role2 is None or interaction.guild.me.top_role > role2)
        and (role3 is None or interaction.guild.me.top_role > role3)
        and (role4 is None or interaction.guild.me.top_role > role4)
        and (role5 is None or interaction.guild.me.top_role > role5)
        and (role6 is None or interaction.guild.me.top_role > role6)
        and (role7 is None or interaction.guild.me.top_role > role7)
        and (role8 is None or interaction.guild.me.top_role > role8)
        and (role9 is None or interaction.guild.me.top_role > role9)
        and (role10 is None or interaction.guild.me.top_role > role10)
    ):
        # 権限が低い場合、エラーメッセージを送信
        error_embed = discord.Embed(
            title="エラー",
            description="BOTの権限が付与しようとしているロールより低いです\n設定を変更後再度お試しください",
            color=0xFF0000,
        )
        await interaction.response.send_message(embed=error_embed, ephemeral=True)
        return

    # ロールオブジェクトのリストを作成
    roles = []
    if role1:
        roles.append({"id": role1.id, "name": role1.name, "description": description1})
    if role2:
        roles.append({"id": role2.id, "name": role2.name, "description": description2})
    if role3:
        roles.append({"id": role3.id, "name": role3.name, "description": description3})
    if role4:
        roles.append({"id": role4.id, "name": role4.name, "description": description4})
    if role5:
        roles.append({"id": role5.id, "name": role5.name, "description": description5})
    if role6:
        roles.append({"id": role6.id, "name": role6.name, "description": description6})
    if role7:
        roles.append({"id": role7.id, "name": role7.name, "description": description7})
    if role8:
        roles.append({"id": role8.id, "name": role8.name, "description": description8})
    if role9:
        roles.append({"id": role9.id, "name": role9.name, "description": description9})
    if role10:
        roles.append(
            {"id": role10.id, "name": role10.name, "description": description10}
        )

    options = []
    for i, role in enumerate(roles):
        option = discord.SelectOption(
            label=role["name"], value=str(i), description=role.get("description")
        )
        options.append(option)

    select = discord.ui.Select(
        placeholder=label or "付与したいロールを選択してください",
        options=options,
        min_values=1,
        max_values=1,
    )

    embed = discord.Embed(
        title=title or "ロールパネル",
        description=message or "下記の選択肢からロールを選択してください。",
        color=0xFFD700,
    )
    role_list = "\n\n".join(
        [f"<@&{role['id']}>｜{role.get('description', '')}" for role in roles]
    )
    embed.add_field(name=secondtitle or "ロール一覧", value=role_list, inline=False)

    view = discord.ui.View(timeout=None)
    view.add_item(select)
    message = await interaction.response.send_message(embed=embed, view=view)

    async def callback(interaction: discord.Interaction):
        selected_value = interaction.data["values"][0]
        if selected_value == "-":  # 選択解除オプションが選択された場合
            embed = discord.Embed(
                title="選択解除完了", description="ロールパネルの選択を解除しました。", color=0x00FF00
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            selected_role_index = int(selected_value)
            selected_role = roles[selected_role_index]
            user = interaction.user
            member = interaction.guild.get_member(user.id)

            user_role = discord.utils.get(member.roles, id=selected_role["id"])
            role = interaction.guild.get_role(selected_role["id"])

            if user_role in member.roles:
                await member.remove_roles(user_role)
                embed = discord.Embed(
                    title="ロール削除完了",
                    description=f"{user.mention} から <@&{role.id}> を削除しました。",
                    color=0x00FF00,
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                await member.add_roles(role)
                embed = discord.Embed(
                    title="ロール付与完了",
                    description=f"{user.mention} に <@&{role.id}> を付与しました。",
                    color=0x00FF00,
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)

    select.callback = callback

# ----------------------------------------------------------------------------------------
# 通話の一括移動
@bot.tree.command(name="all-move", description="ボイスチャンネル内のユーザーを一括で移動できます")
async def all_move(
    interaction: discord.Interaction,
    left: discord.VoiceChannel,
    join: discord.VoiceChannel,
):
    """
    :param left: 移動対象のチャンネル
    :param hiub: 移動先のチャンネル
    """
    # コマンドを使用したユーザーがチャンネルの管理権限を持っていることを確認
    if not interaction.channel.permissions_for(interaction.user).manage_channels:
        # 管理者権限を持っていない場合、エラーメッセージを送信
        error_embed = discord.Embed(
            title="エラー",
            description="権限を確認出来ませんでした\n このコマンドを実行するには管理者権限が必要です",
            color=0xFF0000,
        )
        await interaction.response.send_message(embed=error_embed, ephemeral=True)
        return

    left_members = left.members
    if not left_members:
        embed = discord.Embed(
            title="エラー", description=f"{left.name}にはユーザーが存在しません", color=0xFF0000
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    moved_members = []
    for member in left_members:
        await member.move_to(join)
        moved_members.append(member.mention)

    embed = discord.Embed(
        title="移動完了",
        description=f"{left.mention}から{join.mention}に`{len(moved_members)}`人移動させました",
        color=0x00FF00,
    )
    embed.add_field(name="移動させたユーザー", value="\n".join(moved_members))
    await interaction.response.send_message(embed=embed)


# ----------------------------------------------------------------------------------------
# チャンネル名の編集
@bot.tree.command(name="edit-channel", description="指定したチャンネルの名前を変更します")
async def edit_channel(
    interaction: discord.Interaction,
    channel: Union[discord.TextChannel, discord.VoiceChannel],
    name: str,
):
    """
    :param channel: 名前を変更するチャンネルを指定できます
    :param name: 変更する名前を指定できます
    """
    # コマンドを使用したユーザーがチャンネルの管理権限を持っていることを確認
    if not interaction.channel.permissions_for(interaction.user).manage_channels:
        # 管理者権限を持っていない場合、エラーメッセージを送信
        error_embed = discord.Embed(
            title="エラー",
            description="権限を確認出来ませんでした\n このコマンドを実行するには管理者権限が必要です",
            color=0xFF0000,
        )
        await interaction.response.send_message(embed=error_embed, ephemeral=True)
        return

    old_name = channel.name
    await channel.edit(name=name)
    embed = discord.Embed(title="チャンネル名変更完了", color=0x00FF00)
    embed.add_field(name="変更されたチャンネル", value=f"{channel.mention}")
    embed.add_field(name="変更前", value=f"```\n{old_name}\n```", inline=False)
    embed.add_field(name="変更後", value=f"```\n{name}\n```", inline=False)
    guild = interaction.guild
    if guild.icon:
        icon_url = guild.icon.url
        embed.set_thumbnail(url=icon_url)
    else:
         # アイコンが設定されていない場合、デフォルトの画像をサムネイルとして使用
        default_icon_url = "https://cdn.discordapp.com/attachments/1101747131519348856/1108622056343490581/image.png"
        embed.set_thumbnail(url=default_icon_url)
    await interaction.response.send_message(embed=embed)


# ----------------------------------------------------------------------------------------
# カテゴリー名の編集
@bot.tree.command(name="edit-category", description="指定したカテゴリーの名前を変更します")
async def edit_category(
    interaction: discord.Interaction, category: discord.CategoryChannel, name: str
):
    """
    :param category: 名前を変更するカテゴリーを指定できます
    :param name: 変更する名前を指定できます
    """
    # コマンドを使用したユーザーがカテゴリーの管理権限を持っていることを確認
    if not interaction.channel.permissions_for(interaction.user).manage_channels:
        # 管理者権限を持っていない場合、エラーメッセージを送信
        error_embed = discord.Embed(
            title="エラー",
            description="権限を確認出来ませんでした\n このコマンドを実行するには管理者権限が必要です",
            color=0xFF0000,
        )
        await interaction.response.send_message(embed=error_embed, ephemeral=True)
        return

    old_name = category.name
    await category.edit(name=name)
    embed = discord.Embed(title="カテゴリー名変更完了", color=0x00FF00)
    embed.add_field(name="変更されたカテゴリー", value=f"`{category.name}`")
    embed.add_field(name="変更前", value=f"```\n{old_name}\n```", inline=False)
    embed.add_field(name="変更後", value=f"```\n{name}\n```", inline=False)
    guild = interaction.guild
    if guild.icon:
        icon_url = guild.icon.url
        embed.set_thumbnail(url=icon_url)
    else:
         # アイコンが設定されていない場合、デフォルトの画像をサムネイルとして使用
        default_icon_url = "https://cdn.discordapp.com/attachments/1101747131519348856/1108622056343490581/image.png"
        embed.set_thumbnail(url=default_icon_url)
    await interaction.response.send_message(embed=embed)
    
# ----------------------------------------------------------------------------------------
#サーバー名の編集
@bot.tree.command(name="edit-guild", description="サーバー名を変更します")
async def edit_guild(interaction: discord.Interaction, name: str):
    """
    :param name: 変更する名前を指定できます
    """
    # コマンドを使用したユーザーがカテゴリーの管理権限を持っていることを確認
    if not interaction.channel.permissions_for(interaction.user).manage_channels:
        # 管理者権限を持っていない場合、エラーメッセージを送信
        error_embed = discord.Embed(
            title="エラー",
            description="権限を確認出来ませんでした\n このコマンドを実行するには管理者権限が必要です",
            color=0xFF0000,
        )
        await interaction.response.send_message(embed=error_embed, ephemeral=True)
        return
    
    guild = interaction.guild
    old_name = guild.name
    await guild.edit(name=name)
    embed = discord.Embed(title="サーバー名を変更しました", color=0x00FF00)
    embed.add_field(name="変更前", value=f"```{old_name}```", inline=False)
    embed.add_field(name="変更後", value=f"```{name}```", inline=False)
    if guild.icon:
        icon_url = guild.icon.url
        embed.set_thumbnail(url=icon_url)
    else:
         # アイコンが設定されていない場合、デフォルトの画像をサムネイルとして使用
        default_icon_url = "https://cdn.discordapp.com/attachments/1101747131519348856/1108622056343490581/image.png"
        embed.set_thumbnail(url=default_icon_url)
    await interaction.response.send_message(embed=embed)
    
# ----------------------------------------------------------------------------------------
#kick
@bot.tree.command(name="kick", description="ユーザーをキックします")
async def kick(interaction: discord.Interaction, user: discord.Member, reason: str = None):
    """
    :param user: キック対象のユーザー
    :param reason: キックする理由
    """
    
    # コマンドを使用したユーザーがカテゴリーの管理権限を持っていることを確認
    if not interaction.channel.permissions_for(interaction.user).manage_channels:
        # 管理者権限を持っていない場合、エラーメッセージを送信
        error_embed = discord.Embed(
            title="エラー",
            description="権限を確認できませんでした。\nこのコマンドを実行するには管理者権限が必要です。",
            color=0xFF0000,
        )
        await interaction.response.send_message(embed=error_embed, ephemeral=True)
        return
    
    # キック対象のユーザーが存在しない場合、エラーメッセージを送信
    try:
        await user.kick(reason=reason)
    except discord.Forbidden:
        error_embed = discord.Embed(
            title="エラー",
            description=f"{user.mention}をキックできませんでした。\n以下のことが考えられます:\n1. キック対象のユーザーの権限がBOTより高い\n2. ユーザーが存在しない",
            color=0xFF0000,
        )
        await interaction.response.send_message(embed=error_embed, ephemeral=True)
        return
    
    if reason is None:
        reason = "なし"

    embed = discord.Embed(title="ユーザーをキックしました", color=0xff0000)
    if user.avatar:
        embed.set_thumbnail(url=user.avatar.url)
    else:
        embed.set_thumbnail(url=user.default_avatar.url)

    embed.add_field(name="名前", value=f"```{user.name}#{user.discriminator}```", inline=False)
    embed.add_field(name="ユーザーID", value=f"```{user.id}```", inline=False)
    embed.add_field(name="理由", value=f"```{reason}```", inline=False)
    embed.add_field(name="実行ユーザー", value=f"```{interaction.user.name}#{interaction.user.discriminator}\n{interaction.user.id}```", inline=False)

    await interaction.response.send_message(embed=embed)
    
# ----------------------------------------------------------------------------------------
#BAN
@bot.tree.command(name="ban", description="ユーザーをBANします")
async def ban(interaction: discord.Interaction, user: discord.Member, reason: str = None):
    """
    :param user: BAN対象のユーザー
    :param reason: BANする理由
    """

    # コマンドを使用したユーザーがカテゴリーの管理権限を持っていることを確認
    if not interaction.channel.permissions_for(interaction.user).ban_members:
        # 管理者権限を持っていない場合、エラーメッセージを送信
        error_embed = discord.Embed(
            title="エラー",
            description="権限を確認出来ませんでした\n このコマンドを実行するには管理者権限が必要です",
            color=0xFF0000,
        )
        await interaction.response.send_message(embed=error_embed, ephemeral=True)
        return

    # BAN対象のユーザーが存在しない場合、エラーメッセージを送信
    try:
        await user.ban(reason=reason)
    except discord.Forbidden:
        error_embed = discord.Embed(
            title="エラー",
            description=f"{user.mention}をBANできませんでした\n原因は以下のことが考えられます\n1:BAN対象のユーザーの権限がBOTより高い\n2:ユーザーが存在しない",
            color=0xFF0000,
        )
        await interaction.response.send_message(embed=error_embed, ephemeral=True)
        return

    await user.ban(reason=reason)

    if reason is None:
        reason = "なし"

    embed = discord.Embed(title="ユーザーをBANしました", color=0xff0000)
    if user.avatar:
        embed.set_thumbnail(url=user.avatar.url)
    else:
        embed.set_thumbnail(url=user.default_avatar.url)

    embed.add_field(name="名前", value=f"```{user.name}#{user.discriminator}```", inline=False)
    embed.add_field(name="ユーザーID", value=f"```{user.id}```", inline=False)
    embed.add_field(name="理由", value=f"```{reason}```", inline=False)
    embed.add_field(name="実行ユーザー", value=f"```{interaction.user.name}#{interaction.user.discriminator}\n{interaction.user.id}```", inline=False)

    await interaction.response.send_message(embed=embed)
    
# ----------------------------------------------------------------------------------------
#BAN解除
@bot.tree.command(name="un-ban", description="BANを解除します")
async def unban(interaction: discord.Interaction, user: discord.User, reason: str = "なし"):
    """
    :param user: BAN解除対象のユーザーID
    :param reason: BANを解除する理由
    """
    # コマンドを使用したユーザーがカテゴリーの管理権限を持っていることを確認
    if not interaction.channel.permissions_for(interaction.user).ban_members:
        # 管理者権限を持っていない場合、エラーメッセージを送信
        error_embed = discord.Embed(
            title="エラー",
            description="権限を確認出来ませんでした\n このコマンドを実行するには管理者権限が必要です",
            color=0xFF0000,
        )
        await interaction.response.send_message(embed=error_embed, ephemeral=True)
        return
    
    guild = interaction.guild
    executor = interaction.user
    member = guild.get_member(user.id)

    await guild.unban(user, reason=reason)

    embed = discord.Embed(title="BANを解除しました", color=0x00ff00)
    if user.avatar:
        embed.set_thumbnail(url=user.avatar.url)
    else:
        embed.set_thumbnail(url=user.default_avatar.url)
    embed.add_field(name="名前", value=f"```{user.name}#{user.discriminator}```", inline=False)
    embed.add_field(name="ユーザーID", value=f"```{user.id}```", inline=False)
    embed.add_field(name="理由", value=f"```{reason}```", inline=False)
    embed.add_field(name="実行ユーザー", value=f"```{executor.name}#{executor.discriminator}\n{executor.id}```", inline=False)

    await interaction.response.send_message(embed=embed)

# ----------------------------------------------------------------------------------------
#タイムアウト
@bot.tree.command(name="timeout", description="指定したユーザーを一定時間タイムアウトします")
async def timeout(interaction: discord.Interaction, user: discord.Member, time: str, reason: str = None):
    """
    :param user: タイムアウト対象のユーザー
    :param time: タイムアウトする時間 「d h m s」を使用する形式で指定出来ます
    :param reason: タイムアウトする理由
    """
    # コマンドを使用したユーザーがカテゴリーの管理権限を持っていることを確認
    if not interaction.channel.permissions_for(interaction.user).ban_members:
        # 管理者権限を持っていない場合、エラーメッセージを送信
        error_embed = discord.Embed(
            title="エラー",
            description="権限を確認出来ませんでした\n このコマンドを実行するには管理者権限が必要です",
            color=0xFF0000,
        )
        await interaction.response.send_message(embed=error_embed, ephemeral=True)
        return
    
    if user.top_role >= interaction.guild.me.top_role:
        embed = discord.Embed(
            title="エラー",
            description=f"{user.mention}をタイムアウトできませんでした\n原因は以下のことが考えられます\n1:タイムアウト対象のユーザーの権限がBOTより高い\n2:ユーザーが存在しない\n3:ユーザーが管理者権限を持っている",
            color=0xFF0000
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    
    time_regex = re.compile(r"(\d+d)?(\d+h)?(\d+m)?(\d+s)?")
    time_match = time_regex.fullmatch(time)
    if not time_match:
        embed = discord.Embed(title="エラー", description=f"`time`の引用が不適切です\n`time`では`1d13h18m10s` や `15m18s`のような形式で時間を指定してください", color=0xFF0000)
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    time_dict = {
        "d": ["日", 86400],
        "h": ["時間", 3600],
        "m": ["分", 60],
        "s": ["秒", 1]
    }

    time_str = ""
    seconds = 0
    for group_num in range(1, 5):
        group = time_match.group(group_num)
        if group is not None:
            time_unit = time_dict[group[-1]]
            time_val = int(group[:-1])
            time_str += f"{time_val}{time_unit[0]}"
            seconds += time_val * time_unit[1]

    if seconds <= 10:
        embed = discord.Embed(title="エラー", description=f"`time`の引用が不適切です\n`time`で指定する時間は10秒以上でなければいけません", color=0xFF0000)
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    timeout_end = discord.utils.utcnow().replace(tzinfo=pytz.UTC) + timedelta(seconds=seconds)
    await user.edit(timed_out_until=timeout_end)

    embed = discord.Embed(title="ユーザーをタイムアウトしました", color=0xff0000)
    if user.avatar:
        embed.set_thumbnail(url=user.avatar.url)
    else:
        embed.set_thumbnail(url=user.default_avatar.url)
    embed.add_field(name="名前", value=f"```{user.name}#{user.discriminator}```", inline=False)
    embed.add_field(name="ユーザーID", value=f"```{user.id}```", inline=False)
    embed.add_field(name="実行ユーザー", value=f"```{interaction.user.name}#{interaction.user.discriminator}\n{interaction.user.id}```", inline=False)
    embed.add_field(name="時間", value=f"```{time_str}```", inline=False)
    embed.add_field(name="理由", value=f"```{reason if reason else 'なし'}```", inline=False)
    await interaction.response.send_message(embed=embed)
    
# ----------------------------------------------------------------------------------------
#タイムアウト解除
@bot.tree.command(name="un-timeout", description="指定したユーザーのタイムアウトを解除します")
async def untimeout(interaction: discord.Interaction, member: Union[discord.Member, discord.User], *, reason: str = None):
    """
    :param member: タイムアウトを解除するユーザー
    :param reason: タイムアウトを解除する理由
    """
    # コマンドを使用したユーザーがカテゴリーの管理権限を持っていることを確認
    if not interaction.channel.permissions_for(interaction.user).ban_members:
        # 管理者権限を持っていない場合、エラーメッセージを送信
        error_embed = discord.Embed(
            title="エラー",
            description="権限を確認出来ませんでした\n このコマンドを実行するには管理者権限が必要です",
            color=0xFF0000,
        )
        await interaction.response.send_message(embed=error_embed, ephemeral=True)
        return
    
    if not isinstance(member, discord.Member):
        embed = discord.Embed(title="エラー", description="`user`の引用が不適切です\n`user`ではサーバー内にいるタイムアウトを解除したいユーザーを指定してください", color=0xff0000)
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    try:
        await member.edit(timed_out_until=None, reason=reason)
        
        embed = discord.Embed(title="タイムアウトを解除しました", color=0x00ff00)
        embed.add_field(name="名前", value=f"```{member.name}#{member.discriminator}```", inline=False)
        embed.add_field(name="ユーザーID", value=f"```{member.id}```", inline=False)
        embed.add_field(name="実行ユーザー", value=f"```{interaction.user.name}#{interaction.user.discriminator}\n{interaction.user.id}```", inline=False)
        embed.add_field(name="理由", value=f"```{reason if reason else 'なし'}```", inline=False)
        
        if member.avatar:
            avatar_url = member.avatar.url
        else:
            avatar_url = member.default_avatar.url
        
        embed.set_thumbnail(url=avatar_url)

        await interaction.response.send_message(embed=embed)
    except Exception as e:
        embed = discord.Embed(title="エラー", description=f"タイムアウトの解除に失敗しました", color=0xff0000)
        await interaction.response.send_message(embed=embed, ephemeral=True)

# ----------------------------------------------------------------------------------------
#invite
@bot.tree.command(name="invite", description="指定されたチャンネルに招待リンクを作成します")
async def invite(
    interaction: discord.Interaction,
    channel: discord.TextChannel,
    temporary: typing.Optional[bool] = False,
    uses: typing.Optional[int] = None,
):
    """
    :param channel: 招待リンクを作成するチャンネルを指定できます
    :param temporary: 一時的なメンバーとして招待するかどうかを指定できます
    :param uses: 使用回数を指定できます1~100
    """
    # コマンドを使用したユーザーがカテゴリーの管理権限を持っていることを確認
    if not interaction.channel.permissions_for(interaction.user).ban_members:
        # 管理者権限を持っていない場合、エラーメッセージを送信
        error_embed = discord.Embed(
            title="エラー",
            description="権限を確認出来ませんでした\n このコマンドを実行するには管理者権限が必要です",
            color=0xFF0000,
        )
        await interaction.response.send_message(embed=error_embed, ephemeral=True)
        return
    
    if uses is not None and (uses < 1 or uses > 100):
        embed = discord.Embed(
            title="エラー",
            description="`uses`が不適切です\n`uses`では`1~100`の数字を入力してください",
            color=0xFF0000,
        )
        await interaction.response.send_message(embed=embed)
        return
    
    guild = interaction.guild
    invite = await channel.create_invite(temporary=temporary, max_uses=uses)
    embed = discord.Embed(title="招待リンクを作成しました", color=0x00FF00)
    embed.add_field(name="招待コード", value=f"```{invite.code}```", inline=False)
    embed.add_field(name="URL", value=f"{invite.url}", inline=False)
    if temporary:
        embed.add_field(name="一時的なメンバーとして招待する", value="`はい`", inline=False)
    else:
        embed.add_field(name="一時的なメンバーとして招待する", value="`いいえ`", inline=False)
    if uses is not None:
        embed.add_field(name="回数制限", value=f"`{uses}回`", inline=False)
    else:
        embed.add_field(name="回数制限", value="`無制限`", inline=False)
    
    if guild.icon:
        icon_url = guild.icon.url
        embed.set_thumbnail(url=icon_url)
    else:
        # アイコンが設定されていない場合、デフォルトの画像をサムネイルとして使用
        default_icon_url = "https://cdn.discordapp.com/attachments/1101747131519348856/1108622056343490581/image.png"
        embed.set_thumbnail(url=default_icon_url)
        
    await interaction.response.send_message(embed=embed)
    
# ----------------------------------------------------------------------------------------
#招待リンクリスト
@bot.tree.command(name="invite-list", description="現在有効な招待リンクのリストを表示します")
async def invite_list(interaction: discord.Interaction):

    # コマンドを使用したユーザーがカテゴリーの管理権限を持っていることを確認
    if not interaction.channel.permissions_for(interaction.user).ban_members:
        # 管理者権限を持っていない場合、エラーメッセージを送信
        error_embed = discord.Embed(
            title="エラー",
            description="権限を確認出来ませんでした\n このコマンドを実行するには管理者権限が必要です",
            color=0xFF0000,
        )
        await interaction.response.send_message(embed=error_embed, ephemeral=True)
        return
    
    guild = interaction.guild
    invites = await guild.invites()
    invite_list = "\n".join([f"コード:`{invite.code}` URL:{invite.url}" for invite in invites])
    
    embed = discord.Embed(title="招待リンクリスト", description=invite_list, color=0xFFD700)
    
    if guild.icon:
        icon_url = guild.icon.url
        embed.set_thumbnail(url=icon_url)
    else:
        # アイコンが設定されていない場合、デフォルトの画像をサムネイルとして使用
        default_icon_url = "https://cdn.discordapp.com/attachments/1101747131519348856/1108622056343490581/image.png"
        embed.set_thumbnail(url=default_icon_url)
    
    await interaction.response.send_message(embed=embed)
    
# ----------------------------------------------------------------------------------------
#招待リンク削除
@bot.tree.command(name="invite-delete", description="招待リンクを無効にします")
async def invite_delete(interaction: discord.Interaction, code: str):
    """
    :param code: 無効にする招待コードを入力してください
    """
    # コマンドを使用したユーザーがカテゴリーの管理権限を持っていることを確認
    if not interaction.channel.permissions_for(interaction.user).manage_guild:
        # 管理者権限を持っていない場合、エラーメッセージを送信
        error_embed = discord.Embed(
            title="エラー",
            description="権限を確認出来ませんでした\n このコマンドを実行するには管理者権限が必要です",
            color=0xFF0000,
        )
        await interaction.response.send_message(embed=error_embed, ephemeral=True)
        return

    # コマンドを使用したサーバーのIDを取得
    guild_id = interaction.guild_id
    try:
        invite = await bot.fetch_invite(f"https://discord.gg/{code}")
        # 取得した招待リンクのサーバーIDとコマンドを使用したサーバーIDを比較し、一致しない場合はエラーメッセージを送信
        if invite.guild.id != guild_id:
            error_embed = discord.Embed(
                title="エラー",
                description=f"`{code}`は有効な招待コードではありません\n`code`には有効な招待コードを入力してください",
                color=0xFF0000,
            )
            await interaction.response.send_message(embed=error_embed, ephemeral=True)
            return

        await invite.delete(reason="Invite link deleted by user.")
        embed = discord.Embed(
            title="招待リンクを無効にしました",
            description=f"無効にした招待コード ```{code}```",
            color=0x00FF00,
        )
        guild = interaction.guild
        if guild.icon:
            icon_url = guild.icon.url
            embed.set_thumbnail(url=icon_url)
        else:
            # アイコンが設定されていない場合、デフォルトの画像をサムネイルとして使用
            default_icon_url = "https://cdn.discordapp.com/attachments/1101747131519348856/1108622056343490581/image.png"
            embed.set_thumbnail(url=default_icon_url)
            
        embed.add_field(name="リンク", value=f"https://discord.gg/{code}", inline=False)
        await interaction.response.send_message(embed=embed)

    except discord.NotFound:
        embed = discord.Embed(
            title="エラー",
            description=f"`{code}`は有効な招待コードではありません\n`code`には有効な招待コードを入力してください",
            color=0xFF0000,
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

# ----------------------------------------------------------------------------------------
#招待リンク全て無効
@bot.tree.command(name="invite-delete-all", description="サーバーに存在する招待リンクをすべて無効にします")
async def invite_delete_all(interaction: discord.Interaction):
    
    # コマンドを使用したユーザーがカテゴリーの管理権限を持っていることを確認
    if not interaction.channel.permissions_for(interaction.user).ban_members:
        # 管理者権限を持っていない場合、エラーメッセージを送信
        error_embed = discord.Embed(
            title="エラー",
            description="権限を確認出来ませんでした\n このコマンドを実行するには管理者権限が必要です",
            color=0xFF0000,
        )
        await interaction.response.send_message(embed=error_embed, ephemeral=True)
        return
    
    guild = interaction.guild
    invites = await guild.invites()

    invalid_count = 0
    for invite in invites:
        try:
            await invite.delete()
            invalid_count += 1
        except:
            pass

    embed = discord.Embed(
        title="招待リンクを無効にしました",
        description=f"{guild.name}の招待リンク計{invalid_count}を無効にしました",
        color=0x00FF00
    )
    guild = interaction.guild
    if guild.icon:
        icon_url = guild.icon.url
        embed.set_thumbnail(url=icon_url)
    else:
         # アイコンが設定されていない場合、デフォルトの画像をサムネイルとして使用
        default_icon_url = "https://cdn.discordapp.com/attachments/1101747131519348856/1108622056343490581/image.png"
        embed.set_thumbnail(url=default_icon_url)

    await interaction.response.send_message(embed=embed)

# ----------------------------------------------------------------------------------------
#チャンネルの作成
class ChannelType(Enum):
    VOICE = "voice"
    TEXT = "text"

@bot.tree.command(name="channel-create", description="チャンネルを作成します")
async def channel_create(
    interaction: discord.Interaction,
    type: ChannelType,
    name: str,
    category: discord.CategoryChannel = None
):
    """
    :param type: 作成するチャンネルのタイプ
    :param name: 作成するチャンネルの名前
    :param category: 作成するチャンネルのカテゴリー
    """  
    # コマンドを使用したユーザーがカテゴリーの管理権限を持っていることを確認
    if not interaction.channel.permissions_for(interaction.user).ban_members:
        # 管理者権限を持っていない場合、エラーメッセージを送信
        error_embed = discord.Embed(
            title="エラー",
            description="権限を確認出来ませんでした\n このコマンドを実行するには管理者権限が必要です",
            color=0xFF0000,
        )
        await interaction.response.send_message(embed=error_embed, ephemeral=True)
        return
    
    guild = interaction.guild
    category = category or interaction.channel.category

    if not category:
        embed = discord.Embed(
            title="エラー",
            description=f"カテゴリーが指定されていません\n`category`を指定するかカテゴリー内でコマンドを実行してください",
            color=0xFF0000
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    if type == ChannelType.TEXT:
        channel = await category.create_text_channel(name=name)
        channel_type = "テキストチャンネル"
    elif type == ChannelType.VOICE:
        channel = await category.create_voice_channel(name=name)
        channel_type = "ボイスチャンネル"

    embed = discord.Embed(title="チャンネルを作成しました", color=0x00FF00)
    embed.add_field(name="チャンネルネーム", value=f"```{name}```", inline=False)
    embed.add_field(name="ID", value=f"```{channel.id}```", inline=False)
    embed.add_field(name="タイプ", value=f"```{channel_type}```", inline=False)
    embed.add_field(name="カテゴリー", value=f"```{category.name if category else 'なし'}```", inline=False)
    embed.add_field(name="実行ユーザー", value=f"```{interaction.user.name}#{interaction.user.discriminator}\n{interaction.user.id}```", inline=False)
    await interaction.response.send_message(embed=embed)
    
# ----------------------------------------------------------------------------------------
#GIVEAWAY
@bot.tree.command(name="giveaway-start", description="GIVEAWAYを開催出来ます")
async def giveaway(interaction: discord.Interaction, time: str, prize: str, winners: int, description: str = None):
    """
    :param time: 抽選時間を『s m h d』を使用する形式で指定できます
    :param prize: 景品を指定できます
    :param winners: 当選人数
    :param description: 景品の詳細
    """
    
    # コマンドを使用したユーザーがチャンネルの管理権限を持っていることを確認
    if not interaction.channel.permissions_for(interaction.user).manage_channels:
        # 管理者権限を持っていない場合、エラーメッセージを送信
        error_embed = discord.Embed(
            title="エラー",
            description="権限を確認出来ませんでした\n このコマンドを実行するには管理者権限が必要です",
            color=0xFF0000,
        )
        await interaction.response.send_message(embed=error_embed, ephemeral=True)
        return
    
    await interaction.response.send_message("GIVEAWAY作成中", ephemeral=True)

    duration = parse_duration(time)
    end_time = datetime.now() + duration

    end_time_format = f"<t:{int(end_time.timestamp())}:f>"
    remaining_time = get_remaining_time(end_time)

    # 企画メッセージを送信
    embed = discord.Embed(title="🎉 GIVEAWAY 🎉", description="**GIVEAWAYに参加するには🎉のリアクションを押してください**", color=0x00FFFF)
    embed.add_field(name="", value=f"残り時間:<t:{int(end_time.timestamp())}:R>\n終了時間:{end_time_format}\n主催者: {interaction.user.mention}\n当選者数: `{winners}人`", inline=False)
    embed.add_field(name="景品", value=f"{prize}", inline=False)
    embed.add_field(name="詳細", value=description or "なし", inline=False)

    # 0.1秒待機してから通常のメッセージ形式で送信
    await asyncio.sleep(0.1)
    sent_message = await interaction.channel.send(embed=embed)
    await sent_message.add_reaction("🎉")

    await asyncio.sleep(duration.total_seconds())  # 指定した時間待機

    try:
        # メッセージを取得
        message = await interaction.channel.fetch_message(sent_message.id)
    except discord.NotFound:
        # メッセージが削除された場合、giveawayを停止
        return

    reaction = discord.utils.get(message.reactions, emoji="🎉")

    # リアクションされたユーザーを取得
    users = []
    async for user in reaction.users():
        if not user.bot:
            users.append(user)

    # winners人数の当選者をランダムに選ぶ
    if len(users) < winners:
        winners = len(users)

    winners_list = random.sample(users, winners)

    if len(winners_list) > 0:
        # 当選者をメンション
        winners_mention = " ".join([winner.mention for winner in winners_list])

        # 当選メッセージを送信
        embed = discord.Embed(title="🎉 GIVEAWAY END 🎉", color=0x00FFFF)
        embed.add_field(name="", value=f"当選者: {winners_mention}\nおめでとうございます！", inline=False)
        embed.add_field(name="", value=f"企画メッセージ: [ここをクリック]({sent_message.jump_url})", inline=False)
        embed.add_field(name="景品", value=f"{prize}", inline=False)
        embed.add_field(name="詳細", value=description or "なし", inline=False)
        await interaction.channel.send(embed=embed)
        await interaction.channel.send(f"{winners_mention}")
    else:
        embed = discord.Embed(title="🎉 GIVEAWAY END 🎉", color=0x00FFFF)
        embed.add_field(name="", value=f"参加者が居ませんでした\n企画メッセージ: [ここをクリック]({sent_message.jump_url})", inline=False)
        await interaction.channel.send(embed=embed)

def parse_duration(time: str) -> timedelta:
    time_pattern = r"(\d+)([smhd])"
    matches = re.findall(time_pattern, time)
    delta_kwargs = {}
    for match in matches:
        amount = int(match[0])
        unit = match[1]
        if unit == "s":
            delta_kwargs["seconds"] = amount
        elif unit == "m":
            delta_kwargs["minutes"] = amount
        elif unit == "h":
            delta_kwargs["hours"] = amount
        elif unit == "d":
            delta_kwargs["days"] = amount
    return timedelta(**delta_kwargs)

def get_remaining_time(end_time: datetime) -> str:
    remaining_time = end_time - datetime.now()
    seconds = remaining_time.seconds
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    days = remaining_time.days
    return f"{days}日{hours}時間{minutes}分{seconds}秒"

#giveaway delete
@bot.tree.command(name="giveaway-delete", description="指定されたGIVEAWAYを削除します")
async def giveaway_delete(interaction: discord.Interaction, message_id: str):
    """
    :param message_id: 削除するGIVEAWAYのメッセージID
    """
    
    # コマンドを使用したユーザーがチャンネルの管理権限を持っていることを確認
    if not interaction.channel.permissions_for(interaction.user).manage_channels:
        # 管理者権限を持っていない場合、エラーメッセージを送信
        error_embed = discord.Embed(
            title="エラー",
            description="権限を確認出来ませんでした\n このコマンドを実行するには管理者権限が必要です",
            color=0xFF0000,
        )
        await interaction.response.send_message(embed=error_embed, ephemeral=True)
        return
    
    try:
        message = await interaction.channel.fetch_message(message_id)
    except discord.NotFound:
        embed = discord.Embed(title="エラー",description=f"`{message_id}`は有効なメッセージIDではありません", color=0xFF0000)
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    if not isinstance(message.embeds, list) or len(message.embeds) == 0:
        embed = discord.Embed(title="エラー",description=f"`{message_id}`は有効なgiveawayではありません", color=0xFF0000)
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    embed = message.embeds[0]
    if embed.title != "🎉 GIVEAWAY 🎉":
        embed = discord.Embed(title="エラー",description=f"`{message_id}`は有効なgiveawayではありません", color=0xFF0000)
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    await message.delete()

    embed = discord.Embed(title="GIVEAWAY Delete", description="指定されたGIVEAWAYを削除しました", color=0x00FF00)
    await interaction.response.send_message(embed=embed, ephemeral=True)
    
#giveaway reroll
@bot.tree.command(name="giveaway-reroll", description="GIVEAWAYの再抽選を行います")
async def giveaway_reroll(interaction: discord.Interaction, message_id: str, winners: int):
    """
    :param message_id: 再抽選するGIVEAWAYのメッセージID
    :param winners: 当選人数
    """
    
    # コマンドを使用したユーザーがチャンネルの管理権限を持っていることを確認
    if not interaction.channel.permissions_for(interaction.user).manage_channels:
        # 管理者権限を持っていない場合、エラーメッセージを送信
        error_embed = discord.Embed(
            title="エラー",
            description="権限を確認出来ませんでした\n このコマンドを実行するには管理者権限が必要です",
            color=0xFF0000,
        )
        await interaction.response.send_message(embed=error_embed, ephemeral=True)
        return

    try:
        message = await interaction.channel.fetch_message(message_id)
    except discord.NotFound:
        embed = discord.Embed(title="エラー", description=f"`{message_id}`は有効なメッセージIDではありません", color=0xFF0000)
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    if not message.embeds or message.embeds[0].title != "🎉 GIVEAWAY 🎉":
        embed = discord.Embed(title="エラー", description=f"`{message_id}`は有効なGIVEAWAYではありません", color=0xFF0000)
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    original_embed = message.embeds[0]
    prize = None
    description = None

    for field in original_embed.fields:
        if field.name == "景品":
            prize = field.value.strip("`")
        elif field.name == "詳細":
            description = field.value

    if not prize:
        prize = "なし"

    if not description:
        description = "なし"

    reaction = discord.utils.get(message.reactions, emoji="🎉")

    if not reaction:
        embed = discord.Embed(title="エラー", description=f"`{message_id}`は有効なGIVEAWAYではありません", color=0xFF0000)
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    users = []
    async for user in reaction.users():
        if not user.bot:
            users.append(user)

    if len(users) < winners:
        winners = len(users)

    winners_list = random.sample(users, winners)

    if len(winners_list) > 0:
        winners_mention = " ".join([winner.mention for winner in winners_list])

        embed = discord.Embed(title="🎉 GIVEAWAY Reroll 🎉", color=0x00FFFF)
        embed.add_field(name="", value=f"当選者: {winners_mention}\nおめでとうございます！", inline=False)
        embed.add_field(name="", value=f"企画メッセージ: [ここをクリック]({message.jump_url})", inline=False)
        embed.add_field(name="景品", value=f"{prize}", inline=False)
        embed.add_field(name="詳細", value=description, inline=False)
        await interaction.response.send_message(embed=embed)
        await interaction.channel.send(f"{winners_mention}")
    else:
        embed = discord.Embed(title="🎉 GIVEAWAY Reroll 🎉", color=0x00FFFF)
        embed.add_field(name="", value=f"参加者が居ませんでした", inline=False)
        embed.add_field(name="", value=f"企画メッセージ: [ここをクリック]({message.jump_url})", inline=False)
        embed.add_field(name="景品", value=f"{prize}", inline=False)
        embed.add_field(name="詳細", value=description, inline=False)
        await interaction.response.send_message(embed=embed)

# ----------------------------------------------------------------------------------------
#auto command
#自動reaction付与
@bot.event
async def on_message(message: discord.Message):
    if message.content.startswith("https://discord.com/channels/") and len(message.content.split()) == 1:
        await message.add_reaction("🔍")

#discordメッセージ情報取得
@bot.event
async def on_reaction_add(reaction: discord.Reaction, user: discord.User):
    if user.bot:
        return

    if reaction.emoji == "🔍":
        message_url = reaction.message.content
        if message_url.startswith("https://discord.com/channels/") and len(message_url.split()) == 1:
            try:
                guild_id, channel_id, message_id = message_url.split("/")[-3:]
                guild = bot.get_guild(int(guild_id))
                if guild is None:
                    raise ValueError("1:リンク先のサーバーにBOTが参加していない\n2:リンク先のメッセージが存在しない")
                channel = guild.get_channel(int(channel_id))
                if channel is None:
                    raise ValueError("1:リンク先のサーバーにBOTが参加していない\n2:リンク先のメッセージが存在しない")
                message = await channel.fetch_message(int(message_id))
            except (ValueError, discord.errors.NotFound) as e:
                error_embed = discord.Embed(
                    title="エラー",
                    description=f"メッセージ情報を取得できませんでした。以下の点を確認してください\n1:リンク先のサーバーにBOTが参加していない\n2:リンク先のメッセージが存在しない",
                    color=0xFF0000
                )
                reply_message = await reaction.message.reply(embed=error_embed, mention_author=False)
                return

            embed = discord.Embed(
                title="メッセージ情報",
                color=0xFFD700
            )
            embed.add_field(name="サーバー", value=f"`{message.guild.name}`", inline=True)
            embed.add_field(name="チャンネル", value=f"`{message.channel.name}`", inline=True)
            embed.add_field(name="メッセージ", value=message.content, inline=False)

            if message.author.display_avatar:
                embed.set_author(name=f"{message.author.name}#{message.author.discriminator}", icon_url=message.author.display_avatar.url)

            if message.guild.icon:
                embed.set_thumbnail(url=message.guild.icon.url)

            if message.attachments:
                for attachment in message.attachments:
                    if attachment.content_type.startswith('image/') or attachment.content_type.startswith('video/'):
                        embed.set_image(url=attachment.url)
                        break

            reply_message = await reaction.message.reply(embed=embed, mention_author=False)

            if message.embeds:
                embed = message.embeds[0]
                if embed.type == "rich":
                    await reaction.message.channel.send(embed=embed, mention_author=False)
                    
# ----------------------------------------------------------------------------------------
#モデレーター向け
@bot.tree.command(name="bot-server", description="Botが参加しているサーバーを管理します")
async def bot_server(interaction: discord.Interaction):
    authorized_user_id = 967347570013790258  # 許可されたユーザーのIDを指定してください

    if interaction.user.id != authorized_user_id:
        embed = discord.Embed(title="エラー", description="権限を確認できませんでした\nこのコマンドを実行できるのはモデレーターのみです", color=0xFF0000)
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    guilds = bot.guilds
    embed = discord.Embed(title="Bot Server", color=0xFFD700)

    for guild in guilds:
        invite_link = await guild.text_channels[0].create_invite(max_age=0)
        embed.add_field(name=guild.name, value=invite_link.url, inline=False)

    await interaction.response.send_message(embed=embed)

bot.run("MTA5NjE0OTg2NTc0ODI1MDc1NA.GGUHvM.LUByTOZD6eMdoMa2rYTqn0quhhRAn8c5AuToFI")

#MTA5NjE0OTg2NTc0ODI1MDc1NA.GGUHvM.LUByTOZD6eMdoMa2rYTqn0quhhRAn8c5AuToFI test
#MTA5OTQ3NjU0ODI5NTM0ODI1NQ.GDZf-Z.R_FEiq7ubG1mT_4UpxUfxzAm6rfg-iImSHLAtg mein