from abc import abstractmethod
import base64
import sys

class DataReaderWriter:

    @abstractmethod
    def write_file(self, path, data):
        pass

    @abstractmethod
    def read_file(self, path, data):
        pass



class StorageMethod:

    def __init(self,data_reader_writer):
        self.data_reader_writer = data_reader_writer

    @abstractmethod
    def create_data_block():
        pass

class LocalFileSystem(StorageMethod):

    def __init__(self):
        pass

    def create_data_block(self):
        return DataBlock(self)

class LocalDataReaderWriter(DataReaderWriter):

    def write_file(self, path, data):
        pass
    def read_file(self,path, data):
        pass


class Index:

    def __init__(self):
        self.index_location = None
        self.storage_method = None

    def find(self, filename):
        pass


class DumpsterFile:

    def __init__(self,file_system):
        self.data_blocks = []
        self.filesystem = file_system

    def write(self, bytes):
        bytes = base64.b64encode(bytes)
        file_length = len(bytes)
        block_size_counter = 0
        i = 0
        p = 0
        while file_length != 0:
            # causes typical off by one size difference, but we don't care (for now)
            if DataBlock.block_size == block_size_counter:
                block_size_counter = 0
                new_data_block = self.filesystem.create_data_block()
                new_data_block.set_data(bytes[p:i])
                print(bytes[p:i])
                p = i
            elif file_length < DataBlock.block_size:
                new_data_block = self.filesystem.create_data_block()
                print(bytes[i:len(bytes)])
                break;

            block_size_counter += 1
            file_length -= 1
            i += 1
    def deserialize():
        pass

    def serialize():
        pass

class DumpsterFS:

    def __init__(self, file_system):
        self.index = None
        self.file_system = file_system
    def connect(self):
        pass

    def create_file(self,path, data):
        new_file = DumpsterFile(self.file_system)
        # default to utf-8 for all strings
        if type(data) == str:
            bytes = bytearray(data,encoding='utf-8')
            new_file.write(bytes)

        pass

class DataBlock:

    block_size = 10

    NEW = 0
    IN_CACHE = 1
    PERSISTED = 2

    def __init__(self, storage_method):
        self.next_block_location = None
        self.storage_method = storage_method
        self.state = DataBlock.NEW

    def set_data(self,data):
        self.data = data



dumpster_fs = DumpsterFS(LocalFileSystem())

dumpster_fs.create_file('test','some random string to put in a file')
