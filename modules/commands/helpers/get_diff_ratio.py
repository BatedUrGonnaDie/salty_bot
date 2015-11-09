#! /usr/bin/env python2.7

import difflib

def diff_ratio(supplied, check_against):
    custom_lambda = lambda x: x == " " or x == "_"
    diff = difflib.SequenceMatcher(custom_lambda, supplied, check_against)
    return diff.ratio()
