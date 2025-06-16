from dataclasses import dataclass, asdict
import json
import os

CONFIG_FILE = 'config.json'

@dataclass
class Config:
    world_dir: str | None = None
    campaign_dir: str | None = None
    case_sensitive: bool = False

def load_config() -> Config:
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return Config(**data)
        except Exception:
            pass
    return Config()


def save_config(cfg: Config) -> None:
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(asdict(cfg), f, indent=2)
