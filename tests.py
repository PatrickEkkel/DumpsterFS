import json
import unittest
from dumpsterfs import DumpsterFS
from datatypes import DataBlock, DumpsterNode
from filesystems.lfs import LocalFileSystem
from caching.lfs_write_cache import LocalFileWriteCache
from caching.inmemory_read_cache import InMemoryReadCache
from stat import S_IFDIR, S_IFLNK, S_IFREG


class LocalFileSystemTests(unittest.TestCase):

    def reset_fs(self):
        self.dfs.reset_index()

    def setUp(self):

        self.lfs = LocalFileSystem()
        self.lfc = LocalFileWriteCache(self.lfs)
        self.lrc = InMemoryReadCache()
        self.dfs = DumpsterFS(self.lfs, self.lfc, self.lrc)
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

    def test_read_file_lots_of_blocks(self):
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

        fd = self.dfs.create_new_file('/multi_chunk_file')

        self.dfs.write_file(buf1, fd)
        self.dfs.write_file(buf2, fd)
        self.dfs.write_file(buf3, fd)
        self.dfs.write_file(buf4, fd)
        self.dfs.write_file(buf5, fd)
        expected_result = bytearray((buf1 + buf2 + buf3 + buf4 + buf5), encoding='utf-8')
        self.dfs.flush()
        read_fd = self.dfs.open_file('/multi_chunk_file')
        read_result = self.dfs.read_file(read_fd, 0, 21)
        assert read_result == expected_result

    def test_read_file_single_block(self):
        self.dfs.reset_index()
        DataBlock.block_size = 1000
        fd = self.dfs.create_new_file('/filetoopen')
        self.dfs.write_file(self.data_to_write, fd)
        self.dfs.flush()
        read_fd = self.dfs.open_file('/filetoopen')
        buf_len = len(self.data_to_write)

        read_result = self.dfs.read_file(read_fd, 0, buf_len)
        expected_result = bytearray(self.data_to_write, encoding='utf-8')
        assert expected_result == read_result

    def test_open_file(self):
        self.dfs.reset_index()
        DataBlock.block_size = 1000
        fd = self.dfs.create_new_file('/filetoopen')
        self.dfs.write_file(self.data_to_write, fd)
        self.dfs.flush()
        read_fd = self.dfs.open_file('/filetoopen')
        assert read_fd

    def test_index_with_file_descriptors(self):
        self.dfs.reset_index()
        DataBlock.block_size = 1000
        self.dfs.create_new_file('/test')
        self.dfs.flush()
        new_fd = self.dfs.open_file('/test')
        self.dfs.read_file(new_fd, 0, 4096)
        result = self.dfs._get_index().find('/test')
        # expect to find an empty file, because we have not written anything
        assert result == DataBlock.empty_block_pointer

    def test_write_small_file_one_pass(self):
        self.dfs.reset_index()
        DataBlock.block_size = 1000
        fd = self.dfs.create_new_file('/test')
        self.dfs.write_file(self.data_to_write, fd)
        self.dfs.flush()
        open_fd = self.dfs.open_file('/test')
        result = self.dfs.read_file(open_fd, 0, len(self.data_to_write))
        assert result == self.data_to_write.encode('utf-8')

    def test_binary_write_and_read_cycle(self):
        self.dfs.reset_index()
        DataBlock.block_size = 5
        binary_test_data = b'\xDE\xAD\xBE\xEF\xAD\xBE\xAD\xBE\xAD\xBE'
        fd = self.dfs.create_new_file('/binary')
        offset1 = 4
        offset2 = 8

        buf1 = binary_test_data[0:offset1]
        buf2 = binary_test_data[offset1:offset2]
        buf3 = binary_test_data[offset2:len(binary_test_data)]

        self.dfs.write_file(buf1, fd)
        self.dfs.write_file(buf2, fd)
        self.dfs.write_file(buf3, fd)
        self.dfs.flush()
        read_fd = self.dfs.open_file('/binary')
        read_result = self.dfs.read_file(read_fd, 0, 10)

        assert read_result == binary_test_data

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
        self.dfs._get_index().find('/fiveblocksonefile', search_in='lstat_dict')['st_size'] == 21

    def test_first_block_creation(self):
        file_handle = self.lfs.create_new_file_handle('/create_first_block_test', S_IFREG)
        buf1 = self.data_to_write[0:5]
        block = file_handle.dfs_filehandle.get_next_available_block(len(buf1))
        assert len(file_handle.dfs_filehandle.data_blocks) == 1
        assert block

    def test_create_filehandle(self):
        self.dfs.reset_index()
        file_handle = self.lfs.create_new_file_handle('/create_test_filehandle', S_IFREG)
        assert file_handle.fd == 1

    def test_file_read_from_writecache(self):
        # a fileread on a file that has not yet been flushed to the storage medium
        # should not be a problem
        self.dfs.reset_index()
        DataBlock.block_size = 5
        offset1 = 4
        offset2 = 8
        offset3 = 12
        buf1 = self.more_data_to_write[0:offset1]
        buf2 = self.more_data_to_write[offset1:offset2]
        buf3 = self.more_data_to_write[offset2:offset3]
        create_fd = self.dfs.create_new_file('/blockappending')
        self.dfs.write_file(buf1, create_fd)
        self.dfs.write_file(buf2, create_fd)
        self.dfs.write_file(buf3, create_fd)
        fd = self.dfs.open_file('/blockappending')
        read_result_1 = self.dfs.read_file(fd, 0, 12)
        assert read_result_1 == bytearray((buf1 + buf2 + buf3), encoding='utf-8')

    def test_file_appending_after_flush(self):
        # create a file, write a few blocks, do a flush to storage medium and than append data,
        # flushing in between writes should not be a problem
        self.dfs.reset_index()

        DataBlock.block_size = 5
        offset1 = 4
        offset2 = 8
        offset3 = 12
        offset4 = 15
        buf1 = self.more_data_to_write[0:offset1]
        buf2 = self.more_data_to_write[offset1:offset2]
        buf3 = self.more_data_to_write[offset2:offset3]
        buf4 = self.more_data_to_write[offset3:offset4]
        create_fd = self.dfs.create_new_file('/blockappending')

        self.dfs.write_file(buf1, create_fd)
        self.dfs.write_file(buf2, create_fd)
        # flush the filesystem to storage medium,
        self.dfs.flush()
        fd = self.dfs.open_file('/blockappending')
        # after flushing append buf3
        self.dfs.write_file(buf3, fd)
        #self.dfs.flush()
        read_result = self.dfs.read_file(fd, 0, 12)
        # file has been flushed partially, and now we read directly from cache
        assert read_result == bytearray((buf1 + buf2 + buf3), encoding='utf-8')
        # flush and release
        print('second flush')
        self.dfs.flush()
        #self.dfs.release(fd)
        fd = self.dfs.open_file('/blockappending')
        read_result = self.dfs.read_file(fd, 0, 12)
        print(bytearray((buf1 + buf2 + buf3), encoding='utf-8'))
        print(read_result)
        #assert read_result == bytearray((buf1 + buf2 + buf3), encoding='utf-8')
        fd = self.dfs.open_file('/blockappending')
        self.dfs.write_file(buf4, fd)
        read_result = self.dfs.read_file(fd, 0, (12 + len(buf4)))
        print(read_result)


    def test_open_same_file_twice(self):
        self.dfs.reset_index()
        self._write_multiblock_file('/open_twice_test.txt', self.more_data_to_write)
        result_fd_1 = self.dfs.open_file('/open_twice_test.txt')
        result_fd_2 = self.dfs.open_file('/open_twice_test.txt')
        read_result_1 = self.dfs.read_file(result_fd_1, 0, 4)
        read_result_2 = self.dfs.read_file(result_fd_2, 4, 8)

        assert result_fd_1 != result_fd_2
        assert len(read_result_2) == 4
        assert len(read_result_1) == 4

    def test_fd_index_update(self):
        file_handle = self.lfs.create_new_file_handle('/path/test123', S_IFREG)
        self.dfs._add_fd_to_index(file_handle.dfs_filehandle)

        path = self.dfs._get_index().get_fd(1)  # .get_fd(file_handle.fd))
        assert path == '/path/test123'

    def test_clear_index(self):
        self.dfs._init_filesystem()
        self.dfs.reset_index()
        assert self.lfs.get_index_location() == ''

    def _write_multiblock_file(self, path, data):
        offset1 = 4
        offset2 = 8
        offset3 = 12
        offset4 = 16
        offset5 = 21

        buf1 = data[0:offset1]
        buf2 = data[offset1:offset2]
        buf3 = data[offset2:offset3]
        buf4 = data[offset3:offset4]
        buf5 = data[offset4:offset5]

        fd = self.dfs.create_new_file(path)

        self.dfs.write_file(buf1, fd)
        self.dfs.write_file(buf2, fd)
        self.dfs.write_file(buf3, fd)
        self.dfs.write_file(buf4, fd)
        self.dfs.write_file(buf5, fd)
        self.dfs.flush()
        return fd
        # expected filesize


if __name__ == '__main__':
    unittest.main()
