import sys
from dumpsterfs import DumpsterFS
from filesystems import InMemoryFileSystem, LocalFileSystem, LocalFileCache


lfs = LocalFileSystem()
lfc = LocalFileCache(lfs)
dfs = DumpsterFS(lfs, lfc)
print(dfs.read_file(sys.argv[1]))
