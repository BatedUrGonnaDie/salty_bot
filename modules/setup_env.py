#! /usr/bin/env python2.7

import json
import os

def set_environment_variables():
    with open("env_config.json", "r") as fin:
        envs = json.load(fin)
    salty_environment = os.environ.get("salty_environment", None) or envs.get("environment", None) or "development"
    for k, v in envs[salty_environment].iteritems():
        os.environ[k] = str(v)

    return salty_environment
