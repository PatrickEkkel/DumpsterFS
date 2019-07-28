from dumpsterfs import DumpsterFS
from filesystems import LocalFileSystem

dumpster_fs = DumpsterFS(LocalFileSystem())
#dumpster_fs.create_file('/test','some random string to put in a file')

dumpster_fs.create_file('/dikke_tests','kakakakakakakakakakakak')
