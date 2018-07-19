#! /usr/bin/env python3.7

ON_ACTION = "RECONNECT"


def call(salty_inst, c_msg, balancer, **kwargs):
    with balancer.lock:
        irc_obj = balancer.connections[c_msg["bot_name"]]["irc_obj"]
        old_host = irc_obj.host
        irc_obj.host = irc_obj.get_peer_ip()
        irc_obj.reconnect()
        irc_obj.host = old_host

    return True, ""
