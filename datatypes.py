import base64
import json
import time
import fuse_helpers
import ntpath
import numpy
import os

class WriteOperationTooBig(Exception):
    pass


class BlockNotWriteable(Exception):
    pass


class DumpsterNode:

    def __init__(self, file_system, path, node_type=33204):
        self.data_blocks = []
        self.filesystem = file_system
        self.block_start_location = None
        self.path = path
        self.length = 0
        self.lstat = fuse_helpers.create_lstat(node_type=node_type)
        self.block_pointer = 0

    def get_base64(self):
        result = ''
        for block in self.data_blocks:
            result += block.data
        return result

    def get_next_available_block(self, buffer_length):
        # buffer_length should never exceed max_block_length because this would mean 1 write operation
        # yields multiple blocks, which is something we don't want because it involves more
        # complexity

        if buffer_length > DataBlock.block_size:
            raise WriteOperationTooBig()

        if len(self.data_blocks) > 0:
            last_block = self.data_blocks[-1]
            # check if it fits into an existing datablock
            remaining_block_space = DataBlock.block_size - last_block.length
            if remaining_block_space >= buffer_length:
                return last_block
            else:
                new_block = self.filesystem.create_data_block()
                self.data_blocks.append(new_block)
        else:
            new_block = self.filesystem.create_data_block()
            self.data_blocks.append(new_block)
            return new_block

    def set_file_creation_time(self, time):
        self.lstat['st_ctime'] = time

    def set_file_modification_time(self, time):
        self.lstat['st_mtime'] = time

    def set_file_access_time(self, time):
        self.lstat['st_atime'] = time

    def write(self, file_bytes):

        creation_time = time.time()

        self.set_file_access_time(creation_time)
        self.set_file_creation_time(creation_time)
        self.set_file_modification_time(creation_time)

        b64_encoded_bytes = base64.b64encode(file_bytes)
        file_length = len(b64_encoded_bytes)
        self.length = file_length
        block_size_counter = 0
        i = 0
        p = 0

        if file_length < DataBlock.block_size and file_length != 0:
            new_data_block = self.filesystem.create_data_block()
            new_data_block.data = b64_encoded_bytes[0:file_length]
            self.data_blocks.append(new_data_block)
        else:

            while file_length != 0:

                # causes typical off by one size difference, but we don't care (for now)
                if (DataBlock.block_size - 1) == block_size_counter:
                    block_size_counter = 0
                    new_data_block = self.filesystem.create_data_block()
                    new_data_block.data = b64_encoded_bytes[p:i]
                    self.data_blocks.append(new_data_block)
                    p = i
                    # get the last part of the file that doesn't fit max block_size
                    if file_length < DataBlock.block_size:
                        new_data_block = self.filesystem.create_data_block()
                        p = len(b64_encoded_bytes) - file_length
                        new_data_block.data = b64_encoded_bytes[p:len(b64_encoded_bytes)]
                        self.data_blocks.append(new_data_block)
                block_size_counter += 1
                file_length -= 1
                i += 1

    def deserialize(self):
        pass

    def serialize(self):
        pass


class DataBlock:

    block_size = 1000
    # random set of selected bytes to mark the end of the header useable data
    # prolly a bad idea, we are not going for reliability... if its crap
    # we will find something better
    header_end_byte_marker = 'F00F'

    NEW_NOT_COMMITTED = 0
    READY_NOT_COMMITTED = 1
    NEW_IN_CACHE = 2
    PERSISTED = 3

    @staticmethod
    def extract_block_location(block):
        data = block.data
        block_data = base64.b64decode(data).decode().split(DataBlock.header_end_byte_marker)
        if block_data[0] == 'None':
            block_data[0] = None
        return {'header': block_data[0], 'file_data': block_data[1]}

    @staticmethod
    def embed_block_location(block):
        nbl = block.next_block_location
        if nbl is not None:
            # location is always text, so utf-8 encode it and send it
            encoded_header = base64.b64encode(
                (nbl + DataBlock.header_end_byte_marker).encode('utf-8'))
            prepared_header = base64.b64decode(encoded_header)
        else:
            prepared_header = ('None' + DataBlock.header_end_byte_marker).encode('utf-8')

        return base64.b64encode(prepared_header + block.data).decode()

    def update_block_info(self):
        formatted_data = DataBlock.extract_block_location(self)
        self.next_block_location = formatted_data['header']
        self.data = formatted_data['file_data']

    def write(self, buf):
        # block is not yet written to medium, self.data should represent the actual state of affairs
        if self.state == DataBlock.NEW_NOT_COMMITTED:
            print('laat maar zien')
            #buf = (bytearray(buf, encoding='utf-8'))
            # print(self.data)
            self.data.extend(buf)
            print(len(self.data))
        else:
            raise BlockNotWriteable()

    def __init__(self, storage_method):
        self.next_block_location = None
        self.storage_method = storage_method
        self.state = DataBlock.NEW_NOT_COMMITTED
        self.data = []
        # property to keep track of the block_length, self.data is not safe to check, because we
        # can't keep everything in memory, this would be problematic for big files
        self.length = 0


class FileHandle:

    def __init__(self, fd, dfs_filehandle):
        self.fd = fd
        self.dfs_filehandle = dfs_filehandle


class Index:

    def __init__(self, storage_method):
        self.index_location = None
        self.storage_method = storage_method
        self.index = {'index_dict': {}, 'lstat_dict': {}}

    def to_json(self):
        return json.dumps(self.index)
        #return json.dumps({'index_dict': self.index_dict, 'lstat_dict': self.lstat_dict})

    @staticmethod
    def from_json(json_string):
        return json.loads(json_string)

    def add_info(self, path, info):
        self.index['lstat_dict'][path] = info

    def add(self, path, location):
        self.index['index_dict'][path] = location

    def info(self, path):
        return self.index_dict['lstat_dict'][path]

    def find(self, path, search_in='index_dict'):
            return self.index[search_in].get(path) #[path]
