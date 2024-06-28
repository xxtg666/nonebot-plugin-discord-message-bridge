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

### 1. 创建一个新的 NoneBot2 机器人

> 如果您需要将本插件安装到现有的机器人，可忽略此步骤

注意在 `pyproject.toml` 中配置一个 `plugin_dirs`，可以参考以下设置：

```toml
plugin_dirs = ["src/plugins"]
```

> [!TIP]
> 在配置完成后您需要在机器人工作目录新建此文件夹，下文将使用 `插件目录` 代指此目录。

### 2. 安装插件

您可以选择以下两种安装方式

<details>
<summary>使用 Git 子模块安装</summary>

> [!TIP]
> 此方法需要您能够使用 git 并已经在机器人目录下初始化 git 仓库

请将以下指令的 `src/plugins/` 替换为您的插件目录

```bash
git submodule add https://github.com/xxtg666/nonebot-plugin-discord-message-bridge src/plugins/nonebot_plugin_discord_message_bridge
git submodule update --init --recursive
```

</details>


<details>
<summary>使用文件</summary>

1. [下载本仓库](https://github.com/xxtg666/nonebot-plugin-discord-message-bridge/archive/refs/heads/main.zip)
2. 将 `nonebot-plugin-discord-message-bridge-main` 文件夹解压到插件目录，并重命名为 `nonebot_plugin_discord_message_bridge`

</details>

### 3. 安装依赖

经过步骤二后，您的插件应该被安装到了 `插件目录/nonebot_plugin_discord_message_bridge` 中，本步骤您需要进入 `插件目录/nonebot_plugin_discord_message_bridge` 安装本插件所需依赖

```bash
pip install -r requirements.txt
```

如果您使用了其他包管理器，请参考您所使用的包管理器的使用方法安装所需依赖

## ⚙️ 配置

请修改 -> [🔗config.py](https://github.com/xxtg666/nonebot-plugin-discord-message-bridge/blob/main/config.py)

- 需要 [🔗创建一个 Discord Bot](https://discord.com/developers/applications) 并邀请进入服务器中，用于接收消息
- 需要在 Discord 的 「服务器设置 → 整合」 内为需要转发的频道创建一个 Webhook ，并填入配置文件中，用于发送 QQ 内的消息


## 🎉 使用

- 在 QQ 群内收到一条消息时会启动 Discord 接收端，转发即可正常使用
- 用户在 Discord 内发送绑定命令 (默认为 `~`) 后可转发提及(@)
