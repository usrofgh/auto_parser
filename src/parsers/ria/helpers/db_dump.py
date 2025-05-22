import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from src.core.settings import Settings


def make_dump():
    settings = Settings()

    db_name = settings.POSTGRES_DB
    dumps_dir = Path(__file__).parent.parent.parent.parent.parent / "dumps"
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    dump_name = f"{db_name}_{timestamp}.sql"
    dumb_path = dumps_dir.joinpath(dump_name)
    cmd = [
        "pg_dump",
        "-U", settings.POSTGRES_USER,
        "-h", settings.POSTGRES_HOST,
        db_name,
    ]

    env = os.environ.copy()
    env["PGPASSWORD"] = settings.POSTGRES_PASSWORD.get_secret_value()
    with dumb_path.open("wb") as f:
        subprocess.run(cmd, env=env, stdout=f, check=True)


if __name__ == "__main__":
    make_dump()
