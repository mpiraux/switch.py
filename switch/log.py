from switch import join_root
import logging

logger = logging.getLogger('switch.py')
file_handler = logging.FileHandler(filename=join_root('app.log'))
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(module)s - [%(context)s] - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)
logger.setLevel(logging.DEBUG)
