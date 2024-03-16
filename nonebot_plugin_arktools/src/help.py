"""帮助"""
from .game_guess_operator import __plugin_meta__ as GUESS_META
from .misc_operator_birthday import __plugin_meta__ as BIRTHDAY_META
from .misc_monster_siren import __plugin_meta__ as SIREN_META
from .tool_announce_push import __plugin_meta__ as ANNOUNCE_META
from .tool_fetch_maa_copilot import __plugin_meta__ as MAA_META
from .tool_operator_info import __plugin_meta__ as INFO_META
from .tool_open_recruitment import __plugin_meta__ as RECRUIT_META
from .tool_sanity_notify import __plugin_meta__ as SAN_META
from .utils import __plugin_meta__ as UTILS_META

from nonebot import on_command, require
from nonebot.adapters.onebot.v11 import MessageSegment
from nonebot.matcher import Matcher

require("nonebot_plugin_htmlrender")
from nonebot_plugin_htmlrender import html_to_pic  # noqa: E402

HELP_DATAS = [
    GUESS_META,
    BIRTHDAY_META,
    SIREN_META,
    ANNOUNCE_META,
    MAA_META,
    INFO_META,
    RECRUIT_META,
    SAN_META,
    UTILS_META
]


help_msg = on_command("方舟帮助", aliases={"arkhelp"})

@help_msg.handle()
async def _(matcher: Matcher):
    result = ""
    for data in HELP_DATAS:
        _usage = data.usage.replace("\n", "</p><p>")
        result += f"""
            <p style="color: red; font-weight: bold;">
            {data.name}
            </p>
            <p>
            {data.description}
            </p>
            <p>
            {_usage}
            </p>
            <br>
            """
    await matcher.finish(MessageSegment.image(await html_to_pic(result)))
