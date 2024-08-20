![](https://socialify.git.ci/xxtg666/nonebot-plugin-discord-message-bridge/image?description=1&forks=1&issues=1&language=1&logo=https://raw.githubusercontent.com/xxtg666/nonebot-plugin-discord-message-bridge/master/docs/nbp_logo.png&name=1&owner=1&pulls=1&stargazers=1&theme=Light)

<div align="center">

<a href="./LICENSE">
    <img src="https://img.shields.io/github/license/xxtg666/nonebot-plugin-discord-message-bridge.svg?style=for-the-badge" alt="license">
</a>

<a href="https://pypi.python.org/pypi/nonebot-plugin-discord-message-bridge">
    <img src="https://img.shields.io/pypi/v/nonebot-plugin-discord-message-bridge.svg?style=for-the-badge" alt="pypi">
</a>

<img src="https://img.shields.io/badge/python-3.9+-blue.svg?style=for-the-badge" alt="python">

<a href="https://github.com/psf/black">
    <img src="https://img.shields.io/badge/code%20style-black-000000.svg?style=for-the-badge" alt="Code style: black">
</a>

</div>

## 📖 介绍

将 QQ 与 Discord 的消息互通，并支持转发**图片**、**回复**、**提及(@)**

## 💿 安装

### 先决条件

在安装之前，请确保您的环境符合以下条件：

1. 拥有一个能够运行的 Python，版本在 3.9 及以上（本插件部分版本可能需要 3.12）
2. 已经安装并配置好 pip 等任意一款 Python3 包管理器
3. 已经创建或拥有了一个 NoneBot2 机器人项目

### 安装

<details>
<summary>通过文件安装</summary>

1. 在您的 pyproject.toml 中配置一个插件目录
```toml
plugin_dirs = ["src/plugins"]
```
> 您需要确保此目录存在，下文将使用 `插件目录` 代指此目录。
2. [下载本仓库](https://github.com/xxtg666/nonebot-plugin-discord-message-bridge/archive/refs/heads/main.zip)
3. 将 `nonebot-plugin-discord-message-bridge-main` 文件夹中的 `nonebot_plugin_discord_message_bridge` 文件夹解压到插件目录
4. 安装依赖
> 进入 `requirements.txt` 同目录下执行
```bash
pip install -r requirements.txt
```

</details>

<details>
<summary>通过 PIP 安装</summary>
    
1. 使用 pip 安装插件
```bash
pip install nonebot-plugin-discord-message-bridge
```
2. 修改 `pyproject.toml` 在 `plugins` 中添加 `nonebot_plugin_discord_message_bridge`

</details>

## ⚙️ 配置

请修改在机器人目录中创建一个 `.env` 文件（或编辑对应 `.env` 文件，可能为 `.env.dev` 或 `.env.prod`），并参考 [🔗config.py](https://github.com/xxtg666/nonebot-plugin-discord-message-bridge/blob/main/src/nonebot_plugin_discord_message_bridge/config.py) 的内容进行修改

- 需要 [🔗创建一个 Discord Bot](https://discord.com/developers/applications) 并邀请进入服务器中，用于接收消息
- 需要在 Discord 的 「服务器设置 → 整合」 内为需要转发的频道创建一个 Webhook ，并填入配置文件中，用于发送 QQ 内的消息


## 🎉 使用

- 在 QQ 群内收到一条消息时会启动 Discord 接收端，转发即可正常使用
- 用户在 Discord 内发送绑定命令 (默认为 `~`) 后可转发提及(@)
