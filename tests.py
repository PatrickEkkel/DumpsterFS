import json
import unittest
from dumpsterfs import DumpsterFS
from datatypes import DataBlock, DumpsterNode
from filesystems import InMemoryFileSystem, LocalFileSystem, LocalFileCache
from stat import S_IFDIR, S_IFLNK, S_IFREG


class LocalFileSystemTests(unittest.TestCase):

    def reset_fs(self):
        self.dfs.reset_index()

    def setUp(self):

        self.lfs = LocalFileSystem()
        self.lfc = LocalFileCache(self.lfs)
        self.dfs = DumpsterFS(self.lfs, self.lfc)
        self.data_to_write = 'happy datastream readytowriteto_disk'
        self.more_data_to_write = 'Sed ut perspiciatis unde omnis iste natus error sit voluptatem accusantium doloremque laudantium, totam rem aperiam, eaque ipsa quae ab illo inventore veritatis et quasi architecto beatae vitae dicta sunt explicabo. Nemo enim ipsam voluptatem quia voluptas sit aspernatur aut odit aut fugit, sed quia consequuntur magni dolores eos qui ratione voluptatem sequi nesciunt. Neque porro quisquam est, qui dolorem ipsum quia dolor sit amet, consectetur, adipisci velit, sed quia non numquam eius modi tempora incidunt ut labore et dolore magnam aliquam quaerat voluptatem. Ut enim ad minima veniam, quis nostrum exercitationem ullam corporis suscipit laboriosam, nisi ut aliquid ex ea commodi consequatur? Quis autem vel eum iure reprehenderit qui in ea voluptate velit esse quam nihil molestiae consequatur, vel illum qui dolorem eum fugiat quo voluptas nulla pariatur'

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
        self.dfs.reset_index()

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

    def test_flush_cache_clear(self):
        self.dfs.reset_index()
        DataBlock.block_size = 5
        fd = self.dfs.create_new_file('/filetoberemovedfromcache')
        offset1 = 4
        offset2 = 7

        buf1 = self.data_to_write[0:offset1]
        buf2 = self.data_to_write[offset1:offset2]

        self.dfs.write_file(buf1, fd)
        self.dfs.write_file(buf2, fd)

        file_handle = self.lfs.get_file_handle(fd)
        block_counter = file_handle.dfs_filehandle.block_pointer
        self.dfs.flush()
        while block_counter != -1:
            assert not self.lfc.exists(block_counter, fd)
            block_counter -= 1



    def test_write_small_file_one_pass(self):
        # TODO: not done yet
        self.dfs.reset_index()
        DataBlock.block_size = 1000
        fd = self.dfs.create_new_file('/test')
        self.dfs.write_file(self.data_to_write, fd)
        self.dfs.flush()

    def test_st_size_length(self):
        self.dfs.reset_index()
        DataBlock.block_size = 5
        offset1 = 4
        offset2 = 8
        offset3 = 12
        offset4 = 16
        offset5 = 21

        buf1 = self.more_data_to_write[0:offset1]
        buf2 = self.more_data_to_write[offset1:offset2]
        buf3 = self.more_data_to_write[offset2:offset3]
        buf4 = self.more_data_to_write[offset3:offset4]
        buf5 = self.more_data_to_write[offset4:offset5]

        fd = self.dfs.create_new_file('/fiveblocksonefile')

        self.dfs.write_file(buf1, fd)
        self.dfs.write_file(buf2, fd)
        self.dfs.write_file(buf3, fd)
        self.dfs.write_file(buf4, fd)
        self.dfs.write_file(buf5, fd)
        self.dfs.flush()
        # expected filesize is 21
        self.dfs._get_index().find('/fiveblocksonefile',search_in='lstat_dict')['st_size'] == 21

    def test_first_block_creation(self):
        file_handle = self.lfs.create_new_file_handle('/create_first_block_test', S_IFREG)
        buf1 = self.data_to_write[0:5]
        block = file_handle.dfs_filehandle.get_next_available_block(len(buf1))
        print(block)
        assert len(file_handle.dfs_filehandle.data_blocks) == 1
        assert block

    def test_create_filehandle(self):
        self.dfs.reset_index()
        file_handle = self.lfs.create_new_file_handle('/create_test_filehandle', S_IFREG)
        assert file_handle.fd == 1

    def test_fd_index_update(self):
        file_handle = self.lfs.create_new_file_handle('/path/test123', S_IFREG)
        print(type(file_handle.fd))
        print(file_handle.__dict__)
        self.dfs._add_fd_to_index(file_handle.dfs_filehandle)

        path = self.dfs._get_index().get_fd(1) #.get_fd(file_handle.fd))
        assert path == '/path/test123'

    def test_clear_index(self):
            #print(self.lfs.get_index_location())
            self.dfs._init_filesystem()
            self.dfs.reset_index()
            assert self.lfs.get_index_location() == ''

# TODO: in memory file cache for unit tests

#class DumpsterFSTests(unittest.TestCase):
#    def setUp(self):
#        self.filesystem = InMemoryFileSystem()
#        self.dumpster_fs = DumpsterFS(self.filesystem)
#
#    def test_file_creation(self):
#        #new_file = self.dumpster_fs.create_new_file('/multilayered/dir/')
#        #print(new_file)
#        new_file = self.dumpster_fs.write_file('/test/1/t', 'geert')
#        self.dumpster_fs._get_index().find('/test/1/t')


if __name__ == '__main__':
    unittest.main()
