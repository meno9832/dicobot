import discord
from discord.ext import commands
from datetime import datetime, timezone, timedelta
import random

# 봇 설정
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)
env: BOT_TOKEN: ${{ secrets.BOT_TOKEN }}

# 시작 메시지 ID 저장
start_msg_id = None

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

@bot.command()
async def start(ctx):
    """
    시작 메시지 ID 저장.
    """
    global start_msg_id
    start_msg_id = await get_start_message_id(ctx)
    if start_msg_id:
        await ctx.send(f"시작 메시지 ID가 설정되었습니다: {start_msg_id}")

@bot.command()
async def end(ctx):
    """
    종료 메시지 ID를 받아 백업 실행.
    """
    global start_msg_id
    if not start_msg_id:
        await ctx.send("먼저 시작 메시지를 설정해야 합니다.")
        return

    end_msg_id = await get_end_message_id(ctx)
    if end_msg_id:
        await ctx.send(f"종료 메시지 ID: {end_msg_id}. 백업을 시작합니다.")
        await backup_user_messages(ctx, start_msg_id, end_msg_id)
        start_msg_id = None  # 초기화

# 위에 정의한 함수들 포함
async def get_start_message_id(ctx):
    if ctx.message.reference:
        return ctx.message.reference.message_id
    await ctx.send("시작 메시지에 답장해주세요.")
    return None

async def get_end_message_id(ctx):
    if ctx.message.reference:
        return ctx.message.reference.message_id
    await ctx.send("종료 메시지에 답장해주세요.")
    return None

async def backup_user_messages(ctx, start_msg_id, end_msg_id=None):
    """
    Discord 메시지를 HTML 형식으로 백업 (종료 메시지 ID 포함).
    """
    try:
        channel = ctx.channel
        after = await channel.fetch_message(start_msg_id)  # 시작 메시지 기준
        messages = []
        limit = 1000  # 가져올 메시지 총 개수

        while True:
            fetched = []
            async for message in channel.history(after=after, limit=100, oldest_first=True):
                # 종료 메시지 도달 시 루프 종료
                if message.id == end_msg_id:
                    fetched.append(message)  # 종료 메시지 포함
                    messages.append({
                        "author": message.author.display_name,
                        "avatar": message.author.avatar.url if message.author.avatar else "https://cdn.discordapp.com/embed/avatars/0.png",
                        "content": message.content or "(내용 없음)",
                        "timestamp": message.created_at.astimezone(timezone(timedelta(hours=9))).strftime("%Y년 %m월 %d일 %p %I:%M:%S"),
                        "reply": f"↳ {message.reference.resolved.author.display_name}: {message.reference.resolved.content}" if message.reference and message.reference.resolved else None,
                    })
                    break  # 종료 메시지를 포함하고 종료

                # 메시지 데이터 추가
                messages.append({
                    "author": message.author.display_name,
                    "avatar": message.author.avatar.url if message.author.avatar else "https://cdn.discordapp.com/embed/avatars/0.png",
                    "content": message.content or "(내용 없음)",
                    "timestamp": message.created_at.astimezone(timezone(timedelta(hours=9))).strftime("%Y년 %m월 %d일 %p %I:%M:%S"),
                    "reply": f"↳ {message.reference.resolved.author.display_name}: {message.reference.resolved.content}" if message.reference and message.reference.resolved else None,
                })
                fetched.append(message)
                after = message

            if not fetched or len(messages) >= limit or fetched[-1].id == end_msg_id:
                break  # 종료 조건: 더 이상 메시지가 없거나 제한에 도달하거나 종료 메시지 도달

        # HTML 작성
        message_html = """"""

        for msg in messages:
            reply_html = f'<div class="reply" style="margin-top: 5px; font-size: 0.9em; color: #b9bbbe;">{msg["reply"]}</div>' if msg["reply"] else ""
            message_html += f"""
            <div class="message" style="display: flex; align-items: flex-start; padding: 10px; background-color: #2f3136;">
                <img class="avatar" src="{msg['avatar']}" alt="Avatar" style="width: 40px; height: 40px; border-radius: 50%; margin-right: 15px;">
                <div class="content" style="flex: 1;">
                    <div class="username" style="font-weight: bold; color: #7289da; margin-bottom: 5px;">{msg['author']}<span class="timestamp" style="font-size: 0.8em; color: #72767d; margin-left: 10px;">{msg['timestamp']}</span></div>
                    <p class="message-text" style="margin: 0; color: #dcddde;">{msg['content']}</p>
                    {reply_html}
                </div>
            </div>
            """

        # HTML 파일 저장
        with open("chat_backup.html", "w", encoding="utf-8") as file:
            file.write(message_html)

        await ctx.send("백업이 완료되었습니다! 아래 파일을 확인하세요:", file=discord.File("chat_backup.html"))
    except Exception as e:
        await ctx.send(f"오류 발생: {e}")



def dx_roll(dice_count, critical_value):
    """
    DX 주사위 판정.
    :param dice_count: 굴릴 주사위 개수
    :param critical_value: 크리티컬 값
    :return: 판정 결과 (최종 합계와 굴림 세부 내역)
    """
    try:
        # 판정 초기화
        total_sum = 0
        round_results = []
        round_num = 1

        while dice_count > 0:
            # 주사위 굴림
            rolls = [random.randint(1, 10) for _ in range(dice_count)]
            max_roll = max(rolls)
            if max_roll >= critical_value:
                max_roll = 10
            round_results.append((round_num, rolls, max_roll))

            # 현재 라운드 최대값을 총합에 추가
            total_sum += max_roll

            # 크리티컬 적용: critical_value 이상인 주사위는 추가 굴림
            dice_count = sum(1 for roll in rolls if roll >= critical_value)
            round_num += 1

        return total_sum, round_results
    except Exception as e:
        return f"오류: {e}"

# !dxroll 명령어
@bot.command()
async def dx(ctx, *, input_string: str):
    """
    DX 판정 주사위 굴림.
    입력 형식: NdX (예: 3dx8)
    """
    try:
        # 입력 파싱 (예: 3dx8)
        parts = input_string.lower().split("dx")
        dice_count = int(parts[0])
        critical_value = int(parts[1])

        if critical_value < 2 or critical_value > 10:
            await ctx.send("크리티컬 값은 2 이상 10 이하여야 합니다!")
            return

        # DX 판정 실행
        total_sum, round_results = dx_roll(dice_count, critical_value)

        # 결과 생성
        result_message = "🎲 **DX 판정 결과** 🎲\n"
        for round_num, rolls, max_roll in round_results:
            result_message += f"{max_roll}{rolls} +"
        result_message = result_message[:-1]
        result_message += f"\n**최종 합계**: {total_sum}"

        await ctx.send(result_message)
    except Exception as e:
        await ctx.send(f"오류 발생: {e}")


@bot.command()
async def 덥하아사(ctx):
        # DX 판정 실행
        total_sum, round_results = dx_roll(1,2)

        # 결과 생성
        result_message = "🎲 **DX 판정 결과** 🎲\n"
        for round_num, rolls, max_roll in round_results:
            result_message += f"{max_roll}{rolls} +"
        result_message = result_message[:-1]
        result_message += f"\n**최종 합계**: {total_sum}"

        await ctx.send(result_message)

# 봇 실행
bot.run(BOT_TOKEN)
