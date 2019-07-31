from interfaces import StorageMethod
from services import LocalDataReaderWriter

import os, binascii


class InMemoryFileSystem(StorageMethod):

    def __init__(self):
        super(StorageMethod).__init__()
        self.storage = {}
        self.index = ''

    def read(self, location):
        file = self.storage.get(location)
        datablock = self.create_data_block()
        datablock.data = file
        return datablock

    def write_index_location(self, location):
        self.index = location

    def get_index_location(self):
        return self.index

    def write(self, data_block):
        filename = binascii.b2a_hex(os.urandom(10))
        self.storage[filename.decode()] = data_block.data
        return filename.decode()

class LocalFileSystem(StorageMethod):

    def __init__(self):
        super(StorageMethod).__init__()
        self.data_reader_writer = LocalDataReaderWriter()

    def read(self, location):
        file = self.data_reader_writer.read_file(location)
        datablock = self.create_data_block()
        datablock.data = file
        return datablock

    def write_index_location(self, location):
        self.data_reader_writer.write_file('index', location)

    def get_index_location(self):
        index_file = self.data_reader_writer.read_file('index')
        return index_file

    def write(self, data_block):
        filename = binascii.b2a_hex(os.urandom(15))
        return self.data_reader_writer.write_file(str(filename.decode()), data_block.data)
