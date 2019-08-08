from interfaces import StorageMethod, WriteCachingMethod, ReadCachingMethod
from services import LocalDataReaderWriter
from datatypes import FileHandle, DumpsterNode, DataBlock
from stat import S_IFDIR, S_IFLNK, S_IFREG
import os
import binascii


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

class InMemoryReadCache(ReadCachingMethod):
    # quick little in memory cache to serve as a buffer for the fuse interface
    def read_file(self,fd, offset, length):
        if length > len(self.filecache_dict[fd]):
            return self.filecache_dict[fd][offset:length]#.decode('utf-8')
        return self.filecache_dict[fd][offset:length]

    def write_file(self,data, fd,offset,length):
        self.filecache_dict[fd] = data[offset:length]

    def exists(self, fd):
        result = self.filecache_dict.get([fd])
        return result

    def clear(self):
        self.filecache_dict = {}

    def __init__(self):
        ReadCachingMethod.__init__(self)
        self.filecache_dict = {}



class LocalFileWriteCache(WriteCachingMethod):
    # write cache, that writes blocks of file to disk, makes write operations
    # go smoother, and allows for delayed write tactics
    def exists(self, bp, fh):
        filename = f'cachefile__{fh}__{bp}'
        return self.data_reader_writer.file_exists(filename)

    def delete(self, bp, fh):
        filename = f'cachefile__{fh}__{bp}'

        self.data_reader_writer.delete_file(filename)

    def write(self, data, bp, fh):
        filename = f'cachefile__{fh}__{bp}'
        self.data_reader_writer.write_file(filename,data)

    def read(self, bp, fh):
        filename = f'cachefile__{fh}__{bp}'
        return self.data_reader_writer.read_file(filename)

    def get_cache_backlog(self):
        listing = self.data_reader_writer.list()
        result = {}
        for list in listing:
            # get information like filedescriptors and such out of the cachefile
            cachefile_info = list.split('__')
            fd = int(cachefile_info[1])
            bp = int(cachefile_info[2])
            dfs_handle = result.get(fd)

            if dfs_handle is None:
                backlog_file = DumpsterNode(self.filesystem,None,S_IFREG)
                backlog_file.fd = fd
                backlog_file.block_pointer = bp
                result[fd] = backlog_file
            else:
                if backlog_file.block_pointer < bp:
                    backlog_file.block_pointer = bp

            new_data_block = self.filesystem.create_data_block()
            new_data_block.blockpointer = bp
            new_data_block.state = DataBlock.PERSISTED_IN_CACHE
            result[fd].data_blocks.append(new_data_block)

        return result

    def __init__(self,filesystem):
        WriteCachingMethod.__init__(self)
        self.data_reader_writer = LocalDataReaderWriter()
        self.data_reader_writer.rootdirectory = '/tmp/local_dfs/cache/'
        self.data_reader_writer._create_dirs('/tmp/local_dfs/cache/')
        self.filesystem  = filesystem


class LocalFileSystem(StorageMethod):

    def create_new_file_handle(self, path, type):
        self.fd += 1
        new_fh = FileHandle(self.fd, DumpsterNode(self, path, type,self.fd))
        self.open_file_handles[self.fd] = new_fh
        return new_fh

    def release_file_handle(self,fd):
        if self.open_file_handles.get(fd):
            del self.open_file_handles[fd]

    def get_file_handle(self, fd):
        return self.open_file_handles.get(fd)

    def get_file_handle_by_path(self, path):

        for key, value in self.open_file_handles.items():
            if value and value.dfs_filehandle.path == path:
                return value
    def update_filehandle(self,file_handle):
        self.open_file_handles[file_handle.fd] = file_handle

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

    def write_index_location(self, location):
        self.data_reader_writer.write_file('index', location)

    def get_index_location(self):
        index_file = self.data_reader_writer.read_file('index').decode()
        return index_file

    def write(self, data_block):
        filename = binascii.b2a_hex(os.urandom(15))
        return self.data_reader_writer.write_file(str(filename.decode()), data_block.data)
