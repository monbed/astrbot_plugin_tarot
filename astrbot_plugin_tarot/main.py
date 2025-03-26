import asyncio
import random
from io import BytesIO
from pathlib import Path
from typing import Dict, List, Tuple, Union

import PIL.Image
from astrbot.api.all import *
from astrbot.api.event import filter, AstrMessageEvent
import logging
import os
import json
import re

logger = logging.getLogger(__name__)

class Tarot:
    def __init__(self, context: Context, config: AstrBotConfig):
        self.context = context
        self.tarot_json: Path = Path(__file__).parent / "tarot.json"
        resource_path_str: str = config.get("resource_path", "resource")
        self.resource_path: Path = Path(__file__).parent / resource_path_str
        self.is_chain_reply: bool = config.get("chain_reply", True)
        self.include_ai_in_chain: bool = config.get("include_ai_in_chain", False)  # 新增配置项
        
        os.makedirs(self.resource_path, exist_ok=True)
        if not self.tarot_json.exists():
            logger.error("tarot.json 文件缺失，请确保资源完整！")
            raise Exception("tarot.json 文件缺失，请确保资源完整！")
        logger.info(f"Tarot 插件初始化完成，资源路径: {self.resource_path}, AI 解析加入转发: {self.include_ai_in_chain}")

    def pick_theme(self) -> str:
        sub_themes_dir: List[str] = [f.name for f in self.resource_path.iterdir() if f.is_dir()]
        if not sub_themes_dir:
            logger.error("本地塔罗牌主题为空，请检查资源目录！")
            raise Exception("本地塔罗牌主题为空，请检查资源目录！")
        return random.choice(sub_themes_dir)

    def pick_sub_types(self, theme: str) -> List[str]:
        all_sub_types: List[str] = ["MajorArcana", "Cups", "Pentacles", "Swords", "Wands"]
        sub_types: List[str] = [
            f.name for f in (self.resource_path / theme).iterdir()
            if f.is_dir() and f.name in all_sub_types
        ]
        return sub_types or all_sub_types

    def _random_cards(self, all_cards: Dict, theme: str, num: int = 1) -> List[Dict]:
        sub_types: List[str] = self.pick_sub_types(theme)
        if not sub_types:
            logger.error(f"主题 {theme} 下无可用子类型！")
            raise Exception(f"主题 {theme} 下无可用子类型！")
        subset: Dict = {k: v for k, v in all_cards.items() if v.get("type") in sub_types}
        if len(subset) < num:
            logger.error(f"主题 {theme} 的牌数量不足，需要 {num} 张，实际 {len(subset)} 张！")
            raise Exception(f"主题 {theme} 的牌数量不足！")
        cards_index: List[str] = random.sample(list(subset), num)
        return [v for k, v in subset.items() if k in cards_index]

    async def _get_text_and_image(self, theme: str, card_info: Dict) -> Tuple[bool, str, str, bool]:
        try:
            _type: str = card_info.get("type")
            _name: str = card_info.get("pic")
            img_dir: Path = self.resource_path / theme / _type
            
            img_name = ""
            for p in img_dir.glob(_name + ".*"):
                img_name = p.name
                break
            
            if not img_name:
                logger.warning(f"图片 {theme}/{_type}/{_name} 不存在！")
                return False, f"图片 {theme}/{_type}/{_name} 不存在，请检查资源完整性！", "", True
            
            img_path = img_dir / img_name
            with PIL.Image.open(img_path) as img:
                name_cn: str = card_info.get("name_cn")
                meaning = card_info.get("meaning")
                is_upright = random.random() < 0.5
                text = f"「{name_cn}{'正位' if is_upright else '逆位'}」「{meaning['up' if is_upright else 'down']}」\n"
                if not is_upright:
                    rotated_img_name = f"{_name}_rotated.png"
                    rotated_img_path = img_dir / rotated_img_name
                    if not rotated_img_path.exists():
                        img = img.rotate(180)
                        img.save(rotated_img_path, format="png")
                        logger.info(f"保存旋转后的图片: {rotated_img_path}")
                    else:
                        logger.info(f"使用已存在的旋转图片: {rotated_img_path}")
                    final_path = str(rotated_img_path.resolve())
                else:
                    final_path = str(img_path.resolve())
                
                if not os.path.exists(final_path):
                    logger.error(f"图片文件不存在: {final_path}")
                    return False, f"图片文件 {final_path} 不存在！", "", True
                logger.info(f"使用图片路径: {final_path}")
                return True, text, final_path, is_upright
        except Exception as e:
            logger.error(f"处理图片失败: {str(e)}")
            return False, f"处理塔罗牌图片失败: {str(e)}", "", True

    async def _match_formation(self, text: str, all_formations: Dict) -> str:
        """模糊匹配牌阵或调用 AI 分析用户意图"""
        text = text.strip().lower()
        formation_names = list(all_formations.keys())

        # 直接模糊匹配
        keywords = ["情感", "爱情", "关系", "事业", "工作", "未来", "过去", "现状", "处境", "挑战", "建议"]
        for formation in formation_names:
            for keyword in keywords:
                if keyword in text and keyword in " ".join(all_formations[formation]["representations"][0]).lower():
                    logger.info(f"模糊匹配成功：用户输入 '{text}' 匹配到牌阵 '{formation}'")
                    return formation

        # 调用 AI 分析用户意图
        prompt = f"用户输入了以下占卜指令：'{text}'。请根据输入内容，从以下牌阵中选择一个最匹配的牌阵并返回其名称（仅返回名称，无需解释）：\n{', '.join(formation_names)}\n如果无法明确匹配，返回 '随机选择'。"
        try:
            llm_response = await self.context.get_using_provider().text_chat(
                prompt=prompt,
                session_id=None,
                contexts=[],
                image_urls=[],
                system_prompt="你是一个塔罗牌专家，擅长根据用户意图选择合适的牌阵。"
            )
            matched_formation = llm_response.completion_text.strip()
            if matched_formation == "随机选择" or matched_formation not in formation_names:
                logger.info(f"AI 匹配失败或返回随机选择，用户输入: '{text}'")
                return random.choice(formation_names)
            logger.info(f"AI 匹配成功：用户输入 '{text}' 匹配到牌阵 '{matched_formation}'")
            return matched_formation
        except Exception as e:
            logger.error(f"AI 匹配牌阵失败: {str(e)}")
            return random.choice(formation_names)

    async def _generate_ai_interpretation(self, formation_name: str, cards_info: List[Dict], representations: List[str], is_upright_list: List[bool], user_input: str) -> str:
        """生成 AI 解析，包含用户输入的完整指令"""
        prompt = f"你是一位专业的塔罗牌占卜师，用户输入了以下完整占卜指令：'{user_input}'。\n请根据以下信息为用户提供详细的占卜结果解析：\n\n"
        prompt += f"牌阵：{formation_name}\n"
        prompt += "抽到的牌及位置：\n"
        for i, (card, rep, is_upright) in enumerate(zip(cards_info, representations, is_upright_list)):
            position = f"第{i+1}张牌「{rep}」"
            card_text = f"「{card['name_cn']}{'正位' if is_upright else '逆位'}」「{card['meaning']['up' if is_upright else 'down']}」"
            prompt += f"{position}: {card_text}\n"
        prompt += "\n请结合用户指令、牌阵的含义和每张牌的具体位置，提供一个连贯的解析，解释这些牌可能对用户的生活、情感或决策的启示。回答需简洁但有深度，约200-300字。同时请确保解析结果整洁、可阅读性强，善用换行与颜表情（如😊、✨、🌟等）进行美化。"

        try:
            llm_response = await self.context.get_using_provider().text_chat(
                prompt=prompt,
                session_id=None,
                contexts=[],
                image_urls=[],
                system_prompt="你是一个专业的塔罗牌占卜师，擅长提供深入且简洁的解析。"
            )
            return llm_response.completion_text.strip()
        except Exception as e:
            logger.error(f"生成 AI 解析失败: {str(e)}")
            return "抱歉，AI 解析生成失败，请稍后再试。"

    async def divine(self, event: AstrMessageEvent, user_input: str = ""):
        try:
            theme: str = self.pick_theme()
            with open(self.tarot_json, 'r', encoding='utf-8') as f:
                content = json.load(f)
                all_cards = content.get("cards")
                all_formations = content.get("formations")
                formation_name = await self._match_formation(user_input, all_formations)
                formation = all_formations.get(formation_name)

            yield event.plain_result(f"启用{formation_name}，正在洗牌中...")
            cards_num: int = formation.get("cards_num")
            cards_info_list = self._random_cards(all_cards, theme, cards_num)
            is_cut: bool = formation.get("is_cut")
            representations: List[str] = random.choice(formation.get("representations"))
            is_upright_list = []
            results = []

            group_id = event.get_group_id()
            is_group_chat = group_id is not None

            if self.is_chain_reply and is_group_chat:
                chain = Nodes([])
                for i in range(cards_num):
                    header = f"切牌「{representations[i]}」\n" if (is_cut and i == cards_num - 1) else f"第{i+1}张牌「{representations[i]}」\n"
                    flag, text, img_path, is_upright = await self._get_text_and_image(theme, cards_info_list[i])
                    if not flag:
                        yield event.plain_result(text)
                        return
                    is_upright_list.append(is_upright)
                    node = Node(
                        uin=event.get_self_id(),
                        name=self.context.get_config().get("nickname", "占卜师"),
                        content=[Plain(header + text), Image.fromFileSystem(img_path)]
                    )
                    chain.nodes.append(node)
                    results.append((header, text, img_path))
                
                # 生成 AI 解析
                bot_name = self.context.get_config().get("nickname", "占卜师")
                interpretation = await self._generate_ai_interpretation(formation_name, cards_info_list, representations, is_upright_list, user_input)
                
                # 根据配置决定是否将 AI 解析加入转发
                if self.include_ai_in_chain:
                    ai_node = Node(
                        uin=event.get_self_id(),
                        name=bot_name,
                        content=[Plain(f"\n“属于你的占卜分析！”\n{interpretation}")]
                    )
                    chain.nodes.append(ai_node)
                
                if not chain.nodes:
                    yield event.plain_result("无法生成塔罗牌结果，请稍后重试")
                    return
                logger.info(f"群聊转发发送 {len(chain.nodes)} 张塔罗牌，AI 解析是否包含: {self.include_ai_in_chain}")
                yield event.chain_result([chain])
                
                # 如果 AI 解析未加入转发，则单独发送
                if not self.include_ai_in_chain:
                    yield event.plain_result(f"\n“属于你的占卜分析！”\n{interpretation}")
            else:
                for i in range(cards_num):
                    header = f"切牌「{representations[i]}」\n" if (is_cut and i == cards_num - 1) else f"第{i+1}张牌「{representations[i]}」\n"
                    flag, text, img_path, is_upright = await self._get_text_and_image(theme, cards_info_list[i])
                    if not flag:
                        yield event.plain_result(text)
                        return
                    is_upright_list.append(is_upright)
                    yield event.chain_result([Plain(header + text), Image.fromFileSystem(img_path)])
                    results.append((header, text, img_path))
                    if i < cards_num - 1:
                        await asyncio.sleep(2)

                # 非群聊转发模式，AI 解析单独发送
                bot_name = self.context.get_config().get("nickname", "占卜师")
                interpretation = await self._generate_ai_interpretation(formation_name, cards_info_list, representations, is_upright_list, user_input)
                yield event.plain_result(f"\n“属于你的占卜分析！”\n{interpretation}")
        except Exception as e:
            logger.error(f"占卜过程出错: {str(e)}")
            yield event.plain_result(f"占卜失败: {str(e)}")

    async def onetime_divine(self, event: AstrMessageEvent):
        try:
            theme: str = self.pick_theme()
            with open(self.tarot_json, 'r', encoding='utf-8') as f:
                content = json.load(f)
                all_cards = content.get("cards")
                card_info_list = self._random_cards(all_cards, theme)

            flag, text, img_path, is_upright = await self._get_text_and_image(theme, card_info_list[0])
            if flag:
                yield event.chain_result([Plain("回应是" + text), Image.fromFileSystem(img_path)])
                bot_name = self.context.get_config().get("nickname", "占卜师")
                interpretation = await self._generate_ai_interpretation("单张牌占卜", card_info_list, ["当前情况"], [is_upright], "塔罗牌")
                yield event.plain_result(f"\n“属于你的占卜分析！”\n{interpretation}")
            else:
                yield event.plain_result(text)
        except Exception as e:
            logger.error(f"单张占卜出错: {str(e)}")
            yield event.plain_result(f"单张占卜失败: {str(e)}")

    def switch_chain_reply(self, new_state: bool) -> str:
        self.is_chain_reply = new_state
        logger.info(f"群聊转发模式已切换为: {new_state}")
        return "占卜群聊转发模式已开启~" if new_state else "占卜群聊转发模式已关闭~"


@register("tarot", "XziXmn", "赛博塔罗牌占卜插件", "0.1.1")
class TarotPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.tarot = Tarot(context, config)

    @command("占卜")
    async def divine_handler(self, event: AstrMessageEvent, text: str = ""):
        try:
            if "帮助" in text:
                yield event.plain_result(
                    "赛博塔罗牌 v0.1.1\n"
                    "[占卜] 随机选取牌阵进行占卜并提供 AI 解析，可附加关键词（如 '占卜 情感'）匹配牌阵\n"
                    "[塔罗牌] 得到单张塔罗牌回应及 AI 解析\n"
                    "[开启/关闭群聊转发] 切换群聊转发模式"
                )
            else:
                async for result in self.tarot.divine(event, text):
                    yield result
            event.stop_event()
        except Exception as e:
            logger.error(f"处理占卜命令失败: {str(e)}")
            yield event.plain_result(f"占卜命令执行失败: {str(e)}")

    @command("塔罗牌")
    async def onetime_divine_handler(self, event: AstrMessageEvent, text: str = ""):
        try:
            if "帮助" in text:
                yield event.plain_result(
                    "赛博塔罗牌 v0.1.1\n"
                    "[占卜] 随机选取牌阵进行占卜并提供 AI 解析，可附加关键词（如 '占卜 情感'）匹配牌阵\n"
                    "[塔罗牌] 得到单张塔罗牌回应及 AI 解析\n"
                    "[开启/关闭群聊转发] 切换群聊转发模式"
                )
            else:
                async for result in self.tarot.onetime_divine(event):
                    yield result
            event.stop_event()
        except Exception as e:
            logger.error(f"处理塔罗牌命令失败: {str(e)}")
            yield event.plain_result(f"塔罗牌命令执行失败: {str(e)}")

    @command("开启群聊转发")
    async def enable_chain_reply(self, event: AstrMessageEvent, text: str = ""):
        try:
            msg = self.tarot.switch_chain_reply(True)
            yield event.plain_result(msg)
            event.stop_event()
        except Exception as e:
            logger.error(f"开启群聊转发失败: {str(e)}")
            yield event.plain_result(f"开启群聊转发失败: {str(e)}")

    @command("关闭群聊转发")
    async def disable_chain_reply(self, event: AstrMessageEvent, text: str = ""):
        try:
            msg = self.tarot.switch_chain_reply(False)
            yield event.plain_result(msg)
            event.stop_event()
        except Exception as e:
            logger.error(f"关闭群聊转发失败: {str(e)}")
            yield event.plain_result(f"关闭群聊转发失败: {str(e)}")
