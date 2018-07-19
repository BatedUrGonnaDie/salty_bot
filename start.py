#! /usr/bin/env python3.7

from itertools import chain
import logging
import os
import threading
import time

from modules import saltybot
from modules import balancer
from modules import configuration
from modules import setup_env
from modules.module_errors import NewBotException
from modules.apis import kraken
from modules.apis import newbs
from modules.apis import osu
from modules.apis import splits_io
from modules.apis import sr_com
from modules.apis import srl
from modules.apis import youtube

RUNNING = True
# All apis use the environment keys for the required access
GLOBAL_APIS = {}


def twitch_update_thread(balancer_obj):
    sleep_timer = 2
    while RUNNING:
        with balancer_obj.lock:
            channels = [list(x["bots"].keys()) for x in list(balancer_obj.connections.values())]
        channels = list(chain.from_iterable(channels))

        success, response = GLOBAL_APIS["kraken"].get_streams(channels)
        if not success:
            time.sleep(sleep_timer)
            sleep_timer = sleep_timer ** 2
            continue
        new_info = {x: {"game": "", "title": "", "stream_start": "", "is_live": False} for x in channels}
        try:
            for i in response["streams"]:
                new_info[i["channel"]["name"]] = {
                    "game": i["channel"]["game"],
                    "title": i["channel"]["status"],
                    "is_live": True,
                    "stream_start": i["created_at"]
                }
            balancer_obj.update_twitch(new_info)
        except TypeError:
            pass
        sleep_timer = 2
        time.sleep(60)
    return


def listen_thread(config_obj, balancer_obj, server_obj):
    while RUNNING:
        retrieve_value = server_obj.listen_for_updates()
        new_config = config_obj.fetch_one(retrieve_value)
        if retrieve_value:
            new_config = {"": new_config}
        for i in list(new_config.values()):
            try:
                balancer_obj.update_bot(i)
            except NewBotException:
                balancer_obj.add_bot(saltybot.SaltyBot(i))
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

    salty_environment = setup_env.set_environment_variables()

    GLOBAL_APIS["kraken"] = kraken.Kraken()
    GLOBAL_APIS["kraken"].headers["User-Agent"] = "SaltyBot"
    GLOBAL_APIS["newbs"] = newbs.NewbsAPI()
    GLOBAL_APIS["osu"] = osu.OsuAPI()
    GLOBAL_APIS["splits_io"] = splits_io.SplitsIOAPI()
    GLOBAL_APIS["sr_com"] = sr_com.SRcomAPI()
    GLOBAL_APIS["srl"] = srl.SRLAPI()
    GLOBAL_APIS["youtube"] = youtube.YoutubeAPI()

    config_type = os.environ["DB_TYPE"]
    db_url = os.environ["DB_URL"]
    if config_type == "json":
        config_obj = configuration.JSONConfig(salty_environment, db_url)
        server_obj = configuration.ConfigServer("JSON", **{"filename": os.environ["DB_URL"]})
    else:
        config_obj = configuration.DBConfig(salty_environment, db_url)
        server_obj = configuration.ConfigServer("db", **{
            "web_ip": os.environ["WEB_LISTEN_IP"],
            "web_port": os.environ["WEB_LISTEN_PORT"],
            "web_secret": os.environ["WEB_SECRET_KEY"]
        })

    balancer_obj = balancer.Balancer()
    initial_configs = config_obj.initial_retrieve()
    for k, v in initial_configs.items():
        bot_inst = saltybot.SaltyBot(v)
        balancer_obj.add_bot(bot_inst)

    tu_thread = threading.Thread(name="update-thread", target=twitch_update_thread, args=(balancer_obj,))
    tu_thread.daemon = True
    tu_thread.start()

    l_thread = threading.Thread(name="listen-thread", target=listen_thread, args=(config_obj, balancer_obj, server_obj))
    l_thread.daemon = True
    l_thread.start()

    try:
        global RUNNING
        while RUNNING:
            eval(input("> "))
    except KeyboardInterrupt:
        print("Time to shut down!")
        RUNNING = False


if __name__ == "__main__":
    main()
