from abc import abstractmethod


class DataReaderWriter:

    @abstractmethod
    def write_file(self, path, data):
        pass

    @abstractmethod
    def read_file(self, path):
        pass


class StorageMethod:

    def __init(self, data_reader_writer):
        self.data_reader_writer = None

    @abstractmethod
    def write(self, dfs_file):
        pass

    @abstractmethod
    def read(self, location):
        pass

    @abstractmethod
    def get_index_location(self):
        pass

    @abstractmethod
    def write_index_location(self, location):
        pass

    def create_index(self):
        from datatypes import Index
        return Index(self)

    def create_data_block(self):
        from datatypes import DataBlock
        return DataBlock(self)
