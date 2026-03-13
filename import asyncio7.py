import discord
import re
import os

# 1. 권한 설정
intents = discord.Intents.default()
intents.message_content = True 
intents.reactions = True 

client = discord.Client(intents=intents)

# 환경 변수에서 토큰을 불러옵니다.
token = os.environ.get("DISCORD_TOKEN")

if not token:
    print("오류: DISCORD_TOKEN 환경 변수가 설정되지 않았습니다.")
    exit()

@client.event
async def on_ready():
    print(f"봇 로그인 성공: {client.user.name}")
    print("===========")
    await client.change_presence(activity=discord.Game(name="파티 모집 관리 중"))

@client.event
async def on_raw_reaction_add(payload):
    if payload.user_id == client.user.id:
        return

    channel = client.get_channel(payload.channel_id)
    message = await channel.fetch_message(payload.message_id)
    
    # 1. 디스코드 게시글 제목에서 인원 파싱 (예: [4인], [4~6인])
    thread_title = channel.name 
    match = re.search(r'\[(\d+)(?:~(\d+))?인\]', thread_title)
    
    if not match:
        return
    
    min_count = int(match.group(1))
    max_count = int(match.group(2)) if match.group(2) else min_count
    
    # 2. 반응 확인 (커스텀 이모지 이름 리스트)
    target_emojis = ["__1", "__2", "__3", "__4", "__5", "__6", "__7", "__8", "__9", "_10", "_11", "_12", "_13"]
    
    if payload.emoji.name in target_emojis:
        participants = [] 
        for reaction in message.reactions:
            if reaction.emoji.name in target_emojis:
                async for user in reaction.users():
                    if not user.bot:
                        participants.append(user)
        
        current_count = len(participants)
        
        # 3. 알림 로직 (중복 알림 방지)
        history = [msg async for msg in channel.history(limit=5)]
        
        # [최대 인원 도달 시: 모집 완료]
        if current_count >= max_count:
            if not any("모집 완료" in m.content for m in history):
                mentions = " ".join([u.mention for u in participants])
                await channel.send(f"🎉 **[파티 모집 완료]** {max_count}명 달성! {mentions} 님들 일정 확인해주세요!")
        
        # [최소 인원 도달 시: 출발 가능]
        elif current_count >= min_count:
            if not any("최소 인원 달성" in m.content for m in history):
                await channel.send(f"📢 **[최소 인원 달성]** 현재 {current_count}명입니다! 출발 가능한 인원이 모였습니다.")

# 4. 봇 실행
client.run(token)

