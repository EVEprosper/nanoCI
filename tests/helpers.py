"""helpers.py: tests global scratch space"""
# TODO: move root/paths to pytest official global spaces
from os import path

import prosper.common.prosper_config as p_config

HERE = path.abspath(path.dirname(__file__))
ROOT = path.dirname(HERE)

APP_CONFIG = p_config.ProsperConfig(path.join(ROOT, 'testhelpers', 'app.cfg'))
