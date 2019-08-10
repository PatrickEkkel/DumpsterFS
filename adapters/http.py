import requests
from interfaces import DataReaderWriter

class HttpReaderWriter(DataReaderWriter):

    def __init__(self):
        self.URL = 'http://localhost:7777'

    def file_exists(self, path):
        request_url = f' {self.URL}/documents/{path}'
        response = requests.get(request_url)
        return response.status_code == 200

    def delete_file(self, filename):
        pass

    def write_file(self, path, data):
        request_url = f' {self.URL}/documents'
        response = requests.post(request_url, data=data)
        json_response = response.json()
        key = json_response['key']
        return  f'{self.URL}/documents/{key}'


    def read_file(self, path):
        response = requests.get(path)
        json_response = response.json()
        return json_response['data']
