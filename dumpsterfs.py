from abc import abstractmethod
import base64
import json
import fuse_helpers
import os, binascii
import sys
import errno
import numpy as np
from utils import is_bytes
from datatypes import DataBlock, Index, DumpsterNode
from interfaces import StorageMethod, DataReaderWriter
from filesystems.lfs import LocalFileSystem
from caching.lfs_write_cache import LocalFileWriteCache
from caching.inmemory_read_cache import InMemoryReadCache
from stat import S_IFDIR, S_IFLNK, S_IFREG


class DumpsterFS:

    def __init__(self, file_system, local_file_cache):
        self.index = None
        self.filesystem = file_system
        self.read_cache = InMemoryReadCache()
        # default caching device is the local file cache
        if not local_file_cache:
            self.write_cache = LocalFileWriteCache(self.filesystem)
        else:
            self.write_cache = local_file_cache

    def open_file(self, path):
        index = self._get_index()
        result = index.find(path)
        if result == DataBlock.empty_block_pointer:
            # file is created but has no content, hence no blockpointer
            file_handle = self.filesystem.create_new_file_handle(path, fuse_helpers.S_IFREG)
            self.read_cache.write_file(bytearray(), file_handle.fd, 0, 0)
            self._add_fd_to_index(file_handle.dfs_filehandle)
            return file_handle.fd

        elif result != DataBlock.empty_block_pointer:
            file_handle = self._read_dfs_file(result, path)  #
            offset = 0
            length = len(file_handle.dfs_filehandle.get_base64())
            self.read_cache.write_file(file_handle.dfs_filehandle.get_base64(), file_handle.fd,
                                       offset, length)
            self._add_fd_to_index(file_handle.dfs_filehandle)


            return file_handle.fd

        else:
            file_handle = self.filesystem.create_new_file_handle(path, fuse_helpers.S_IFREG)

            return file_handle.fd

    def list_dir(self, path):
        result = []
        index = self._get_index()
        #file_info = self.get_file_info(path)

        for file in index.index['index_dict']:
            if file.startswith(path) and file != path and file != '/.dfs_index':
                # remove first slash
                # root is special case
                if path == '/':
                    dir_name = file.split('/')[1]

                else:
                    # truncate the part that is being requested, and get the right hand side
                    truncated_path = file.replace(path, '').split('/')[1]
                    dir_name = truncated_path
                if dir_name not in result:
                    result.append(dir_name)
        return result

    def create_dir(self, path, update_index=True):

        new_dir = DumpsterNode(self.filesystem, path, node_type=fuse_helpers.S_IFDIR)
        return self._add_filenode_to_index(new_dir)

    def create_new_file(self, path, update_index=True):
        # creates a filedescriptor and a path in the index
        # returns associated filedescriptor
        file_handle = self.filesystem.create_new_file_handle(path, fuse_helpers.S_IFREG)
        if update_index:
            self._add_fd_to_index(file_handle.dfs_filehandle)
            self._add_filenode_to_index(file_handle.dfs_filehandle)
        return file_handle.fd

    def read_file(self, fd, offset, length):
        return self.read_cache.read_file(fd, offset, length)

    def write_file(self, buf, fh, update_index=False):
        file_handle = self.filesystem.get_file_handle(fh)

        if file_handle is not None:
            dfs_handle = file_handle.dfs_filehandle
            block = dfs_handle.get_next_available_block(len(buf))
            block.write(buf)
            #dfs_handle.data_blocks.append(block)
            self._write_next_block(dfs_handle, fh)


    def flush(self):
        cached_files = self.write_cache.get_cache_backlog()
        for fd, dfs_handle in cached_files.items():
            index = self._get_index()
            dfs_handle.path = index.get_fd(fd)
            dfs_handle.block_start_location = self._write_dfs_file(dfs_handle, sort_blocks=True)
            file_stat = index.find(dfs_handle.path,search_in='lstat_dict')
            if file_stat:
                file_stat['st_size'] = dfs_handle.length
                index.add_info(dfs_handle.path,file_stat)
                #index.find(dfs_handle.path,search_in='lstat_dict')['st_size'] = dfs_handle.length

            self._add_filenode_to_index(dfs_handle)
            self.filesystem.release_file_handle(fd)
            # remove all cachefiles associated with the filedescriptor
            block_counter = dfs_handle.block_pointer
            while block_counter != -1:
                self.write_cache.delete(block_counter, dfs_handle.fd)
                block_counter -= 1

        # for now we decide to aggresively clear the inmemory read cache after
        # every flush, to ensure that the cache is always up to date
        self.read_cache.clear()

    def reset_index(self):
        # helper method to make testing with real filesystems easier
        self.filesystem.write_index_location('')

    def rename(self, old_path, new_path):
        index = self._get_index()
        index.replace(old_path, new_path)
        return self._update_index(index)

    def delete(self, path):
        index = self._get_index()
        index.remove(path)
        return self._update_index(index)

    def release(self,fd):
        self.filesystem.release_file_handle(fd)
        index = self._get_index()

        return self._update_index(index)

    def truncate(self,path, length):
        index = self._get_index()
        file_handle = self.filesystem.get_file_handle_by_path(path)
        file_handle.dfs_filehandle.data_blocks = []
        self.filesystem.update_filehandle(file_handle)
        index.find(path,search_in='lstat_dict')['st_size'] = length
        return self._update_index(index)

    def symlink(self, source, target):
        index = self._get_index()
        index.add(source, target)
        # just put slash in front of it, quick hack to get symlinks working
        target_size = index.find('/' + target,search_in='lstat_dict')['st_size']
        lstat = fuse_helpers.create_lstat(node_type=S_IFLNK,st_size=target_size)
        index.add_info(source, lstat)
        return self._update_index(index)

    def readlink(self, path):
        index = self._get_index()
        return index.find(path)

    def write_file_old(self, path, data, update_index=True):
        # need to get rid of this method, the index is still using it to write to the storage medium
        new_file = DumpsterNode(self.filesystem, path)
        # default to utf-8 for all strings
        if type(data) == str:
            bytes = bytearray(data, encoding='utf-8')
            new_file.write(bytes)
        elif is_bytes(data):
            new_file.write(data)

        new_file.block_start_location = self._write_dfs_file(new_file)
        if update_index:
            self._add_filenode_to_index(new_file)

        return new_file.block_start_location


    def _init_filesystem(self):
        # get the last known location for the index file
        index_location = self.filesystem.get_index_location()
        # no index present, this means this is a blank filesystem, we have to
        # create an indexfile and store the value in the bootstrap file
        if not index_location:
            # file system initialization, should move to seperate method
            index_path = '/.dfs_index'
            root = '/'
            index = self.filesystem.create_index()
            index.add(index_path, DataBlock.empty_block_pointer)
            index.add(root, DataBlock.empty_block_pointer)
            index.add_info('/', fuse_helpers.create_lstat(S_IFDIR, st_nlink=3))
            # don't update the index, because it would trigger an infinite loop
            index_location = self.write_file_old('/.dfs_index', index.to_json(), update_index=False)
            self.filesystem.write_index_location(index_location)
        return index_location

    def set_file_info(self, path, key, value):
        index = self._get_index()
        index.index['lstat_dict'][path][key] = value
        self._update_index(index)

    def get_file_info(self, path):
        index = self._get_index()
        return index.find(path, search_in='lstat_dict')

    def _get_index(self):
        # guarantees that the filesystem is ready for use
        index_location = self._init_filesystem()
        file_handle = self._read_dfs_file(index_location)
        index = self.filesystem.create_index()
        json_index = file_handle.dfs_filehandle.get_base64()
        index.index = Index.from_json(json_index)
        return index

    def _update_index(self, index):
        index_location = self.write_file_old('/.dfs_index', index.to_json(), update_index=False)
        self.filesystem.write_index_location(index_location)
        return index_location

    def _add_fd_to_index(self, file):
        index = self._get_index()
        index.add_fd(file.path, file.fd)
        return self._update_index(index)

    def _add_filenode_to_index(self, file):
        index = self._get_index()
        file.lstat['st_size'] = file.length
        if not file.block_start_location:
            index.add(file.path, DataBlock.empty_block_pointer)
        else:
            index.add(file.path, file.block_start_location)
        index.add_info(file.path, file.lstat)
        return self._update_index(index)

    def _read_dfs_file(self, location, path=None):
        file_handle = self.filesystem.create_new_file_handle(path, fuse_helpers.S_IFREG)
        # get the first datablock so we can start reconstructing the file
        first_block = self.filesystem.read(location)
        if first_block:
            first_block.update_block_info()
            file_handle.dfs_filehandle.data_blocks.append(first_block)

            current_block = first_block
            if current_block.next_block_location and current_block.next_block_location != DataBlock.empty_block_pointer:
                while True:
                    current_block = self.filesystem.read(current_block.next_block_location)
                    current_block.update_block_info()
                    file_handle.dfs_filehandle.data_blocks.append(current_block)

                    if not current_block.next_block_location or current_block.next_block_location == DataBlock.empty_block_pointer:
                        break
        return file_handle

    def _write_next_block(self, dfs_file, fh):
        block_pointer = dfs_file.block_pointer
        dfs_file.data_blocks[block_pointer].state = DataBlock.READY_NOT_COMMITTED
        # write the block to cache and clear the memory,
        self.write_cache.write(dfs_file.data_blocks[block_pointer].data, block_pointer, fh)
        dfs_file.data_blocks[block_pointer].state = DataBlock.NEW_IN_CACHE
        dfs_file.data_blocks[block_pointer].data = []
        dfs_file.block_pointer += 1

    def _read_next_block(self, fd, block):
        return self.write_cache.read(block.blockpointer, fd)

    def _write_dfs_file(self, dfs_file, sort_blocks=False):
        # write the chunks in reversed order, this is easy for later, because the
        # chunks are chained together like a linked list and we we want to read the file, from
        # first to last, every chunk contains a reference to the next_chunk, the
        # location is not in our control so we can't generate the references
        # beforehand

        # this is the result of using the old write method for the index, remove asap before
        # this legacy manifests itself.
        if sort_blocks:
            data_blocks = dfs_file.get_datablocks_in_writeorder()
        else:
            data_blocks = reversed(dfs_file.data_blocks)
        previous_block_location = None
        for block in data_blocks:
            block.next_block_location = previous_block_location
            # read the block from the cache before proceeding

            if block.state == DataBlock.PERSISTED_IN_CACHE:
                block.data = self._read_next_block(dfs_file.fd, block)
                block.length = len(block.data)
                block.state = DataBlock.READ_FROM_CACHE
            block.data = DataBlock.embed_block_location(block)
            previous_block_location = self.filesystem.write(block)
            block.state = DataBlock.PERSISTED_ON_STORAGE
            dfs_file.length += block.length
        # update size_struct

            # return the first block location
        return previous_block_location
