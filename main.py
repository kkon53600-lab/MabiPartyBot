import discord
import re
import os
import asyncio
from datetime import datetime, timedelta

intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.members = True

client = discord.Client(intents=intents)
token = os.environ.get("DISCORD_TOKEN")

TARGET_EMOJIS = ["__1","__2","__3","__4","__5","__6","__7","__8","__9","_10","_11","_12","_13"]
scheduled_tasks = {}

if not token:
    print("오류: DISCORD_TOKEN 환경 변수가 설정되지 않았습니다.")
    exit()

@client.event
async def on_ready():
    print(f"봇 로그인 성공: {client.user.name}")
    await client.change_presence(activity=discord.Game(name="!파티 봇 안내! 입력"))

async def send_reminder(message, target_time, remind_time):
    try:
        wait_seconds = (remind_time - datetime.now()).total_seconds()
        if wait_seconds > 0:
            await asyncio.sleep(wait_seconds)

        messages = [msg async for msg in message.channel.history(limit=1, oldest_first=True)]
        starter_message = messages[0] if messages else None

        participants = set()
        if starter_message:
            for reaction in starter_message.reactions:
                emoji_name = reaction.emoji.name if hasattr(reaction.emoji, 'name') else str(reaction.emoji)
                if emoji_name in TARGET_EMOJIS:
                    async for user in reaction.users():
                        if not user.bot:
                            participants.add(user)

        if participants:
            mentions = " ".join([u.mention for u in participants])
            await message.channel.send(
                f"🔔 {mentions}\n**잠시 후 {target_time.strftime('%H:%M')}에 파티가 출발합니다!** 준비해주세요!"
            )
        else:
            await message.channel.send("🔔 파티 출발 15분 전입니다! (참여 이모지 반응이 없습니다.)")

        scheduled_tasks.pop(message.channel.id, None)
    except asyncio.CancelledError:
        pass
    except Exception as e:
        print(f"알림 전송 오류: {e}")

@client.event
async def on_message(message):
    if message.author.bot:
        return

    if message.content in ['!파티 봇 안내', '!파티봇 안내']:
        guide_msg = (
            "**🤖 마비노기 파티 모집 봇 안내**\n\n"
            "**1. 파티 모집 (자동 카운팅)**\n"
            "- 제목을 `[4인]` 또는 `[4~6인]` 형식으로 작성 시 인원 자동 카운트.\n"
            "- 이모지 반응 시 실시간 인원 체크 및 출발 알림.\n\n"
            "**2. 파티 출발 알림 (!알림)**\n"
            "- 예: `!알림 2월 3일 15:00` 입력 시 출발 15분 전 참여자 멘션.\n\n"
            "**3. 알림 삭제**\n"
            "- `!알림 삭제` 입력 시 현재 채널의 예약 알림 취소."
        )
        await message.channel.send(guide_msg)
        return

    if message.content == '!알림 삭제':
        if message.channel.id in scheduled_tasks:
            scheduled_tasks[message.channel.id].cancel()
            del scheduled_tasks[message.channel.id]
            await message.channel.send("🗑️ 예약된 알림이 취소되었습니다.")
        else:
            await message.channel.send("❌ 현재 이 채널에 예약된 알림이 없습니다.")
        return

    if message.content.startswith('!알림'):
        try:
            numbers = re.findall(r'\d+', message.content)
            if len(numbers) < 4:
                await message.channel.send("형식이 잘못되었습니다. 예: `!알림 2월 3일 15:00`")
                return
            month, day, hour, minute = map(int, numbers[:4])
            target_time = datetime.now().replace(month=month, day=day, hour=hour, minute=minute, second=0, microsecond=0)
            if target_time < datetime.now():
                target_time = target_time.replace(year=datetime.now().year + 1)
            remind_time = target_time - timedelta(minutes=15)
            if remind_time < datetime.now():
                await message.channel.send("⚠️ 알림 시간(출발 15분 전)이 이미 지났습니다!")
                return
            if message.channel.id in scheduled_tasks:
                scheduled_tasks[message.channel.id].cancel()
            task = asyncio.create_task(send_reminder(message, target_time, remind_time))
            scheduled_tasks[message.channel.id] = task
            await message.channel.send(f"⏰ 알림 예약 완료! ({remind_time.strftime('%m/%d %H:%M')} 알림 예정)")
        except Exception as e:
            await message.channel.send(f"오류가 발생했습니다: {e}")

@client.event
async def on_raw_reaction_add(payload):
    if payload.user_id == client.user.id:
        return
    channel = client.get_channel(payload.channel_id)
    try:
        message = await channel.fetch_message(payload.message_id)
    except:
        return

    thread_title = channel.name
    match = re.search(r'\[(\d+)(?:~(\d+))?인\]', thread_title)
    if not match:
        return

    min_count = int(match.group(1))
    max_count = int(match.group(2)) if match.group(2) else min_count

    payload_emoji_name = payload.emoji.name if payload.emoji.name else str(payload.emoji)
    if payload_emoji_name not in TARGET_EMOJIS:
        return

    participants_list = []
    for reaction in message.reactions:
        emoji_name = reaction.emoji.name if hasattr(reaction.emoji, 'name') else str(reaction.emoji)
        if emoji_name in TARGET_EMOJIS:
            async for user in reaction.users():
                if not user.bot:
                    participants_list.append(user)

    current_count = len(participants_list)
    history = [msg async for msg in channel.history(limit=5)]

    if current_count >= max_count:
        if not any("모집 완료" in m.content for m in history):
            mentions = " ".join([u.mention for u in set(participants_list)])
            await channel.send(f"🎉 **[파티 모집 완료]** {max_count}명 달성! {mentions} 님들 일정 확인해주세요!")
    elif current_count >= min_count:
        if not any("최소 인원 달성" in m.content for m in history):
            await channel.send(f"📢 **[최소 인원 달성]** 현재 {current_count}명입니다! 출발 가능한 인원이 모였습니다.")

client.run(token)
