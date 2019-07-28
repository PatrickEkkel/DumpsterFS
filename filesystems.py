from interfaces import StorageMethod
from services import LocalDataReaderWriter

import os,binascii


class LocalFileSystem(StorageMethod):

    def __init__(self):
        super(StorageMethod).__init__()
        self.data_reader_writer = LocalDataReaderWriter()

    def create_data_block(self):
        from dumpsterfs import DataBlock
        return DataBlock(self)

    def get_index(self):
        index_file =  self.data_reader_writer.read_file('index')

        return index_file

    def write(self,data_block):
        filename = binascii.b2a_hex(os.urandom(8))
        return self.data_reader_writer.write_file(str(filename.decode()), data_block.data)
