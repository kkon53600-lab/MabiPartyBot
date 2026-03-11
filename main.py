import discord

# 1. 권한(Intents) 설정
# 메시지 내용과 반응(Reaction)을 읽기 위해 필요합니다.
intents = discord.Intents.default()
intents.message_content = True  # 메시지 내용 읽기 권한
intents.reactions = True        # 이모지 반응 읽기 권한

client = discord.Client(intents=intents)

# ⚠️ 주의: 반드시 'Reset Token'으로 새로 발급받은 토큰을 넣으세요!
token = "MTQ4MTAwOTYwMDUzNzgyNTQxMw.GsSVCi.yntGKvNbCT8CL-wxLvvpaV2JATVOiow1EYRX8w"

@client.event
async def on_ready():
    print(f"봇 로그인 성공: {client.user.name}")
    print("===========")
    # 상태 메시지 설정
    await client.change_presence(activity=discord.Game(name="마비노기 파티 모집 도움"))

@client.event
async def on_message(message):
    # 봇이 쓴 메시지는 무시
    if message.author.bot:
        return

    # '!커맨드'로 시작하는 경우
    if message.content.startswith('!커맨드'):
        await message.channel.send('커맨드 확인!')

@client.event
async def on_raw_reaction_add(payload):
    # 봇이 반응한 것은 무시
    if payload.user_id == client.user.id:
        return

    # 메시지 가져오기
    channel = client.get_channel(payload.channel_id)
    message = await channel.fetch_message(payload.message_id)
    
    # 제목에서 숫자 추출 (예: [6인])
    import re
    match = re.search(r'\[(\d+)인\]', message.content)
    if not match:
        return
    
    target_count = int(match.group(1)) # 모집 인원
    
    # 설정한 이모지 리스트 (:__1:, :__2: 등)
    target_emojis = ["__1", "__2", "__3", "__4", "__5", "__6", "__7", "__8", "__9", "_10", "_11", "_12", "_13"]
    
    if payload.emoji.name in target_emojis:
        # 이모지를 누른 사람들의 목록 구하기
        participants = set()
        for reaction in message.reactions:
            if reaction.emoji.name in target_emojis:
                async for user in reaction.users():
                    if not user.bot:
                        participants.add(user)
        
        # 인원 도달 시 멘션
        if len(participants) >= target_count:
            mentions = " ".join([user.mention for user in participants])
            await channel.send(f" :BlobCataww: 파티 모집 완료! {mentions} 님들 일정 확인해주세요!")
    
# 봇 실행
client.run(token)
