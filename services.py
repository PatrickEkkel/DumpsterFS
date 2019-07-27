import os, errno
from interfaces import DataReaderWriter
class LocalDataReaderWriter(DataReaderWriter):

    def __init__(self):
        self.rootdirectory = '/tmp/local_dfs/'

    def _create_dirs(self, path):
        if not os.path.exists(os.path.dirname(path)):
            try:
                os.makedirs(os.path.dirname(path))
            except OSError as exc: # Guard against race condition
                if exc.errno != errno.EEXIST:
                    raise

    def write_file(self, path, data):
        path = self.rootdirectory + path
        self._create_dirs(path)
        with open(path, "w+") as f:
            f.write(str(data))

        return path

    def read_file(self,path, data):
        pass
