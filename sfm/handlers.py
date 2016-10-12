
import os

import magic
import tornado.web
import tornado.websocket
import tornado.escape
from tornado.log import gen_log

from .models import BatchActions, DirectoryModel, FileModel


ACTIONS = ['chdir', 'list_dir', 'create_dir', 'create_file', 'update_perms',
           'update_buffer', 'paste_files', 'remove_files']

HOME_DIR = os.path.expanduser('~')


class Buffer(object):
    """Storing some useful data"""

    current_dir = HOME_DIR
    file_buffer = {'action': '', 'files': []}


class HandleAction(object):
    """
    Handling action.
    Attributes:
        data: some data for action.
    """

    def __init__(self, data):
        self.data = data

    def run(self):
        """
        Run action. Calls internal methods (started with underscore) to get
        result
        :return:
        """
        action = getattr(HandleAction(self.data), '_' + self.data['do'])
        result = {'action': self.data['do']}
        response = action()
        if 'exception' in response:
            result['exception'] = response['exception']
        else:
            result['response'] = response['response']
        return result

    def _chdir(self):
        """
        Change current directory
        :return:
        """
        if not all([item in self.data for item in ['path', 'name']]):
            return {'exception': 'Not enough data'}
        if self.data['path'] == '':
            self.data['path'] = Buffer.current_dir
        path = os.path.normpath(
            os.path.join(self.data['path'], self.data['name'])
        )
        Buffer.current_dir = path
        return {'response': {'result': path}}

    def _list_dir(self):
        """
        Show directory contents.
        :return:
        """
        path = os.path.normpath(Buffer.current_dir)
        Buffer.current_dir = path
        dir_model = DirectoryModel(path)
        try:
            files = dir_model.list_files()
        except (OSError, PermissionError) as e:
            return {'response': {'error': e.strerror, 'dir': path}}
        return {'response': {'files': files, 'dir': path}}

    def _create_file(self):
        """
        Create new file
        :return:
        """
        if 'name' not in self.data:
            return {'exception': 'Not enough data'}
        file_model = FileModel(Buffer.current_dir)
        try:
            result = file_model.create(os.path.basename(self.data['name']))
        except IOError as e:
            error = e.strerror or str(e)
            return {'response': {'error': error}}
        return {'response': {'result': result}}

    def _create_dir(self):
        """
        Create new directory
        :return:
        """
        if 'name' not in self.data:
            return {'exception': 'Not enough data'}
        dir_model = DirectoryModel(Buffer.current_dir)
        try:
            result = dir_model.create(os.path.basename(self.data['name']))
        except IOError as e:
            error = e.strerror or str(e)
            return {'response': {'error': error}}
        return {'response': {'result': result}}

    def _update_buffer(self):
        """
        Update buffer (cut, copy, remove)
        :return:
        """
        if not all([item in self.data for item in ['files', 'action']]):
            return {'exception': 'Not enough data'}
        Buffer.file_buffer['files'] = [
            os.path.join(
                Buffer.current_dir, str(f)
            ) for f in self.data['files']
        ]
        Buffer.file_buffer['action'] = self.data['action']
        return {
            'response': {
                'result': len(Buffer.file_buffer['files']),
                'action': self.data['action']
            }
        }

    def _paste_files(self):
        """
        Paste files
        :return:
        """
        action = Buffer.file_buffer['action']
        files = Buffer.file_buffer['files']
        destination = Buffer.current_dir
        if action == 'cut':
            result = BatchActions.move(files, destination)
            Buffer.file_buffer = {'action': '', 'files': []}
        elif action == 'copy':
            result = BatchActions.copy(files, destination)
        else:
            return {'response': {'error': 'Cut and copy only'}}
        return {'response': {'result': result, 'action': action}}

    def _remove_files(self):
        """
        Remove files
        :return:
        """
        action = Buffer.file_buffer['action']
        files = Buffer.file_buffer['files']
        if action != 'remove':
            return {'response': {'error': 'Wrong action'}}
        result = BatchActions.remove(files)
        Buffer.file_buffer = {'action': '', 'files': []}
        return {'response': {'result': result}}

    def _update_perms(self):
        """
        Update file permissions (chmod)
        :return:
        """
        result = BatchActions.chmod(
            self.data['files'], self.data['mode'], self.data['recursive']
        )
        return {'response': {'result': result}}

    def _pwd(self):
        """
        Returns current directory
        :return:
        """
        result = Buffer.current_dir
        return {'response': {'result': result}}


class BaseHandler(tornado.web.RequestHandler):

    def get_current_user(self):
        user = self.get_secure_cookie("current_user")
        if not user:
            return None
        return user

    def get_host_data(self):
        """
        Get host (ip or domain)
        :return:
        """
        host_data = {
            'host': '127.0.0.1',
            'port': '80'
        }
        host_tuple = self.request.host.split(':')
        host_data['host'] = host_tuple[0]
        if len(host_data) > 1:
            host_data['port'] = host_tuple[1]
        return host_data


class FileListHandler(BaseHandler):
    """File list."""

    @tornado.web.authenticated
    def get(self):
        self.render('file_list.html')


class UploadHandler(BaseHandler):
    """Upload file. Big files may eat much memory."""

    @tornado.web.authenticated
    def get(self):
        self.render('upload.html')

    @tornado.web.authenticated
    def post(self):
        try:
            new_file = self.request.files['uploadFile'][0]
            file_name = os.path.join(Buffer.current_dir, os.path.basename(new_file['filename']))
            with open(file_name, 'wb') as f:
                f.write(new_file['body'])
            response = 'File uploaded successfully'
        except KeyError:
            response = 'No file selected'
        except IOError as e:
            response = e.strerror
        self.render('upload.html', response=response)


class AuthHandler(BaseHandler):
    """
    Authentication. You can set login and password in app settings.
    """

    def get(self):
        if self.current_user:
            self.redirect('/')
            return
        self.render('auth.html')

    def post(self):
        login = self.get_argument('login', None)
        password = self.get_argument('passwd', None)
        if (self.application.settings['admin_login'] == login
            and self.application.settings['admin_passwd'] == password):
            self.set_secure_cookie(
                'current_user', self.application.settings['admin_login'],
                domain=self.get_host_data()['host']
            )
            self.redirect('/')
            return
        else:
            self.render('auth.html', response='Wrong login or password')


class DownloadHandler(BaseHandler):
    """
    Download file. Can send big files without memory leak. By default, buffer
    size equals 1Mb
    """

    @tornado.web.authenticated
    @tornado.web.asynchronous
    def get(self, path):
        self.buffer_size = 1048576
        path = '/' + path
        if os.path.exists(path) and os.path.isfile(path):
            try:
                mime = magic.from_file(path)
            except magic.MagicException:
                mime = 'application/octet-stream'
            self.set_header("Content-Type", mime)
            self.set_header(
                "Content-Disposition", "attachment; filename={}".format(
                    os.path.basename(path)
                )
            )
            self.set_header("Content-Length", os.path.getsize(path))
            self.file = open(path, 'rb')
            self.send_file()
        else:
            self.send_error(404)

    def send_file(self):
        data = self.file.read(self.buffer_size)
        if not data:
            self.finish()
            self.file.close()
            return
        self.write(data)
        self.flush(callback=self.send_file)


class ExitHandler(BaseHandler):
    """
    User exit. Just remove current_user cookie
    """

    def get(self):
        self.clear_cookie('current_user')
        self.redirect('/auth')


class BaseWsHandler(tornado.websocket.WebSocketHandler):
    """
    Base websocket handler
    """

    def open(self):
        gen_log.info(self.request.remote_ip + ' Connection established')

    def on_close(self):
        gen_log.info(self.request.remote_ip + ' Connection closed')


class MainWsHandler(BaseWsHandler, BaseHandler):
    """
    Websocket handler. Receives and checks action
    """

    def open(self):
        if not self.current_user:
            self.write_message({'response': {'error': 'Please log in first'}})
            self.close()
        super().open()

    def on_message(self, message):
        try:
            data = tornado.escape.json_decode(message)
        except ValueError:
            self.write_message(tornado.escape.json_encode(
                {'exception': "Invalid JSON data"})
            )
            return
        if 'do' not in data:
            self.write_message(tornado.escape.json_encode(
                {'exception': "No action"})
            )
            return
        if data['do'] not in ACTIONS:
            self.write_message(tornado.escape.json_encode(
                {'exception': "Unknown action"})
            )
            return
        action = HandleAction(data)
        result = action.run()
        self.write_message(tornado.escape.json_encode(result))


