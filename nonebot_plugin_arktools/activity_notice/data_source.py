import httpx
import os
import json
import asyncio
import base64

from lxml import etree
from nonebot import get_driver, logger

from PIL import Image
from .._utils import async_GET
from .._utils import get_browser
from nonebot.adapters.onebot.v11 import MessageSegment
from playwright._impl._api_types import TimeoutError
from nonebot.adapters.onebot.v11 import Message
from io import BytesIO

from .config import Config

activity_config = Config.parse_obj(get_driver().config.dict())
DATA_PATH = activity_config.activities_data_path
IMG_PATH = activity_config.activities_img_path


async def get_activities(*, is_force: bool = False, is_cover: bool = False):
    """获取近期活动"""
    activity_data = {}
    announcement_url = "https://ak.hypergryph.com/news.html"
    result = None
    for retry in range(5):
        try:
            result = await async_GET(url=announcement_url)
        except httpx.TimeoutException:
            logger.warning(f"获取方舟近期活动第{retry + 1}次失败...")
            continue
        else:
            break
    if not result:
        return None
    text = result.text
    dom = etree.HTML(text, etree.HTMLParser())
    activity_urls = dom.xpath(
        "//ol[@class='articleList' and @data-category-key='ACTIVITY']/li/a/@href"
    )[:3]
    activity_titles = dom.xpath(
        "//ol[@class='articleList' and @data-category-key='ACTIVITY']/li/a/h1/text()"
    )[:3]
    activity_times = dom.xpath(
        "//ol[@class='articleList' and @data-category-key='ACTIVITY']/li/a/span[@class='articleItemDate']/text()"
    )[:3]
    for idx, time in enumerate(activity_times):
        activity_data[time] = {
            "url": f"https://ak.hypergryph.com{activity_urls[idx]}",
            "title": activity_titles[idx].strip()
        }
    if not os.path.exists(DATA_PATH):
        os.makedirs(DATA_PATH)
    if not os.path.exists(DATA_PATH / "activities.json"):
        with open(DATA_PATH / "activities.json", 'w', encoding='utf-8') as f:
            json.dump({}, f)
    update_flag = await write_in_data(activity_data, activity_times[0])
    if update_flag or is_force:
        latest = activity_times[0]
        msg = await get_latest_info(activity_data, latest, is_cover=is_cover)
        if msg:
            return msg
        return None
    return None


async def write_in_data(activity_data: dict, latest: str) -> bool:
    """把最新的三条活动信息写入文件"""
    update_flag = False
    with open(DATA_PATH / "activities.json", 'r', encoding='utf-8') as f_read:
        old_data = json.load(f_read)
        if old_data and old_data['latest'] not in activity_data.keys():
            update_flag = True
            with open(DATA_PATH / "activities.json", 'w', encoding='utf-8') as f_write:
                json.dump(
                    {"latest": latest, "details": activity_data}
                    , f_write
                )
    return update_flag


async def get_latest_info(activity_data: dict, latest: str, *, is_cover: bool = False):
    """截图最新活动"""
    if not os.path.exists(IMG_PATH):
        os.makedirs(IMG_PATH)

    value = activity_data[latest]
    url = value['url']
    title = value['title']
    file_name = IMG_PATH / f"{title}.png"
    if file_name.exists() and not is_cover:
        return Message(
            f"{MessageSegment.image(file_name)}"
            f"{title}\n"
            f"公告更新日期(不是活动开始日期): {latest}\n"
            f"数据来源于: {url}"
        )

    page = None
    for retry in range(3):
        try:
            browser = await get_browser()
            if not browser:
                return None
            page = await browser.new_page()
            await page.goto(url, timeout=10000)
            await page.set_viewport_size({"width": 960, "height": 1080})
            await asyncio.sleep(1)
            screenshot = await page.screenshot(full_page=True, type='jpeg', quality=50)
        except TimeoutError:
            logger.warning(f"第{retry + 1}次获取方舟活动截图失败……")
            continue
        except Exception as e:
            if page:
                await page.close()
            logger.error(f"方舟活动截图失败！ - {type(e)}: {e}")
            return None
        else:
            await page.close()
            b_scr = BytesIO(screenshot)
            img = Image.open(b_scr)
            img.save(file_name)
            return Message(
                f"{MessageSegment.image(base64.b64encode(screenshot))}"
                f"{title}\n"
                f"公告更新日期: {latest}\n"
                f"数据来源于: {url}"
            )
    if page:
        await page.close()
    return None
