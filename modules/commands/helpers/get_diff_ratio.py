#! /usr/bin/env python3.7

import difflib


def diff_ratio(supplied, check_against):
    custom_lambda = lambda x: x == " " or x == "_" or x == ":"
    diff = difflib.SequenceMatcher(custom_lambda, supplied, check_against)
    return diff.ratio()
