from abc import abstractmethod
import base64
import json
import os, binascii
import sys
import errno
import numpy as np
from datatypes import DataBlock, Index, DumpsterFile
from interfaces import StorageMethod, DataReaderWriter
from filesystems import LocalFileSystem


class DumpsterFS:

    def __init__(self, file_system):
        self.index = None
        self.filesystem = file_system

    def init_filesystem(self):
        # get the last known location for the index file
        index_location = self.filesystem.get_index_location()
        # no index present, this means this is a blank filesystem, we have to
        # create an indexfile and store the value in the bootstrap file
        if not index_location:
            # file system initialization, should move to seperate method
            index_path = '/.dfs_index'
            index = self.filesystem.create_index()
            index.add(index_path, 'None')
            # don't update the index, because it would trigger an infinite loop
            index_location = self.create_file('/.dfs_index', index.to_json(), update_index=False)
            self.filesystem.write_index_location(index_location)
        return index_location

    def _get_index(self):
        # guarantees that the filesystem is ready for use
        index_location = self.init_filesystem()
        dfs_handle = self._read_dfs_file(index_location)
        index = self.filesystem.create_index()
        json_index = base64.b64decode(dfs_handle.get_base64())
        index.index = Index.from_json(json_index)
        return index

    def _update_index(self, path, new_entry):
        # guarantees that the filesystem is ready for use
        index_location = self.init_filesystem()

        dfs_handle = self._read_dfs_file(index_location)
        json_index = base64.b64decode(dfs_handle.get_base64())
        index = self.filesystem.create_index()
        index.index = Index.from_json(json_index)
        index.add(path, new_entry)
        index_location = self.create_file('/.dfs_index', index.to_json(), update_index=False)
        self.filesystem.write_index_location(index_location)

    def _update_block_info(self, current_block):
        formatted_data = DataBlock.extract_block_location(current_block)
        current_block.next_block_location = formatted_data['header']
        current_block.data = formatted_data['file_data']

    def _read_dfs_file(self, location):
        result = DumpsterFile(self.filesystem, None)
        # get the first datablock so we can start reconstructing the file
        first_block = self.filesystem.read(location)
        self._update_block_info(first_block)
        result.data_blocks.append(first_block)

        current_block = first_block

        while True:
            current_block = self.filesystem.read(current_block.next_block_location)
            self._update_block_info(current_block)
            result.data_blocks.append(current_block)

            if not current_block.next_block_location:
                break

        # print(base64.b64decode(result.get_base64()))
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

    def create_file(self, path, data, update_index=True):
        new_file = DumpsterFile(self.filesystem, path)
        # default to utf-8 for all strings
        if type(data) == str:
            bytes = bytearray(data, encoding='utf-8')
            new_file.write(bytes)
            block_start_location = self._write_dfs_file(new_file)
            if update_index:
                self._update_index(path, block_start_location)
            return block_start_location
