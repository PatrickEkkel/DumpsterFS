from abc import abstractmethod


class DataReaderWriter:

    @abstractmethod
    def write_file(self, path, data):
        pass


    @abstractmethod
    def read_file(self, path):
        pass



class StorageMethod:

    def __init(self,data_reader_writer):
        self.data_reader_writer = None

    @abstractmethod
    def write(self, dfs_file):
        pass
    @abstractmethod
    def get_index(self):
        pass

    @abstractmethod
    def create_data_block():
        pass
