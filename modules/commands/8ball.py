#! /usr/bin/env python2.7

import random

HELP_TEXT = ["!8ball <question>", "Ask the 8ball and get a response."]

ANSWERS = [
    "It is certain",
    "It is decidedly so",
    "Without a doubt",
    "Yes definitely",
    "You may rely on it",
    "As I see it, yes",
    "Most likely",
    "Outlook good",
    "Yes",
    "Signs point to yes",
    "Reply hazy try again",
    "Ask again later",
    "Better not tell you now",
    "Cannot predict now",
    "Concentrate and ask again",
    "Don't count on it",
    "My reply is no",
    "My sources say no",
    "Outlook not so good",
    "Very doubtful"
]

def call(salty_inst, c_msg, **kwargs):
    question = c_msg["message"].split(' ')[1:]
    if not question:
        return False, "Magic 8ball says: Ask me a real question!"

    return True, "Magic 8ball says: {0}".format(random.choice(ANSWERS))

def test(salty_inst, c_msg, **kwargs):
    assert True
