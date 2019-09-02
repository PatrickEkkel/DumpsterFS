import binascii, os
from interfaces import StorageMethod
from adapters.localfilesystem import LocalDataReaderWriter
from datatypes import FileHandle, DumpsterNode, DataBlock


class LocalFileSystem(StorageMethod):

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

    def write(self, data_block):
        filename = binascii.b2a_hex(os.urandom(15))
        return self.data_reader_writer.write_file(str(filename.decode()), data_block.data)

    def write_index_location(self, location):
        self.data_reader_writer.write_file('lfs_index', location)

    def get_index_location(self):
        index_file = self.data_reader_writer.read_file('lfs_index').decode()
        return index_file
