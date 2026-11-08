from pathlib import Path

from decouple import Config, RepositoryEnv


BASE_DIR = Path(__file__).resolve().parent.parent

env_path = BASE_DIR / "settings" / ".env"

config = Config(RepositoryEnv(str(env_path)))