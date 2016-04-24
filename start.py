#! /usr/bin/env python2.7

import json
import logging
import os


from   modules import saltybot
from   modules import balancer
from   modules import configuration

from   modules.apis import *



























def twitch_update_thread():
    pass

def input_thread():
    pass

def listen_thread(config_obj, balancer_obj, server_type):
    if server_type == "json":
        e_params = {"filename" : os.environ["db_uri"]}
    else:
        e_params = {
            "web_ip" : os.environ["web_listen_ip"],
            "web_port" : os.environ["web_listen_port"],
            "web_secret" : os.environ["web_secret_key"]
        }
    server_obj = configuration.ConfigServer(server_type, **e_params)
    retrieve_value = server_obj.listen_for_updates()
    new_config = config_obj.fetch_one(retrieve_value)
    if retrieve_value:
        balancer_obj.update_bot(new_config)
    else:
        for i in new_config.values():
            balancer_obj.update_bot(i)



def main(**kwargs):
    logging.basicConfig(
        filename="debug.log",
        filemode="w",
        level=logging.DEBUG,
        format="[%(levelname)s %(asctime)s] %(message)s",
        datefmt="%m-%d %H:%M:%S"
    )
    logging.getLogger("requests").setLevel(logging.WARNING)
    with open("env_config.json", "r") as fin:
        envs = json.load(fin)
    salty_environment = kwargs["SALTY_ENV"] or os.environ.get("salty_environment", None) or "development"
    for k, v in envs[salty_environment].iteritems():
        os.environ[k] = v

    config_type = os.environ["db_type"]
    db_uri = os.environ["db_uri"]
    if config_type == "json":
        config_obj = configuration.JSONConfig(salty_environment, db_uri)
    else:
        config_obj = configuration.DBConfig(salty_environment, db_uri)

    initial_configs = config_obj.initial_retrieve()

if __name__ == "__main__":
    main()
