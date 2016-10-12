#!/usr/bin/env python


from tornado import ioloop
from tornado.options import define, options

from sfm.app import make_app

define(
    "server_address", default="127.0.0.1", help="bind given ip or hostname",
    type=str
)
define("server_port", default=8000, help="bind given port", type=int)


def main():
    options.parse_command_line()
    app = make_app()
    app.listen(options.server_port, address=options.server_address)
    ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    main()