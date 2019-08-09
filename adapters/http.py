import requests
from interfaces import DataReaderWriter
class HttpReaderWriter(DataReaderWriter):

    def __init__(self):
        self.URL = 'http://localhost:7777/documents'

    def file_exists(self, path):
        pass

    def delete_file(self, filename):
        pass

    def write_file(self, path, data):
        response = requests.post(self.URL, data=data)
        json_response = response.json()
        print(json_response)
        key = json_response['key']
        return "http://localhost:7777/%s" % key


    def read_file(self, path):
        pass
