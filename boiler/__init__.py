import os


def get_root_path():
    return os.path.abspath(os.path.dirname(__file__))


def join_root(path):
    return os.path.join(get_root_path(), path)
