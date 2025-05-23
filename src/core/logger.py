import logging
from datetime import datetime, timezone

from src.core.settings import Settings

"""Here we settings up logger with output to file & console"""


class UTCFormatter(logging.Formatter):
    def formatTime(self, record, datefmt=None):
        dt = datetime.fromtimestamp(record.created, tz=timezone.utc)
        if datefmt:
            s = dt.strftime(datefmt)
        else:
            t = dt.strftime("%Y-%m-%d %H:%M:%S")
            s = "%s,%03d" % (t, record.msecs)
        return s


logger = logging.getLogger("logger")
logger.setLevel(logging.INFO)

logger_format = "[%(asctime)s %(levelname)s] %(message)s"
date_format = "%m/%d/%Y %H:%M:%S"

file_handler = logging.FileHandler(Settings().LOG_PATH)
file_handler.setLevel(logging.INFO)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
formatter = UTCFormatter(logger_format, datefmt=date_format)

file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(console_handler)
