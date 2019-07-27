class DataBlock:

    block_size = 10
    header_size = 255
    # random set of selected bytes to mark the end of the header useable data
    # prolly a bad idea, we are not going for reliability... if its crap
    # we will find something better
    header_end_byte_marker = '\x51\x00\x00\x50'

    NEW = 0
    IN_CACHE = 1
    PERSISTED = 2

    def __init__(self, storage_method):
        self.next_block_location = None
        self.storage_method = storage_method
        self.state = DataBlock.NEW
        self.data = None


class Index:

    def __init__(self):
        self.index_location = None
        self.storage_method = None

    def find(self, filename):
        pass
