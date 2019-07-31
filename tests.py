import json
import unittest
from dumpsterfs import DumpsterFS
from filesystems import InMemoryFileSystem, LocalFileSystem


#dumpster_fs = DumpsterFS(local_file_system)
#print(.index)


class DumpsterFSTests(unittest.TestCase):
    def setUp(self):
        self.filesystem = InMemoryFileSystem()
        self.dumpster_fs = DumpsterFS(self.filesystem)

    def test_file_creation(self):
        #new_file = self.dumpster_fs.create_new_file('/multilayered/dir/')
        #print(new_file)
        new_file = self.dumpster_fs.write_file('/test/1/t', 'geert')
        self.dumpster_fs._get_index().find('/test/1/t')


if __name__ == '__main__':
    unittest.main()
