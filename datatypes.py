import base64
import json
import time
import fuse_helpers


class DumpsterNode:

    def __init__(self, file_system, path, node_type=33204):
        self.data_blocks = []
        self.filesystem = file_system
        self.block_start_location = None
        self.path = path


        self.lstat = fuse_helpers.create_lstat(node_type=node_type)
        #self.lstat = {'st_atime': '',
        #'st_ctime': '',
        #              'st_gid': 1000,
        #              'st_mode': node_type,
        #              'st_mtime': '',
        #              'st_nlink': 1,  # 1 because we don't support symlinks
        #              'st_uid': 1000}

    def get_base64(self):
        result = ''
        for block in self.data_blocks:
            result += block.data
        return result

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
        block_size_counter = 0
        i = 0
        p = 0
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

    block_size = 10
    # random set of selected bytes to mark the end of the header useable data
    # prolly a bad idea, we are not going for reliability... if its crap
    # we will find something better
    header_end_byte_marker = 'F00F'

    NEW = 0
    IN_CACHE = 1
    PERSISTED = 2

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

    def __init__(self, storage_method):
        self.next_block_location = None
        self.storage_method = storage_method
        self.state = DataBlock.NEW
        self.data = None


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
