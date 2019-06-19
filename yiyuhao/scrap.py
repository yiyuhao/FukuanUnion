#
#      File: scrap.py
#   Project: payunion
#    Author: Yi Yuhao
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.

width_count = {}


def count(depth=300):
    def decorator(f):
        def wrapper(*args, **kwargs):
            width_count['url'] = width_count.get('url', 0) + 1
            if width_count['url'] > 300:
                pass

def parse_detail():
    return 2


def parse(detail):
    if not detail:
        yield 1
    else:
        yield parse_detail()


def run():
    detail = False
    while True:
        for result in parse(detail):
            detail = not detail

            print(result)


if __name__ == '__main__':
    run()
