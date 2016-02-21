#! /usr/bin/env python2.7

import re

OSU_URL = re.compile("http[s]{0,1}://osu.ppy.sh/([sb])/(\d+)")
YOUTUBE_URL = re.compile("(?:youtube(?:-nocookie)?\.com\/(?:[^\/\n\s]+\/\S+\/|(?:v|e(?:mbed)?)\/|\S*?[?&]v=)|youtu\.be\/)([a-zA-Z0-9_-]{11})")
POLL_NAME = re.compile('"(.+)"')
POLL_OPTIONS = re.compile("\((.+?)\)")
