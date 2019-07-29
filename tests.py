from dumpsterfs import DumpsterFS
from filesystems import LocalFileSystem

local_file_system = LocalFileSystem()
dumpster_fs = DumpsterFS(local_file_system)

dumpster_fs.create_file('/test', 'some random string to put in a file')
dumpster_fs.create_file('/dikke_tests', 'kakakakakakakakakakakak')
dumpster_fs.create_file('/some/dir/deep/down/lalalal', 'gekke henkie 3.0')

print(dumpster_fs.read_file('/some/dir/deep/down/lalalal'))



