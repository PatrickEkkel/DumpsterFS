from interfaces import StorageMethod, CachingMethod
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


class LocalFileCache(CachingMethod):

    def write(self, data, bp, fh):
        filename = f'cachefile__{fh}__{bp}'
        self.data_reader_writer.write_file(filename,data)

    def read(self, bp, fh):
        filename = f'cachefile__{fh}__{bp}'
        return self.data_reader_writer.read_file(filename).encode()

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
                new_data_block = self.filesystem.create_data_block()
                new_data_block.blockpointer = bp
                new_data_block.state = DataBlock.PERSISTED_IN_CACHE
                backlog_file.data_blocks.append(new_data_block)
                backlog_file.fd = fd
                backlog_file.block_pointer = bp
                result[fd] = backlog_file
            else:
                if backlog_file.block_pointer < bp:
                    backlog_file.block_pointer = bp

        return result

    def __init__(self,filesystem):
        CachingMethod.__init__(self)
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

    def get_file_handle(self, fd):
        return self.open_file_handles.get(fd)

    def __init__(self):
        super(StorageMethod).__init__()
        self.data_reader_writer = LocalDataReaderWriter()
        self.fd = 0
        self.open_file_handles = {}

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
