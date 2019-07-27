from abc import abstract_method

class DataWriter:

    @abstract_method
    def write_file(self, path, data):
        pass
        
    @abstract_method
    def read_file(self, path, data):
        pass


class Index:

    def __init__(self):
        self.index_location = None
        self.storage_method = None

    def find(self, filename):
        pass


class DumpsterFile:

    def __init__(self):
        self.data_blocks = []

    def deserialize():
        pass

    def serialize():
        pass

class DumpsterFS:

    def __init__(self):
        self.index = None:

    def connect(self):
        pass

    def create_file(self,path, data):
        pass

class DataBlock:

    def __init__(self):
        self.next_block_location = None
        self.storage_method = None
