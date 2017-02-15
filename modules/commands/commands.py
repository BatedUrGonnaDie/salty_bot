#! /usr/bin/env python2.7

HELP_TEXT = ["!commands", "Displays all active commands in the current channel."]

def call(salty_inst, c_msg, **kwargs):
    active_commands = dict(salty_inst.commands)
    if not salty_inst.is_live:
        if "!uptime" in active_commands:
            del active_commands["!uptime"]
        if "!highlight" in active_commands:
            del active_commands["!highlight"]
    reg_commands = []
    admin_commands = []
    for i in active_commands.iteritems():
        if i[1]["mod_req"]:
            admin_commands.append(i[0])
        else:
            reg_commands.append(i[0])

    command_string = ", ".join(sorted(reg_commands))
    if admin_commands:
        command_string += " | Mod Only Commands: {0}".format(", ".join(sorted(admin_commands)))
    return True, command_string
