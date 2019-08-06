from dumpsterfs import DumpsterFS
from filesystems import InMemoryFileSystem, LocalFileSystem, LocalFileWriteCache


lfs = LocalFileSystem()
lfc = LocalFileWriteCache(lfs)
dfs = DumpsterFS(lfs, lfc)
print(dfs._get_index().index)
