import json
import unittest
from dumpsterfs import DumpsterFS
from datatypes import DataBlock, DumpsterNode
from filesystems import InMemoryFileSystem, LocalFileSystem, LocalFileCache
from stat import S_IFDIR, S_IFLNK, S_IFREG


class LocalFileSystemTests(unittest.TestCase):

    def setUp(self):

        self.lfs = LocalFileSystem()
        self.lfc = LocalFileCache(self.lfs)
        self.dfs = DumpsterFS(self.lfs, self.lfc)
        self.data_to_write = 'happy datastream readytowriteto_disk'

    def write_partial_stream_in_multiple_blocks(self):
        DataBlock.block_size = 5
        offset1 = 4
        offset2 = 7
        buf1 = self.data_to_write[0:offset1]
        buf2 = self.data_to_write[offset1:offset2]
        fd = self.dfs.create_new_file('/multiblock_file')
        self.dfs.write_file(buf1, fd)
        self.dfs.write_file(buf2, fd)
        self.dfs.flush()
        output = self.dfs.read_file('/multiblock_file')
        assert output
        assert output == (buf1 + buf2)

    def test_cache_write_block_status(self):
        DataBlock.block_size = 5
        offset1 = 4
        offset2 = 7

        buf1 = self.data_to_write[0:offset1]
        buf2 = self.data_to_write[offset1:offset2]
        fd = self.dfs.create_new_file('/multiblock_file')
        self.dfs.write_file(buf1, fd)
        self.dfs.write_file(buf2, fd)

        cached_file = self.lfc.get_cache_backlog()[fd]
        for block in cached_file.data_blocks:
            assert block.state == DataBlock.PERSISTED_IN_CACHE
        assert len(cached_file.data_blocks) == 2

    def test_write_small_file_one_pass(self):
        # TODO: not done yet
        fd = self.dfs.create_new_file('/test')
        self.dfs.write_file(self.data_to_write, fd)
        self.dfs.flush()

    def test_first_block_creation(self):
        file_handle = self.lfs.create_new_file_handle('/create_first_block_test', S_IFREG)
        buf1 = self.data_to_write[0:5]
        block = file_handle.dfs_filehandle.get_next_available_block(len(buf1))
        print(block)
        assert len(file_handle.dfs_filehandle.data_blocks) == 1
        assert block

    def test_create_filehandle(self):
        file_handle = self.lfs.create_new_file_handle('/create_test_filehandle', S_IFREG)
        assert file_handle.fd == 1

    def test_fd_index_update(self):
        file_handle = self.lfs.create_new_file_handle('/path/test123', S_IFREG)
        print(type(file_handle.fd))
        print(file_handle.__dict__)
        self.dfs._add_fd_to_index(file_handle.dfs_filehandle)

        path = self.dfs._get_index().get_fd(1) #.get_fd(file_handle.fd))
        assert path == '/path/test123'


class DumpsterFSTests(unittest.TestCase):
    def setUp(self):
        self.filesystem = InMemoryFileSystem()
        self.dumpster_fs = DumpsterFS(self.filesystem)

    def test_file_creation(self):
        #new_file = self.dumpster_fs.create_new_file('/multilayered/dir/')
        #print(new_file)
        new_file = self.dumpster_fs.write_file('/test/1/t', 'geert')
        self.dumpster_fs._get_index().find('/test/1/t')


if __name__ == '__main__':
    unittest.main()
