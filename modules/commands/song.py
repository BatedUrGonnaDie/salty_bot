#! /usr/bin/env python2.7

def call(c_msg, **kwargs):
    success, response = kwargs["newbs_api"].get_song(c_msg["channel"][1:])
    if not success:
        return False, \
            "Error retrieving data from LoN ({}).".format(response.status_code)
    return True, response["song"]
