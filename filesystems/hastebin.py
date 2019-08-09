from interfaces import StorageMethod

class HasteBinFileSystem(StorageMethod):

    def create_new_file_handle(self, path, type):
        pass

    def release_file_handle(self, fd):


    def get_file_handle(self, fd):


    def get_file_handle_by_path(self, path):
        pass

    def update_filehandle(self, file_handle):
        pass

    def __init__(self):
        super(StorageMethod).__init__()

    def read(self, location):
        pass

    def write_index_location(self, location):
        pass

    def get_index_location(self):
        pass

    def write(self, data_block):
        pass
