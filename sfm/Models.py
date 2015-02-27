
import os
import shutil
from pwd import getpwuid
from grp import getgrgid

import magic


class BatchActions(object):
    """Some batch operations."""

    @staticmethod
    def move(files, path):
        successfully_moved = 0
        for f in files:
            file_name = os.path.basename(f)
            try:
                shutil.move(f, os.path.join(path, file_name))
                successfully_moved += 1
            except OSError:
                continue

        return successfully_moved

    @staticmethod
    def copy(files, path):
        successfully_copied = 0
        for f in files:
            file_name = os.path.basename(f)
            try:
                shutil.copy(f, os.path.join(path, file_name))
                successfully_copied += 1
            except OSError:
                continue

        return successfully_copied

    @staticmethod
    def remove(files):
        successfully_removed = 0
        for f in files:
            try:
                if os.path.isdir(f):
                    shutil.rmtree(f)
                else:
                    os.remove(f)
                successfully_removed += 1
            except OSError:
                continue
        return successfully_removed

    @staticmethod
    def chmod(files, mode, recursive=False):
        successful_chmod = 0
        for f in files:
            if os.path.isdir(f):
                if recursive:
                    for path, dirs, _files in os.walk(f):
                        for _dir in dirs + _files:
                            try:
                                os.chmod(os.path.join(path, _dir), mode)
                                successful_chmod += 1
                            except OSError:
                                continue
                else:
                    try:
                        os.chmod(f)
                        successful_chmod += 1
                    except OSError:
                        pass
            else:
                try:
                    os.chmod(f)
                    successful_chmod += 1
                except OSError:
                    pass

        return successful_chmod


class DirectoryModel(object):
    """Directory model
    Attributes:
        current_dir: current working directory.
    """

    def __init__(self, current_dir):
        self.current_dir = current_dir

    def create(self, name):
        """Create new directory in current_dir"""
        path = os.path.join(self.current_dir, name)
        if os.path.exists(path):
            raise IOError('Directory already exists')

        os.mkdir(path)

        return True

    def remove(self, name):
        """Remove directory in current_dir"""
        os.rmdir(os.path.join(self.current_dir, name))

        return True

    def list_files(self):
        """Return list of files from current_dir"""
        files = os.listdir(self.current_dir)
        result = []
        if not files:
            return result

        file_model = FileModel(self.current_dir)
        for f in files:
            file_info = file_model.info(f)
            result.append(file_info)

        return result

    def get_size(self):
        """Get current_dir contents size."""
        dir_size = 0
        for path, dirs, files in os.walk(self.current_dir):
            for f in files:
                dir_size += os.path.getsize(os.path.join(path, f))

        return dir_size

    def chmod_dir(self, mode, recursive=False):
        """Change current_dir permissions. Can be recursive."""
        successful_chmod = 0
        if recursive:
            for path, dirs, files in os.walk(self.current_dir):
                for _dir in dirs:
                    os.chmod(os.path.join(path, _dir), mode)
                    successful_chmod += 1
                for f in files:
                    os.chmod(os.path.join(path, f), mode)
                    successful_chmod += 1
        else:
            os.chmod(self.current_dir)
            successful_chmod += 1

        return successful_chmod


class FileModel(object):
    """File model
    Attributes:
        current_dir: current working directory.
    """

    def __init__(self, current_dir):
        self.current_dir = current_dir

    def create(self, name):
        """Create new file in current_dir. May raise IOError if file exists"""
        file_path = os.path.join(self.current_dir, name)
        if os.path.exists(file_path):
            raise IOError('File already exists')
        open(file_path, 'a').close()

        return True

    def remove(self, name):
        """Remove file from current_dir"""
        os.remove(os.path.join(self.current_dir, name))

        return True

    def info(self, name):
        """Get file info from current_dir. Returns list."""
        stat_data = os.stat(os.path.join(self.current_dir, name))
        try:
            mime_type = magic.from_file(os.path.join(self.current_dir, name), mime=True).decode()
        except magic.MagicException:
            mime_type = 'application/octet-stream'
        file_info = {
            'name': name,
            'path': self.current_dir,
            'mime': mime_type,
            'type': mime_type.replace('/', '-'),
            'size': stat_data.st_size,
            'mode': format(stat_data.st_mode & 0o777, 'o'),
            'owner_id': stat_data.st_uid,
            'owner_name': getpwuid(stat_data.st_uid).pw_name,
            'group_id': stat_data.st_gid,
            'group_name': getgrgid(stat_data.st_gid).gr_name,
        }
        if mime_type == 'inode/symlink':
            file_info['real_path'] = os.path.realpath(os.path.join(self.current_dir, name))
            file_info['real_mime'] = magic.from_file(file_info['real_path'], mime=True).decode()
            file_info['real_type'] = file_info['real_mime'].replace('/', '-')

        return file_info

    def chmod_file(self, name, mode):
        """Change file permissions"""
        os.chmod(os.path.join(self.current_dir, name), mode)

        return True

