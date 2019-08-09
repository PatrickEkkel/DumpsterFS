import binascii, os
from interfaces import StorageMethod
from adapters.localfilesystem import LocalDataReaderWriter
from datatypes import FileHandle, DumpsterNode, DataBlock

class LocalFileSystem(StorageMethod):

    def create_new_file_handle(self, path, type):
        self.fd += 1
        new_fh = FileHandle(self.fd, DumpsterNode(self, path, type, self.fd))
        self.open_file_handles[self.fd] = new_fh
        return new_fh

    def release_file_handle(self, fd):
        if self.open_file_handles.get(fd):
            del self.open_file_handles[fd]

    def get_file_handle(self, fd):
        return self.open_file_handles.get(fd)

    def get_file_handle_by_path(self, path):

        for key, value in self.open_file_handles.items():
            if value and value.dfs_filehandle.path == path:
                return value

    def update_filehandle(self, file_handle):
        self.open_file_handles[file_handle.fd] = file_handle

    def __init__(self):
        super(StorageMethod).__init__()
        self.data_reader_writer = LocalDataReaderWriter()
        self.fd = 0
        self.open_file_handles = {}

    def read(self, location):
        file = self.data_reader_writer.read_file(location)
        datablock = self.create_data_block()
        datablock.state = DataBlock.PERSISTED_ON_STORAGE
        # file is being read from the storage medium so it should have the status
        datablock.data = file
        return datablock

    def write_index_location(self, location):
        self.data_reader_writer.write_file('index', location)

    def get_index_location(self):
        index_file = self.data_reader_writer.read_file('index').decode()
        return index_file

    def write(self, data_block):
        filename = binascii.b2a_hex(os.urandom(15))
        return self.data_reader_writer.write_file(str(filename.decode()), data_block.data)
