import yaml
import logging
from moar import moar


logging.basicConfig(
    format='[%(asctime)-15s] %(filename)s:%(module)s.%(funcName)s:%(lineno)s :: %(message)s',
    level=10)
HANDLE = open('config.yaml', 'r')
CONTENTS = HANDLE.read()
HANDLE.close()
CONFIG = yaml.load(CONTENTS)


def application(env, start_response):
    global CONFIG
    return moar(CONFIG, env, start_response)
