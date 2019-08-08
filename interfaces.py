from abc import abstractmethod


class DataReaderWriter:

    def __init__(self):
        pass

    @abstractmethod
    def file_exists(self, path):
        pass

    @abstractmethod
    def write_file(self, path, data):
        pass

    @abstractmethod
    def read_file(self, path):
        pass

    @abstractmethod
    def delete_file(self, filename):
        pass

class ReadCachingMethod:

    def __init__(self):
        pass

    @abstractmethod
    def read_file(self,fd, offset, length):

        pass

    @abstractmethod
    def write_file(self,data, fd,offset,length):

        pass

    @abstractmethod
    def exists(self,fd):
        pass

    @abstractmethod
    def clear(self):
        pass

class WriteCachingMethod:

    def __init__(self):
        pass

    @abstractmethod
    def get_cache_backlog(self):
        pass

    @abstractmethod
    def write(self, data, bp, fh):
        pass

    @abstractmethod
    def delete(self, bp, fh):
        pass

    @abstractmethod
    def exists(self, bp, fh):
        pass

    @abstractmethod
    def read(self, bp, fh):
        pass

    @abstractmethod
    def read(self, data, bp, fh):
        pass


class StorageMethod:

    def __init(self):
        self.data_reader_writer = None

    @abstractmethod
    def get_file_handle(self, fd):
        pass

    @abstractmethod
    def create_new_file_handle(self, path, file_type):
        pass

    @abstractmethod
    def write(self, dfs_file):
        pass

    @abstractmethod
    def release_file_handle(self,fd):
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
