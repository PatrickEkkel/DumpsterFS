import os, errno
from interfaces import DataReaderWriter


class LocalDataReaderWriter(DataReaderWriter):

    def file_exists(self, path):
        full_path = self.rootdirectory + path
        return os.path.isfile(full_path)

    def delete_file(self, filename):
        full_path = self.rootdirectory + filename
        os.remove(full_path)


    def __init__(self):
        self.rootdirectory = '/tmp/local_dfs/'

    def _create_dirs(self, path):
        if not os.path.exists(os.path.dirname(path)):
            try:
                os.makedirs(os.path.dirname(path))
            except OSError as exc:  # Guard against race condition
                if exc.errno != errno.EEXIST:
                    raise

    def write_file(self, path, data):
        full_path = self.rootdirectory + path
        self._create_dirs(full_path)
        # check if data is str or bytes and
        with open(full_path, "wb+") as f:
            if type(data) == str:
                f.write(data.encode('utf-8'))
            else:
                f.write(data)
        return path

    def list(self):
        return os.listdir(self.rootdirectory)

    def read_file(self, path):
        full_path = self.rootdirectory + path

        if os.path.exists(full_path):
            with open(full_path, "rb") as file:
                data = bytearray(file.read())
        else:
            self.write_file(path, '')
            data = self.read_file(path)
        return data
