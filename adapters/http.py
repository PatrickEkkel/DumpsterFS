import requests
from interfaces import DataReaderWriter

class HttpReaderWriter(DataReaderWriter):

    def __init__(self,URL):
        self.URL = URL

    def file_exists(self, path):
        response = requests.get(path)
        return response.status_code == 200

    def delete_file(self, filename):
        pass

    def write_file(self, path, data):
        response = requests.post(self.URL, data=data)
        return response

    def read_file(self, path):
        return requests.get(path)
