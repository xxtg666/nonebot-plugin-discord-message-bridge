# Repository Guidelines

## Project Structure & Module Organization
This repository is a Python plugin packaged under `src/nonebot_plugin_discord_message_bridge/`.

- `src/nonebot_plugin_discord_message_bridge/__init__.py`: plugin entry point
- `src/nonebot_plugin_discord_message_bridge/config.py`: configuration models and env binding
- `src/nonebot_plugin_discord_message_bridge/bots/`: Discord bot integration
- `src/nonebot_plugin_discord_message_bridge/utils/`: message forwarding, download, YAML, and local helpers
- `docs/`: reference assets and config examples, such as `docs/dmb-config-example.yaml`

Keep new code inside the package tree so imports remain compatible with `src`-layout packaging.

## Build, Test, and Development Commands
The repo does not include a dedicated build script or test runner, so use the standard Python workflow.

- `pip install -r requirements.txt`: install runtime dependencies for local development
- `pip install -e .`: install the plugin in editable mode from a host NoneBot project
- `python -m compileall src/nonebot_plugin_discord_message_bridge`: quick syntax check for all modules

Run the NoneBot host application from the parent project that loads this plugin; this repository is only the plugin package.

## Coding Style & Naming Conventions
Follow the existing Python style: 4-space indentation, `snake_case` for functions and modules, and `PascalCase` for classes. Keep functions small and prefer explicit names over abbreviations.

The README badges indicate `black` style, so format code to Black-compatible conventions even though no formatter config is checked in here. Keep imports tidy and avoid introducing unused helpers.

## Testing Guidelines
There is no in-repo automated test suite yet. When you change behavior, validate it with:

- `python -m compileall src/nonebot_plugin_discord_message_bridge`
- a local NoneBot runtime wired to a Discord bot and webhook

If you add tests, place them in a `tests/` directory and name files `test_*.py`.

## Commit & Pull Request Guidelines
Recent commits are short and imperative, often mixing a fix summary with version bumps, for example `fix a bug & bump version`. Keep commit subjects brief and outcome-focused.

Pull requests should describe the behavior change, note any config updates, and mention how you verified the plugin. Include screenshots or log snippets for Discord-facing changes, and update `README.md` or `docs/` when setup steps change.

## Security & Configuration Tips
Do not commit `.env` files, Discord bot tokens, or webhook URLs. Use `docs/dmb-config-example.yaml` and the settings defined in `config.py` as the source of truth for local configuration.
