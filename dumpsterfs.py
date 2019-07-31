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
from filesystems import LocalFileSystem
from stat import S_IFDIR, S_IFLNK, S_IFREG


class DumpsterFS:

    def __init__(self, file_system):
        self.index = None
        self.filesystem = file_system

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
            index_location = self.write_file('/.dfs_index', index.to_json(), update_index=False)
            self.filesystem.write_index_location(index_location)
        return index_location

    def set_file_info(self,path,key, value):

        index_location = self._init_filesystem()
        dfs_handle = self._read_dfs_file(index_location)
        json_index = base64.b64decode(dfs_handle.get_base64())
        index = self.filesystem.create_index()

        index.index = Index.from_json(json_index)
        index.index['lstat_dict'][path][key] = value

        index_location = self.write_file('/.dfs_index', index.to_json(), update_index=False)
        self.filesystem.write_index_location(index_location)

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

    def _update_index(self, file):
        # guarantees that the filesystem is ready for use

        index_location = self._init_filesystem()

        dfs_handle = self._read_dfs_file(index_location)
        json_index = base64.b64decode(dfs_handle.get_base64())
        index = self.filesystem.create_index()
        index.index = Index.from_json(json_index)
        file.lstat['st_size'] = file.length
        index.add(file.path, file.block_start_location)
        index.add_info(file.path, file.lstat)
        index_location = self.write_file('/.dfs_index', index.to_json(), update_index=False)
        self.filesystem.write_index_location(index_location)
        return index_location

    def _update_block_info(self, current_block):
        formatted_data = DataBlock.extract_block_location(current_block)
        current_block.next_block_location = formatted_data['header']
        current_block.data = formatted_data['file_data']

    def _read_dfs_file(self, location):
        result = DumpsterNode(self.filesystem, None)
        # get the first datablock so we can start reconstructing the file
        first_block = self.filesystem.read(location)
        if first_block:
            self._update_block_info(first_block)
            result.data_blocks.append(first_block)

            current_block = first_block
            if current_block.next_block_location:
                while True:
                    current_block = self.filesystem.read(current_block.next_block_location)
                    self._update_block_info(current_block)
                    result.data_blocks.append(current_block)

                    if not current_block.next_block_location:
                        break
        return result

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
            block.data = DataBlock.embed_block_location(block)
            previous_block_location = self.filesystem.write(block)

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
        return self._update_index(new_dir)

    def create_new_file(self, path, update_index=True):
        return self.write_file(path, '', update_index)

    def write_file(self, path, data, update_index=True):
        new_file = DumpsterNode(self.filesystem, path)
        # default to utf-8 for all strings
        if type(data) == str:
            bytes = bytearray(data, encoding='utf-8')
            new_file.write(bytes)
        elif is_bytes(data):
            new_file.write(data)

        new_file.block_start_location = self._write_dfs_file(new_file)
        if update_index:
            self._update_index(new_file)

        return new_file.block_start_location
