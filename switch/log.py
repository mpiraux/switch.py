#
# This file is part of switch.py. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.
#


import json
import logging
import os
from datetime import datetime
from pathlib import Path
from threading import Lock

from switch import join_root
from switch.utils import timesince, DateTimeEncoder, DateTimeDecoder


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
        frontend_logs_path = join_root('data', 'frontend_logs.data')
        self._records = []
        if os.path.exists(frontend_logs_path):
            with open(frontend_logs_path, 'r') as f:
                for line in f.readlines():
                    self._records.append(json.loads(line, cls=DateTimeDecoder))
        else:
            Path(frontend_logs_path).touch()
        self._records_file = open(frontend_logs_path, 'a+')
        self._records_file_lock = Lock()
        self.get_context_name = None
        super().__init__(level)

    def emit(self, record):
        record = (datetime.fromtimestamp(record.created), record.context, record.getMessage())
        self._records.append(record)
        with self._records_file_lock:
            json.dump(record, self._records_file, cls=DateTimeEncoder)
            self._records_file.write('\n')
            self._records_file.flush()

    def get_records(self):
        logs_records = []
        for date, context, message in self._records:
            logs_records.append((self.get_context_name(context), message, timesince(date), date.strftime('%c')))
        logs_records.reverse()
        return logs_records

    def __del__(self):
        self._records_file.close()

app_logger = get_app_logger()
