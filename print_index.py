from dumpsterfs import DumpsterFS
from filesystems.hastebin import HasteBinFileSystem
from filesystems.lfs import LocalFileSystem
from caching.lfs_write_cache import LocalFileWriteCache



hbfs = HasteBinFileSystem()
lfs = LocalFileSystem()
lfc = LocalFileWriteCache(lfs)
dfs = DumpsterFS(lfs, lfc)
print(dfs._get_index().index)
