from adapters.http import  HttpReaderWriter
from adapters.localfilesystem import LocalDataReaderWriter
from datatypes import DataBlock
from interfaces import StorageMethod

class HasteBinFileSystem(StorageMethod):


    def __init__(self):
        super(StorageMethod).__init__()
        # write all the data to hastebin via the HttpReaderWriter
        self.http_data_reader_writer = HttpReaderWriter()
        # still need the local file system for the index
        self.lfs_data_reader_writer = LocalDataReaderWriter()
        self.fd = 0
        self.open_file_handles = {}



    def read(self, location):
        file = self.http_data_reader_writer.read_file(location)
        datablock = self.create_data_block()
        datablock.state = DataBlock.PERSISTED_ON_STORAGE
        # file is being read from the storage medium so it should have the status
        datablock.data = file
        return datablock


    def write(self, data_block):

        location = self.http_data_reader_writer.write_file(None,data_block.data)
        return location

    def write_index_location(self, location):
        self.lfs_data_reader_writer.write_file('index', location)

    def get_index_location(self):
        index_file = self.lfs_data_reader_writer.read_file('index').decode()
        return index_file
