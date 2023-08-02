#!/usr/bin/env python3


import sys
import os
import re
from framework import Framework


def get_log_strings(logs):
    # Find all flies that end in "log" and who's names are a mix of letters and numbers
    Files = [
        os.path.join(dp, f)
        for dp, dn, fn in os.walk(os.path.expanduser(logs))
        for f in fn
        if re.match(r"[\w\d]+\.log", f)
    ]
    logs = []
    for F in Files:
        fp = open(F)
        for l in fp:
            logs.append(l)

        fp.close()

    return logs


def get_matches(logs, framework):
    matches = []
    for msg in logs:
        ret = framework.parse_fragment(msg, "root:regex")
        if ret is not None:
            (PtnList, Token) = ret
            out = framework.generate_json_output(PtnList, Token)
            matches.append(out)
        else:
            matches.append('{"match":"none found"}')

    return matches


def build_output(matches):
    count = 0
    strings = []
    for r in matches:
        string = f'"result-{count}":' + r
        strings.append(string)
        count += 1

    res = "{"
    count = 0
    while count != len(strings):
        res += strings[count]
        count += 1
        if count < len(strings):
            res += ","

    res += "}"

    return res


def main(rules, logs):
    logs = get_log_strings(logs)
    f = Framework(rules)

    matches = get_matches(logs, f)

    res = build_output(matches)

    print(res)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("usage: ./framework.py <rule dir> <log dir>")
        print("rule dir: The root directory for rules files")
        print("log dir: The message to parse using the rules")
    else:
        main(sys.argv[1], sys.argv[2])
