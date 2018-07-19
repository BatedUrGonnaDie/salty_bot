#! /usr/bin/env python2.7

import json
import os


def set_environment_variables():
    try:
        with open("env_config.json", "r") as fin:
            envs = json.load(fin)
    except IOError, e:
        # If environment is set then continue, otherwise warn about lack of variables
        env = os.environ.get("SALTY_ENVIRONMENT", None)
        if env:
            return env
        else:
            raise e
    salty_environment = os.environ.get("SALTY_ENVIRONMENT", None) or envs.get("environment", None) or "development"
    for k, v in envs[salty_environment].iteritems():
        os.environ[k.upper()] = str(v)

    return salty_environment
