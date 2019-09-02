from interfaces import WriteCachingMethod
from adapters.localfilesystem import LocalDataReaderWriter
from datatypes import DumpsterNode, DataBlock
from stat import S_IFDIR, S_IFLNK, S_IFREG

class LocalFileWriteCache(WriteCachingMethod):
    # write cache, that writes blocks of file to disk, makes write operations
    # go smoother, and allows for delayed write tactics
    def exists(self, bp, fh):
        filename = f'cachefile__{fh}__{bp}'
        return self.data_reader_writer.file_exists(filename)

    def delete(self, bp, fh):
        filename = f'cachefile__{fh}__{bp}'
        if self.data_reader_writer.file_exists(filename):
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
