from datetime import datetime

from switch import join_root
import logging

from switch.utils import timesince


def get_app_logger():
    logger = logging.getLogger('switch.py')
    file_handler = logging.FileHandler(filename=join_root('app.log'))
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(
        logging.Formatter('%(asctime)s - %(module)s - [%(context)s] - %(levelname)s - %(message)s'))
    logger.addHandler(file_handler)
    logger.setLevel(logging.DEBUG)
    return logger


def get_frontend_logger():
    logger = logging.getLogger('switch.py-frontend')
    handler = FrontendHandler(level=logging.INFO)
    logging.Formatter('')
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger


class FrontendHandler(logging.Handler):
    def __init__(self, level=logging.NOTSET):
        self._records = []
        self.get_context_name = None
        super().__init__(level)

    def emit(self, record):
        self._records.append((datetime.fromtimestamp(record.created), record.context, record.getMessage()))

    def get_records(self):
        logs_records = []
        for date, context, message in self._records:
            logs_records.append((self.get_context_name(context), message, timesince(date), date.strftime('%c')))
        logs_records.reverse()
        return logs_records

app_logger = get_app_logger()
frontend_logger = get_frontend_logger()
frontend_handler = frontend_logger.handlers[0]
