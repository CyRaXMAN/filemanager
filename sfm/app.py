
import os
import sys
from tornado import web

from sfm.handlers import (
    FileListHandler, UploadHandler, MainWsHandler, AuthHandler,
    DownloadHandler, ExitHandler
)


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
            template_path=os.path.join(os.getcwd(), "templates"),
            debug=True,
            autoescape='xhtml_escape',
            xsrf_cookies=False,
            cookie_secret="1234567890qwerty",
            admin_login='admin',
            admin_passwd='admin',
            login_url="/auth",
        )
        web.Application.__init__(self, handlers, **settings)


def make_app():
    app = Application()
    return app