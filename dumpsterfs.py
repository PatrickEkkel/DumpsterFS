from abc import abstractmethod
import base64
import json
import os,binascii
import sys
import errno
import numpy as np
from datatypes import DataBlock, Index
from interfaces import StorageMethod, DataReaderWriter
from filesystems import LocalFileSystem


class DumpsterFile:

    def __init__(self,file_system, path):
        self.data_blocks = []
        self.filesystem = file_system
        self.path = path

    def get_base64(self):
        result = ''
        for block in self.data_blocks:
            result += block.data
        return result

    def write(self, bytes):
        bytes = base64.b64encode(bytes)
        file_length = len(bytes)
        block_size_counter = 0
        i = 0
        p = 0
        while file_length != 0:
            file_length -= 1
            # causes typical off by one size difference, but we don't care (for now)
            if (DataBlock.block_size-1) == block_size_counter:
                block_size_counter = 0
                new_data_block = self.filesystem.create_data_block()
                new_data_block.data = bytes[p:i]
                self.data_blocks.append(new_data_block)
                p = i
            # get the last part of the file that doesn't fit max block_size
            elif file_length < DataBlock.block_size:
                new_data_block = self.filesystem.create_data_block()
                self.data_blocks.append(new_data_block)
                p = len(bytes) - file_length
                new_data_block.data = bytes[p:len(bytes)]

                break;

            block_size_counter += 1

            i += 1
    def deserialize():
        pass

    def serialize():
        pass

class DumpsterFS:

    def __init__(self, file_system):
        self.index = None
        self.filesystem = file_system
    def connect(self):
        pass

    def _extract_blocklocation(self,block):
        data = block.data
        print(base64.b64decode(data))
        block_data =  base64.b64decode(data).decode().split(DataBlock.header_end_byte_marker)
        if block_data[0] == 'None':
            block_data[0] = None
        return {'header':  block_data[0], 'file_data': block_data[1]}

    def _embed_blocklocation(self, block):
        data = block.data
        nbl = block.next_block_location
        if nbl is not None:
            # location is always text, so utf-8 encode it and send it
            encoded_header = base64.b64encode((nbl + DataBlock.header_end_byte_marker).encode('utf-8'))
            prepared_header = base64.b64decode(encoded_header)
        else:
            prepared_header = ('None' + DataBlock.header_end_byte_marker).encode('utf-8')


        data_to_write = base64.b64encode(prepared_header + block.data)
        #print(base64.b64decode(data_to_write).decode())


        return base64.b64encode(prepared_header + block.data).decode()


    def _update_index(self,new_entry):
        # get the last known location for the index file
        initial_data = self.filesystem.get_index_location()
        # no index present, this means this is a blank filesystem, we have to
        # create an indexfile and store the value in the bootstrap file
        if not initial_data:
            # file system initialization, should move to seperate method
            index_path = '/.dfs_index'
            index =  self.filesystem.create_index()
            index.add(index_path,'None')
            # don't update the index, because it would trigger an infinite loop
            index_location = self.create_file('/.dfs_index',index.to_json(),update_index=False)
            self.filesystem.write_index_location(index_location)
        else:
            self._read_dfs_file(initial_data)

    def _read_dfs_file(self, location):
        result = DumpsterFile(self.filesystem, None)
        # get the first datablock so we can start reconstructing the file
        first_block = self.filesystem.read(location)
        formatted_data = self._extract_blocklocation(first_block)
        first_block.next_block_location = formatted_data['header']
        first_block.data = formatted_data['file_data']
        print(first_block.data.decode())
        result.data_blocks.append(first_block)

        current_block = first_block
        while current_block.next_block_location:
            current_block =  self.filesystem.read(current_block.next_block_location)
            result.data_blocks.append(current_block)
            formatted_data = self._extract_blocklocation(current_block)
            current_block.next_block_location = formatted_data['header']
            current_block.data = formatted_data['file_data']
            result.data_blocks.append(current_block)

        #print(result.get_base64())


        return result
    def _write_dfs_file(self,dfs_file):
        # write the chunks in reversed order, this is easy for later, because the
        # chunks are chained together like a linked list and we we want to read the file, from
        # first to last, every chunk contains a reference to the next_chunk, the
        # location is not in our control so we can't generate the references
        # beforehand
        data_blocks = reversed(dfs_file.data_blocks)
        previous_block_location = None
        for block in data_blocks:
            block.next_block_location = previous_block_location
            block.data = self._embed_blocklocation(block)

            previous_block_location = self.filesystem.write(block)

        # return the first block location
        return previous_block_location

    def read_file(self,path,data):
        pass

    def create_file(self,path, data, update_index=True):
        new_file = DumpsterFile(self.filesystem, path)
        # default to utf-8 for all strings
        if type(data) == str:
            bytes = bytearray(data,encoding='utf-8')
            new_file.write(bytes)
            block_start_location = self._write_dfs_file(new_file)
            if update_index:
                self._update_index(block_start_location)
            return block_start_location
