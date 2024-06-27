![](https://socialify.git.ci/xxtg666/nonebot-plugin-discord-message-bridge/image?description=1&forks=1&issues=1&language=1&logo=https://raw.githubusercontent.com/xxtg666/nonebot-plugin-discord-message-bridge/master/docs/nbp_logo.png&name=1&owner=1&pulls=1&stargazers=1&theme=Light)

<div align="center">

<a href="./LICENSE">
    <img src="https://img.shields.io/github/license/xxtg666/nonebot-plugin-discord-message-bridge.svg?style=for-the-badge" alt="license">
</a>

<img src="https://img.shields.io/badge/python-3.10+-blue.svg?style=for-the-badge" alt="python">

<a href="https://github.com/psf/black">
    <img src="https://img.shields.io/badge/code%20style-black-000000.svg?style=for-the-badge" alt="Code style: black">
</a>

</div>

## 📖 介绍

将 QQ 与 Discord 的消息互通，并支持转发**图片**、**回复**、**提及(@)**

## 💿 安装

目前只提供了 GitHub 下载源码安装方式

## ⚙️ 配置

请修改 -> [🔗config.py](https://github.com/xxtg666/nonebot-plugin-discord-message-bridge/blob/main/config.py)

- 需要 [🔗创建一个 Discord Bot](https://discord.com/developers/applications) 并邀请进入服务器中，用于接收消息
- 需要在 Discord 的 「服务器设置 → 整合」 内为需要转发的频道创建一个 Webhook ，并填入配置文件中，用于发送 QQ 内的消息


## 🎉 使用

- 在 QQ 群内收到一条消息时会启动 Discord 接收端，转发即可正常使用
- 用户在 Discord 内发送绑定命令 (默认为 `~`) 后可转发提及(@)