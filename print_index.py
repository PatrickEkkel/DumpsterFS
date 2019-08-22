from dumpsterfs import DumpsterFS
from filesystems.hastebin import HasteBinFileSystem
from filesystems.lfs import LocalFileSystem
from caching.lfs_write_cache import LocalFileWriteCache
from caching.inmemory_read_cache import InMemoryReadCache



hbfs = HasteBinFileSystem()
lfs = LocalFileSystem()
lwc = LocalFileWriteCache(lfs)
lrc = InMemoryReadCache()
dfs = DumpsterFS(lfs, lwc, lrc)
print(dfs._get_index().index['index_dict'])
