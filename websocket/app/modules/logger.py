import json
import logging
import logging.config


class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        return json.dumps(log_data)


def get_logger(log_level: str = "INFO"):
    log_config = {
        "version": 1,
        "formatters": {
            "custom_formatter": {
                "()": JSONFormatter
            }
        },
        "handlers": {
            "console_handler": {
                "class": "logging.StreamHandler",
                "level": log_level,
                "formatter": "custom_formatter",
                "stream": "ext://sys.stdout"
            }
        },
        "root": {
            "level": log_level,
            "handlers": ["console_handler"]
        }
    }
    logging.config.dictConfig(log_config)

    return logging.getLogger()
