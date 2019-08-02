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
from filesystems import LocalFileSystem, LocalFileCache
from stat import S_IFDIR, S_IFLNK, S_IFREG

class DumpsterFS:

    def __init__(self, file_system):
        self.index = None
        self.filesystem = file_system
        self.cache = LocalFileCache(self.filesystem)

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
            index.add(index_path, 'None')
            index.add(root, 'None')
            index.add_info('/', fuse_helpers.create_lstat(S_IFDIR, st_nlink=3))
            # don't update the index, because it would trigger an infinite loop
            index_location = self.write_file_old('/.dfs_index', index.to_json(), update_index=False)
            self.filesystem.write_index_location(index_location)
        return index_location

    def set_file_info(self,path,key, value):
        index = self._get_index()
        index.index['lstat_dict'][path][key] = value
        self._update_index(index)

    def get_file_info(self, path):
        index = self._get_index()
        return index.find(path, search_in='lstat_dict')

    def _get_index(self):
        # guarantees that the filesystem is ready for use
        index_location = self._init_filesystem()
        dfs_handle = self._read_dfs_file(index_location)
        index = self.filesystem.create_index()
        json_index = base64.b64decode(dfs_handle.get_base64())
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
        index.add(file.path, file.block_start_location)
        index.add_info(file.path, file.lstat)
        return self._update_index(index)

    def _read_dfs_file(self, location):
        result = DumpsterNode(self.filesystem, None)
        # get the first datablock so we can start reconstructing the file
        first_block = self.filesystem.read(location)
        if first_block:
            first_block.update_block_info()
            result.data_blocks.append(first_block)

            current_block = first_block
            if current_block.next_block_location:
                while True:
                    current_block = self.filesystem.read(current_block.next_block_location)
                    current_block.update_block_info()
                    result.data_blocks.append(current_block)

                    if not current_block.next_block_location:
                        break
        return result

    def _write_next_block(self, dfs_file, fh):
        block_pointer = dfs_file.block_pointer
        dfs_file.data_blocks[block_pointer].state = DataBlock.READY_NOT_COMMITTED
        # write the block to cache and clear the memory,
        self.cache.write(dfs_file.data_blocks[block_pointer].data, block_pointer, fh)
        dfs_file.data_blocks[block_pointer].state = DataBlock.NEW_IN_CACHE
        dfs_file.data_blocks[block_pointer].data = []
        dfs_file.block_pointer += 1
    def _read_next_block(self,fd, block):
        return self.cache.read(block.blockpointer, fd)

    def _write_dfs_file(self, dfs_file):
        # write the chunks in reversed order, this is easy for later, because the
        # chunks are chained together like a linked list and we we want to read the file, from
        # first to last, every chunk contains a reference to the next_chunk, the
        # location is not in our control so we can't generate the references
        # beforehand
        data_blocks = reversed(dfs_file.data_blocks)
        previous_block_location = None
        for block in data_blocks:
            block.next_block_location = previous_block_location
            # read the block from the cache before proceeding
            if block.state == DataBlock.PERSISTED_IN_CACHE:
                block.data = self._read_next_block(dfs_file.fd,block)
                block.state = DataBlock.READ_FROM_CACHE
            block.data = DataBlock.embed_block_location(block)
            previous_block_location = self.filesystem.write(block)
            block.state = DataBlock.PERSISTED_ON_STORAGE

            # return the first block location
        return previous_block_location

    def get_attr(self, path):
        index = self._get_index()
        result = index.find(path)
        if result:
            pass

    def read_file(self, path):
        index = self._get_index()
        result = index.find(path)
        if result:
            file_data = self._read_dfs_file(result)
            return base64.b64decode(file_data.get_base64())
        else:
            return None

    def list_dir(self, path):
        result = []
        index = self._get_index()
        file_info = self.get_file_info(path)
        # if file_info and file_info['st_mode'] == fuse_helpers.S_IFDIR:
        for file in index.index['index_dict']:
            if file.startswith(path) and file != path and file != '/.dfs_index':
                # sanitized_filename = file.split(path)
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
        file_handle = self.filesystem.create_new_file_handle(path,fuse_helpers.S_IFREG)
        if update_index:
            self._add_fd_to_index(file_handle.dfs_filehandle)
        return file_handle.fd

    def write_file(self, buf, fh, update_index=False):
        file_handle = self.filesystem.get_file_handle(fh)
        if file_handle is not None:
            dfs_handle = file_handle.dfs_filehandle
            block = dfs_handle.get_next_available_block(len(buf))
            print('next available block')
            print(block.__dict__)
            block.write(buf)
            self._write_next_block(dfs_handle, fh)


    def flush(self):
        cached_files = self.cache.get_cache_backlog()

        for fd, dfs_handle in cached_files.items():
            index = self._get_index()
            dfs_handle.path = index.get_fd(fd)
            self._write_dfs_file(dfs_handle)


    def write_file_old(self, path, data, update_index=True):
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
