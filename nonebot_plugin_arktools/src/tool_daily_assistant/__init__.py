"""每日助理"""
from pathlib import Path
from nonebot.adapters.onebot.v11 import MessageEvent
from datetime import datetime, date
import hashlib
from nonebot import on_command, get_driver,logger,on_keyword
from nonebot.rule import to_me,Rule
from nonebot.plugin import PluginMetadata
from nonebot.adapters.onebot.v11 import MessageSegment, Message
from nonebot.exception import MatcherException
from datetime import datetime
from io import BytesIO
from random import choice
import json
import aiofiles
from ..core.models_v3 import Character
from ..configs.path_config import PathConfig



pcfg = PathConfig.parse_obj(get_driver().config.dict())
gameimage_path = Path(pcfg.arknights_gameimage_path).absolute()
charword_path = Path(pcfg.arknights_gamedata_path).absolute() / "excel" / "charword_table.json"

daily_assistant=on_command("今日助理",block=True)
daily_assistant=on_keyword({"助理"},rule=to_me(),block=True)

with open(charword_path,"r",encoding="utf-8") as f:
    charword = json.load(f)["charWords"]

@daily_assistant.handle()
async def _(event:MessageEvent):
    try:
        TODAY = datetime.now().date()
        user=event.get_user_id()
        characters = await Character.all()
        idx=int(hashlib.md5((str(user) + str(TODAY)).encode()).hexdigest(), 16) % len(characters)
        if user=="2323537709":
            idx=27
        assistant_name=characters[idx].name
        assistant_word=charword[characters[idx].id+"_CN_001"]["voiceText"]
        closet=[(i.id).replace('@','_')+'b.png' for i in (await characters[idx].get_skins())]
        now_skin=choice(closet)
        img_path=gameimage_path / "skin" / now_skin
        logger.info(f"尝试读取图片文件{img_path}")
        if not await aiofiles.os.path.exists(img_path):
            now_skin=now_skin.replace('#','_')
            img_path=gameimage_path / "skin" / now_skin
            logger.info(f"尝试读取图片文件{img_path}")
            if not await aiofiles.os.path.exists(img_path):
                retry_cnt=0
                while retry_cnt<5 and not await aiofiles.os.path.exists(img_path):
                    now_skin=choice(closet)
                    img_path=gameimage_path / "skin" / now_skin
                    logger.info(f"尝试读取图片文件{img_path}")
                    retry_cnt+=1
                if (retry_cnt==5 or not await aiofiles.os.path.exists(img_path)):
                    logger.error(f"图片文件不存在: {img_path}")
                    await daily_assistant.finish("今天的助理干员好像没准备好...")
        async with aiofiles.open(img_path, "rb") as f:
            img_data = await f.read() 
        await daily_assistant.finish(MessageSegment.at(event.get_user_id())+f"\n博士，您今天选到的助理是干员{assistant_name}呢!\n"+Message(MessageSegment.image(img_data))+f"\n“{assistant_word}”")
    except MatcherException:
        raise 
    except Exception as e:
        logger.error(f"今日助理生成失败: {str(e)}")
        await daily_assistant.finish("博士，助理系统暂时出了点问题...")

__plugin_meta__ = PluginMetadata(
    name="今日助理",
    description="选一位干员作为助理",
    usage=(
        "命令:"
        "\n    今日助理 => 选一位干员作为助理"
    ),
    extra={
        "name": "daily_assistant",
        "author": "cyxypa@foxmail.com",
        "version": "0.1.0"
    }
)