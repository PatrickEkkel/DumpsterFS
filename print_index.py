from dumpsterfs import DumpsterFS
from filesystems import InMemoryFileSystem, LocalFileSystem, LocalFileCache


lfs = LocalFileSystem()
lfc = LocalFileCache(lfs)
dfs = DumpsterFS(lfs, lfc)
print(dfs._get_index().index)
