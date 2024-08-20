import yaml

from .local import safe_open


class CustomDumper(yaml.Dumper):
    def represent_none(self, data):
        return self.represent_scalar('tag:yaml.org,2002:null', '~')


CustomDumper.add_representer(type(None), CustomDumper.represent_none)

default_config_data = {
    'discord-bots': {
        1: 'XXX',
        2: 'XXX'
    },
    'discord-channels': {
        1: {
            'bot': 1,
            'guild-id': 123456,
            'channel-id': 123456,
            'webhook-url': 'https://discord.com/api/webhooks/123456/XXX'
        }
    },
    'qq-groups': {
        1: 123456
    },
    'forwards': [
        {
            'type': 0,
            'discord-channel': 1,
            'qq-group': 1
        }
    ]
}


def dump(data: dict, file_path: str):
    with safe_open(file_path, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, Dumper=CustomDumper, default_flow_style=False, allow_unicode=True)


def load(file_path: str) -> dict:
    with safe_open(file_path, 'r', encoding='utf-8') as f:
        return yaml.load(f, Loader=yaml.FullLoader)
