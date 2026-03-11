import discord
import asyncio
import os
import re
from aiohttp import web
from discord.ext import commands

# 1. 환경 설정 및 권한
intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.members = True # 멘션을 위해 필요

client = discord.Client(intents=intents)
token = "재발급받은_토큰을_입력하세요"

# --- 웹 서버 기능 (24시간 유지용) ---
async def health_check(request):
    return web.Response(text="OK", status=200)

async def start_web_server():
    app = web.Application()
    app.router.add_get('/health', health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8000)
    await site.start()

# --- 봇 이벤트 ---
@client.event
async def on_ready():
    print(f"로그인 성공: {client.user.name}")
    # 웹 서버 시작
    client.loop.create_task(start_web_server())
    await client.change_presence(activity=discord.Game(name="마비노기 파티 모집 도움"))

@client.event
async def on_message(message):
    if message.author.bot: return
    if message.content.startswith('!커맨드'):
        await message.channel.send('커맨드 확인!')

@client.event
async def on_raw_reaction_add(payload):
    if payload.user_id == client.user.id: return

    channel = client.get_channel(payload.channel_id)
    message = await channel.fetch_message(payload.message_id)
    
    match = re.search(r'\[(\d+)인\]', message.content)
    if not match: return
    
    target_count = int(match.group(1))
    target_emojis = ["__1", "__2", "__3", "__4", "__5", "__6", "__7", "__8", "__9", "_10", "_11", "_12", "_13"]
    
    if payload.emoji.name in target_emojis:
        participants = set()
        for reaction in message.reactions:
            if reaction.emoji.name in target_emojis:
                async for user in reaction.users():
                    if not user.bot:
                        participants.add(user)
        
        if len(participants) >= target_count:
            mentions = " ".join([user.mention for user in participants])
            await channel.send(f"파티 모집 완료! {mentions} 님들 일정 확인해주세요!")

client.run(token)
