from stat import S_IFDIR, S_IFLNK, S_IFREG
from abc import abstractmethod
from datatypes import FileHandle, DumpsterNode

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
    def read_file(self, fd, offset, length):
        pass

    @abstractmethod
    def write_file(self, data, fd, offset, length):
        pass

    @abstractmethod
    def append_file(self,data,fd, offset, length):
        pass

    @abstractmethod
    def exists(self, fd):
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

    def get_file_handle(self, fd):
        return self.open_file_handles.get(fd)

    def create_new_file_handle(self, path, file_type):
        self.fd += 1
        new_fh = FileHandle(self.fd, DumpsterNode(self, path, file_type , self.fd))
        self.open_file_handles[self.fd] = new_fh
        return new_fh

    def release_file_handle(self, fd):
        if self.open_file_handles.get(fd):
            del self.open_file_handles[fd]


    def get_file_handle_by_path(self, path):
        for key, value in self.open_file_handles.items():
            if value and value.dfs_filehandle.path == path:
                return value

    def update_filehandle(self, file_handle):
        self.open_file_handles[file_handle.fd] = file_handle


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
