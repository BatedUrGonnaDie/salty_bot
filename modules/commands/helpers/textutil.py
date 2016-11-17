#! /usr/bin/env python2.7

def add(salty_inst, c_msg, text_type, **kwargs):
    try:
        text = c_msg["message"].split(" ", 1)[1].strip()
    except IndexError:
        return False, "Please do not leave the quote blank."

    data = {
        "reviewed" : 1 if c_msg["sender"] == salty_inst.channel else 0,
        "text" : text,
        "user_id" : salty_inst.user_id
    }
    cookies = {"session" : salty_inst.config.session}
    success, response = salty_inst.newbs_api.add_textutil(salty_inst.channel, text_type, data, cookies, **kwargs)
    if not success:
        return False, "Error adding {0} to database ({1})".format(text_type, response.status_code)
    return True, "{0} successfully added to the database.".format(text_type.capitalize())

def get(salty_inst, c_msg, text_type, **kwargs):
    success, response = salty_inst.newbs_api.get_textutil(salty_inst.channel, text_type, **kwargs)
    if not success:
        return False, \
            "Error retrieving {0} from the database ({1})".format(text_type, response.status_code)
    return True, response["{0}s".format(text_type)][0]["text"]
