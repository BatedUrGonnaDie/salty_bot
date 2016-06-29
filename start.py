#! /usr/bin/env python2.7

from itertools import chain
import json
import logging
import os
import threading
import time

from   modules import saltybot
from   modules import balancer
from   modules import configuration
from   modules.module_errors import NewBotException
from   modules.apis import kraken
from   modules.apis import newbs
from   modules.apis import osu
from   modules.apis import splits_io
from   modules.apis import sr_com
from   modules.apis import srl
from   modules.apis import youtube

RUNNING = True
# All apis use the environment keys for the required access
GLOBAL_APIS = {}

def twitch_update_thread(balancer_obj):
    while RUNNING:
        with balancer_obj.lock:
            channels = [x["bots"].keys() for x in balancer_obj.connections.values()]
        channels = list(chain.from_iterable(channels))

        success, response = GLOBAL_APIS["kraken"].get_streams(channels)
        if not success:
            time.sleep(10)
            continue
        new_info = {i : {"game" : "", "title" : "", "stream_start" : "", "is_live" : False} for i in channels}
        for i in response["streams"]:
            new_info[i["channel"]["name"]] = {
                "game" : i["channel"]["game"],
                "title" : i["channel"]["status"],
                "is_live" : True,
                "stream_start" : i["created_at"]
            }
        balancer_obj.update_twitch(new_info)
        time.sleep(60)
    return

def listen_thread(config_obj, balancer_obj, server_obj):
    while RUNNING:
        retrieve_value = server_obj.listen_for_updates()
        new_config = config_obj.fetch_one(retrieve_value)
        if retrieve_value:
            new_config = {"" : new_config}
        for i in new_config.values():
            try:
                balancer_obj.update_bot(i)
            except NewBotException:
                balancer_obj.add_bot(saltybot.SaltyBot(i, GLOBAL_APIS))
    return

def main():
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
    salty_environment = os.environ.get("salty_environment", None) or "development"
    for k, v in envs[salty_environment].iteritems():
        os.environ[k] = str(v)

    GLOBAL_APIS["kraken"] = kraken.Kraken()
    GLOBAL_APIS["newbs"] = newbs.NewbsAPI()
    GLOBAL_APIS["osu"] = osu.OsuAPI()
    GLOBAL_APIS["splits_io"] = splits_io.SplitsIOAPI()
    GLOBAL_APIS["sr_com"] = sr_com.SRcomAPI()
    GLOBAL_APIS["srl"] = srl.SRLAPI()
    GLOBAL_APIS["youtube"] = youtube.YoutubeAPI()

    config_type = os.environ["db_type"]
    db_url = os.environ["db_url"]
    if config_type == "json":
        config_obj = configuration.JSONConfig(salty_environment, db_url)
        server_obj = configuration.ConfigServer("JSON", **{"filename" : os.environ["db_url"]})
    else:
        config_obj = configuration.DBConfig(salty_environment, db_url)
        server_obj = configuration.ConfigServer("db", **{
            "web_ip" : os.environ["web_listen_ip"],
            "web_port" : os.environ["web_listen_port"],
            "web_secret" : os.environ["web_secret_key"]
        })

    balancer_obj = balancer.Balancer()
    initial_configs = config_obj.initial_retrieve()
    for k, v in initial_configs.iteritems():
        bot_inst = saltybot.SaltyBot(v, dict(GLOBAL_APIS))
        balancer_obj.add_bot(bot_inst)

    tu_thread = threading.Thread(name="update-thread", target=twitch_update_thread, args=(balancer_obj,))
    tu_thread.daemon = True
    tu_thread.start()

    l_thread = threading.Thread(name="listen-thread", target=listen_thread, args=(config_obj, balancer_obj, server_obj))
    l_thread.daemon = True
    l_thread.start()

    try:
        while RUNNING:
            input("> ")
    except KeyboardInterrupt:
        print "Time to shut down!"


if __name__ == "__main__":
    main()
