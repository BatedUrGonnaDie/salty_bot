#! /usr/bin/env python2.7

def suffix(number):
    if number in (11, 12, 13):
        return "th"
    else:
        return {1: "st", 2: "nd", 3: "rd"}.get(number % 10, "th")
