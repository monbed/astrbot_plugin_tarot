<div align="center">

# Tarot

_🔮 赛博塔罗牌 🔮_

</div>

<p align="center">

  <a href="https://github.com/MinatoAquaCrews/nonebot_plugin_tarot/blob/master/LICENSE">
    <img src="https://img.shields.io/github/license/MinatoAquaCrews/nonebot_plugin_tarot?color=blue">
  </a>

  <a href="https://github.com/nonebot/nonebot2">
    <img src="https://img.shields.io/badge/nonebot2-2.0.0b3+-green">
  </a>

  <a href="https://github.com/MinatoAquaCrews/nonebot_plugin_tarot/releases/tag/v0.4.0.post4">
    <img src="https://img.shields.io/github/v/release/MinatoAquaCrews/nonebot_plugin_tarot?color=orange">
  </a>

  <a href="https://www.codefactor.io/repository/github/MinatoAquaCrews/nonebot_plugin_tarot">
    <img src="https://img.shields.io/codefactor/grade/github/MinatoAquaCrews/nonebot_plugin_tarot/master?color=red">
  </a>

  <a href="https://github.com/MinatoAquaCrews/nonebot_plugin_tarot">
    <img src="https://img.shields.io/pypi/dm/nonebot_plugin_tarot">
  </a>

  <a href="https://results.pre-commit.ci/latest/github/MinatoAquaCrews/nonebot_plugin_tarot/master">
	<img src="https://results.pre-commit.ci/badge/github/MinatoAquaCrews/nonebot_plugin_tarot/master.svg" alt="pre-commit.ci status">
  </a>

</p>

## 序

_“许多傻瓜对千奇百怪的迷信说法深信不疑：象牙、护身符、黑猫、打翻的盐罐、驱邪、占卜、符咒、毒眼、塔罗牌、星象、水晶球、咖啡渣、手相、预兆、预言还有星座。”——《人类愚蠢辞典》_

## 版本

🧰 [v0.1.0](https://github.com/yzjmxy/astrbot_plugin_tarot)

⚠ 适配astrbot v3.4.39

👉 [如何添加新的塔罗牌主题资源？](./How-to-add-new-tarot-theme.md)欢迎贡献！🙏

## 安装

暂时需要下载自行放入插件目录。

## 命令

1. [占卜] 随机选取牌阵进行占卜并提供 AI 解析，可附加关键词（如 '占卜 情感'）匹配牌阵；

2. [塔罗牌] 得到单张塔罗牌回应及 AI 解析；

3. [开启/关闭群聊转发] 切换群聊转发模式。

## 资源说明

1. 韦特塔罗(Waite Tarot)包括22张大阿卡纳(Major Arcana)牌与权杖(Wands)、星币(Pentacles)、圣杯(Cups)、宝剑(Swords)各系14张的小阿卡纳(Minor Arcana)共56张牌组成，其中国王、皇后、骑士、侍从也称为宫廷牌(Court Cards)；

   - BilibiliTarot：B站幻星集主题塔罗牌
   - TouhouTarot：东方主题塔罗牌，仅包含大阿卡纳

   ⚠ 资源中额外四张王牌(Ace)不在体系中，因此不会在占卜时用到，因为小阿卡纳中各系均有Ace牌，但可以自行收藏。

2. `tarot.json`中对牌阵，抽牌张数、是否有切牌、各牌正逆位解读进行说明。`cards` 字段下对所有塔罗牌做了正逆位含义与资源路径的说明；

3. 根据牌阵的不同有不同的塔罗牌解读，同时也与问卜者的问题、占卜者的解读等因素相关，因此不存在所谓的解读方式正确与否。`cards` 字段下的正逆位含义参考以下以及其他网络资源：

   - 《棱镜/耀光塔罗牌中文翻译》，中华塔罗会馆(CNTAROT)，版权原因恕不提供
   - [AlerHugu3s/PluginVoodoo](https://github.com/AlerHugu3s/PluginVoodoo/blob/master/data/PluginVoodoo/TarotData/Tarots.json)
   - [塔罗.中国](https://tarotchina.net/)
   - [塔罗牌](http://www.taluo.org/)
   - [灵匣](https://www.lnka.cn/)

   🤔 也可以说是作者的解读版本

## 本插件改自

1. [真寻bot插件库/tarot](https://github.com/AkashiCoin/nonebot_plugins_zhenxun_bot)

2. [haha114514/tarot_hoshino](https://github.com/haha114514/tarot_hoshino)

3.  [hMinatoAquaCrews/nonebot_plugin_tarot](https://github.com/MinatoAquaCrews/nonebot_plugin_tarot)
