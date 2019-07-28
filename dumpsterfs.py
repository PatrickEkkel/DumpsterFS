from abc import abstractmethod
import base64
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

    def write(self, bytes):
        bytes = base64.b64encode(bytes)
        file_length = len(bytes)
        block_size_counter = 0
        i = 0
        p = 0
        while file_length != 0:
            # causes typical off by one size difference, but we don't care (for now)
            if DataBlock.block_size == block_size_counter:
                block_size_counter = 0
                new_data_block = self.filesystem.create_data_block()
                new_data_block.data = bytes[p:i]
                self.data_blocks.append(new_data_block)
                p = i
            # get the last part of the file that doesn't fit max block_size
            elif file_length < DataBlock.block_size:
                new_data_block = self.filesystem.create_data_block()
                self.data_blocks.append(new_data_block)
                new_data_block.data = bytes[p:i]
                break;

            block_size_counter += 1
            file_length -= 1
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

    def _embed_blocklocation(self, block):
        data = block.data
        nbl = block.next_block_location
        # initialize a fixed length header to 0

        next_block_header =  [] #bytearray(b'\x00') * DataBlock.header_size
        if nbl is not None:
            # location is always text, so utf-8 encode it and send it
            #encoded_header = base64.b64encode(bytearray(nbl = DataBlock.header_end_byte_marker,encoding='utf-8'))
            encoded_header = base64.b64encode(bytearray(nbl + DataBlock.header_end_byte_marker, encoding='utf-8'))
            if len(encoded_header) > block.header_size + len(DataBlock.header_end_byte_marker):
                raise ValueError('next_block header size to small, increase DataBlock.header_size')
            else:
                # all is peachy and we prepend the encoded header to the data part
                empty_part =  block.header_size - len(encoded_header)
                prepared_header = base64.b64decode(encoded_header)

                if empty_part != 0:
                    prepared_header = bytearray(prepared_header) + bytearray('\x56',encoding='utf-8') * empty_part

        else:
            prepared_header = bytearray('\x56',encoding='utf-8') * (DataBlock.header_size + len(DataBlock.header_end_byte_marker))

        return base64.b64encode(prepared_header) + block.data


    def _update_index(self,new_entry):
        self.filesystem.get_index()


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


        self._update_index(previous_block_location)

        # return the first block location
        return previous_block_location

    def read_file(self,path,data):
        pass

    def create_file(self,path, data):
        new_file = DumpsterFile(self.filesystem, path)
        # default to utf-8 for all strings
        if type(data) == str:
            bytes = bytearray(data,encoding='utf-8')
            new_file.write(bytes)
            block_start_location = self._write_dfs_file(new_file)

            # at this point the file is stored in service and we should update the
            # index
