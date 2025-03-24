"""
抽卡
1. 获取卡池信息 (PRTS)
  - 卡池名称
  - 卡池封面
  - 卡池类型
    - 限时寻访
      - 非标准寻访
        - 春节池 (春节)
        - 跨年池 (跨年欢庆)
        - 周年池 (庆典)
        - 夏活池 (夏季)
        - 联动池 (else)
      - 标准寻访
        - 单up
        - 定向寻访
        - 联合行动
    - 常驻寻访
      - 标准寻访
      - 中坚寻访
    - 新手寻访
  - 开放时间
  - up干员
  - up概率
  - 能抽出的干员

2. 获取干员信息 (GITHUB)
  - gamedata
  - gameimage

3. 按概率随机

搓图函数create_gacha_image(list)

"""
from pathlib import Path
from nonebot.adapters.onebot.v11 import MessageSegment, Message
from nonebot.exception import MatcherException
from nonebot.rule import to_me
from nonebot import on_command, get_driver,logger,on_keyword
from PIL import Image, ImageDraw
from ..core.models_v3 import Character
from ..configs.path_config import PathConfig
import os,asyncio
from io import BytesIO

pcfg = PathConfig.parse_obj(get_driver().config.dict())
gameimage_path = Path(pcfg.arknights_gameimage_path).absolute()

curr_dir = os.path.dirname(__file__)
async def get_xi_character():
    try:
        # 调用 parse_name 方法，传入中文名 "夕"
        xi = await Character.parse_name("夕")
        return xi
    except Exception as e:
        print(f"未知错误: {e}")


async def get_gacha_results():
    tasks = [get_xi_character() for _ in range(10)]
    return await asyncio.gather(*tasks)


exec_gacha=on_keyword({"十连","抽卡"},rule=to_me())

@exec_gacha.handle()
async def handle_gacha():
    # 生成图片二进制数据
    lst = await get_gacha_results()
    img_bytes = create_gacha_image(lst)
    
    # 构造图片消息
    message = MessageSegment.image(img_bytes)
    
    # 发送消息
    await exec_gacha.send(message)


#item.item_obtain_approach=招募寻访









def create_gacha_image(result: list):
    """传入列表,每个元素为character类"""
    image = Image.open(gameimage_path / "gacha" / "bg.png")
    draw = ImageDraw.ImageDraw(image)

    x = 78
    for item in result:
        if item is None:
            x += 82
            continue

        rarity = gameimage_path / "gacha" / f"{item.rarity+1}.png"#character类型rarity属性范围为0-5，故需要+1
        if os.path.exists(rarity):
            img = Image.open(rarity).convert('RGBA')
            image.paste(img, box=(x, 0), mask=img)

        portraits = gameimage_path / "portraits" / f"{item.id}_1.png" #character类型id属性为干员标识符

        if os.path.exists(portraits):
            img = Image.open(portraits).convert('RGBA')

            radio = 252 / img.size[1]

            width = int(img.size[0] * radio)
            height = int(img.size[1] * radio)

            step = int((width - 82) / 2)
            crop = (step, 0, width - step, height)

            img = img.resize(size=(width, height))
            img = img.crop(crop)
            image.paste(img, box=(x, 112), mask=img)

        draw.rectangle((x + 10, 321, x + 70, 381), fill='white')
        class_img = gameimage_path / "classify" / f"{item.profession_id.lower()}.png" #character类型职业代号为全大写，需要转小写
        if os.path.exists(class_img):
            img = Image.open(class_img).convert('RGBA')
            img = img.resize(size=(59, 59))
            image.paste(img, box=(x + 11, 322), mask=img)

        x += 82

    x, y = image.size
    image = image.resize((int(x * 0.8), int(y * 0.8)), Image.LANCZOS)

    # 将图片保存到BytesIO对象
    img_bytes = BytesIO()
    image.save(img_bytes, format='PNG', quality=95)
    img_bytes.seek(0)  # 重置指针位置
    
    return img_bytes

