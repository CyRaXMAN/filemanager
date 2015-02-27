#!/usr/bin/env python

import os.path

from tornado import web, ioloop
from tornado.options import define, options

from sfm.Handlers import FileListHandler, UploadHandler, MainWsHandler, AuthHandler, DownloadHandler, ExitHandler

define("server_address", default="127.0.0.1", help="bind given ip or hostname", type=str)
define("server_port", default=8000, help="bind given port", type=int)


class Application(web.Application):
    def __init__(self):
        handlers = [
            (r"/", FileListHandler),
            (r"/upload", UploadHandler),
            (r"/ws", MainWsHandler),
            (r"/auth", AuthHandler),
            (r"/exit", ExitHandler),
            (r"/download/(.*)", DownloadHandler),
            (r"/static/(.*)", web.StaticFileHandler, {"path": "static"}),
        ]
        settings = dict(
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            debug=True,
            autoescape='xhtml_escape',
            xsrf_cookies=False,
            cookie_secret="1234567890qwerty",
            admin_login='admin',
            admin_passwd='admin',
            login_url="/auth",
        )
        web.Application.__init__(self, handlers, **settings)


def main():
    options.parse_command_line()
    app = Application()
    app.listen(options.server_port, address=options.server_address)
    ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    main()