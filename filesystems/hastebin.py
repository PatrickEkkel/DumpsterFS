from adapters.http import  HttpReaderWriter
from adapters.localfilesystem import LocalDataReaderWriter
from datatypes import DataBlock
from interfaces import StorageMethod

class HasteBinFileSystem(StorageMethod):


    def __init__(self):
        super(StorageMethod).__init__()
        # write all the data to hastebin via the HttpReaderWriter
        self.hastebin_url = 'http://localhost:7777/documents'
        self.http_data_reader_writer = HttpReaderWriter(self.hastebin_url)
        # still need the local file system for the index
        self.lfs_data_reader_writer = LocalDataReaderWriter()
        self.fd = 0
        self.open_file_handles = {}



    def read(self, location):
        data = self.http_data_reader_writer.read_file(location).json()['data']
        datablock = self.create_data_block()
        datablock.state = DataBlock.PERSISTED_ON_STORAGE
        # file is being read from the storage medium so it should have the status
        datablock.data = data
        return datablock


    def write(self, data_block):

        http_response = self.http_data_reader_writer.write_file(None,data_block.data)
        key = http_response.json()['key']
        return f'{self.hastebin_url}/{key}'


    def write_index_location(self, location):
        self.lfs_data_reader_writer.write_file('hastebin_index', location)

    def get_index_location(self):
        index_file = self.lfs_data_reader_writer.read_file('hastebin_index').decode()
        return index_file
