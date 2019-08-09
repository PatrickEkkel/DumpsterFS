from interfaces import ReadCachingMethod

class InMemoryReadCache(ReadCachingMethod):
    # quick little in memory cache to serve as a buffer for the fuse interface
    def read_file(self,fd, offset, length):
        if length > len(self.filecache_dict[fd]):
            return self.filecache_dict[fd][offset:length]#.decode('utf-8')
        return self.filecache_dict[fd][offset:length]

    def write_file(self,data, fd,offset,length):
        self.filecache_dict[fd] = data[offset:length]

    def exists(self, fd):
        result = self.filecache_dict.get([fd])
        return result

    def clear(self):
        self.filecache_dict = {}

    def __init__(self):
        ReadCachingMethod.__init__(self)
        self.filecache_dict = {}
