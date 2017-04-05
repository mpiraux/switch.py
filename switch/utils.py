import os

import yaml


def ensure_directory_exists(path):
    if not os.path.exists(path):
        os.mkdir(path)


def load_config_file(path):
    with open(path, 'r') as f:
        return yaml.load(f)
