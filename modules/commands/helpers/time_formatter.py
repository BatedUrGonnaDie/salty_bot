#! /usr/bin/env python3.7


def format_time(time):
    m, s = divmod(float(time), 60)
    h, m = divmod(int(m), 60)
    s = round(s, 2)

    if s < 10:
        s = "0" + str(s)
    if m < 10:
        m = "0" + str(m)

    sr_time = "{0}:{1}:{2}".format(int(h), m, s)
    if sr_time.endswith(".0"):
        sr_time = sr_time[:-2]
    if sr_time.startswith("0:"):
        sr_time = sr_time[2:]
    if sr_time.startswith("0"):
        sr_time = sr_time[1:]
    return sr_time
