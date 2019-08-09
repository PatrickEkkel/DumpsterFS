

class RamFs(StorageMethod):

    def __init__(self):
        super(StorageMethod).__init__()
        self.storage = {}
        self.index = ''

    def read(self, location):
        file = self.storage.get(location)
        datablock = self.create_data_block()
        datablock.data = file
        return datablock

    def write_index_location(self, location):
        self.index = location

    def get_index_location(self):
        return self.index

    def write(self, data_block):
        filename = binascii.b2a_hex(os.urandom(10))
        self.storage[filename.decode()] = data_block.data
        return filename.decode()
