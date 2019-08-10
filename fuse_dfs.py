#!/usr/bin/env python
from __future__ import with_statement

from dumpsterfs import DumpsterFS
from filesystems.lfs import LocalFileSystem
from filesystems.hastebin import HasteBinFileSystem
from caching.lfs_write_cache import LocalFileWriteCache
import logging
import os
import sys
import time
import errno

from fuse import FUSE, FuseOSError, Operations,  LoggingMixIn
from errno import ENOENT

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)



class FuseDFS(LoggingMixIn, Operations):
    def __init__(self, filesystem):
        if filesystem == 'local':
            selected_filesystem = LocalFileSystem()
        elif filesystem == 'hastebin':
            selected_filesystem = HasteBinFileSystem()
        else:
            selected_filesystem = LocalFileSystem()

        lfc = LocalFileWriteCache(LocalFileSystem())
        self.dfs = DumpsterFS(selected_filesystem,lfc)
        self.truncated_fd = -1

    # Filesystem methods
    # ==================


    def chmod(self, path, mode):
        # rights are not something we care about at the moment therefore, just pass
        pass

    def chown(self, path, uid, gid):
        # rights are not something we care about at the moment therefore, just pass
        pass

    def getattr(self, path, fh=None):
        result  = self.dfs.get_file_info(path)
        if not result:
            raise FuseOSError(ENOENT)

        logger.debug(f'getattr: {result}')

        return result


    def readdir(self, path, fh):
        logger.debug(f'readdir: {path}')
        dirents = ['.', '..']
        dirents.extend(self.dfs.list_dir(path))
        for r in dirents:
            yield r

    def readlink(self, path):
        logger.debug(f'readlink: {path}')
        return self.dfs.readlink(path)

    def mknod(self, path, mode, dev):
        print('mknod')
        print   (path)
        return os.mknod(self._full_path(path), mode, dev)

    def rmdir(self, path):
        logger.debug(f'rmdir: {path}')
        self.dfs.delete(path)
    def mkdir(self, path, mode):
        result = self.dfs.create_dir(path)
        logger.debug(f'mkdir: {result} ')

    def statfs(self, path):
        logger.debug(f'statfs: {path}')
        return dict(f_bsize=512, f_blocks=4096, f_bavail=2048)

    def unlink(self, path):
        logger.debug(f'unlink: {path}')
        self.dfs.delete(path)

    def symlink(self, name, target):
        logger.debug(f'symlink: name: {name} target: {target}')
        # just put slash in front of it, quick hack to get symlinks working
        self.dfs.symlink(name, target)

    def rename(self, old, new):
        logger.debug(f'rename: {old} {new}')
        self.dfs.rename(old, new)

    def link(self, target, name):
        print('link')
        return os.link(self._full_path(target), self._full_path(name))

    def utimens(self, path, times=None):
        logger.debug(f'utimes:  path:  {path} times: {times}')
        now = time.time()
        atime, mtime = times if times else (now, now)
        self.dfs.set_file_info(path,'st_atime',atime)
        self.dfs.set_file_info(path,'st_mtime',mtime)

    # File methods
    # ============

    def open(self, path, flags):
        logger.debug(f'open: path: {path}')
        return self.dfs.open_file(path)

    def create(self, path, mode, fi=None):
        logger.debug(f'create: path: {path} ')
        self.fd = self.dfs.create_new_file(path)
        return self.fd

    def read(self, path, length, offset, fh):

        logger.debug(f'read: path: {path}  length: {length} offset: {offset} fd: {fh}')
        size = offset + length
        result = []
        result = bytes(self.dfs.read_file(fh, offset, size))
        if result is None:
            return []
        return result

    def write(self, path, buf, offset, fh):
        buf_length = len(buf)
        logger.debug(f' write: path: {path} offset: {offset} buf_len: {buf_length} fh: {fh}')
        self.dfs.write_file(buf, fh)
        return buf_length

    def flush(self, path, fh):
        logger.debug(f' flush: path: {path} fh: {fh}')
        self.dfs.flush()

    def truncate(self, path, length, fh=None):
        logger.debug(f'truncate: path: {path} length: {length} fh: {fh}')
        self.dfs.truncate(path,length)

    def release(self, path, fh):
        logger.debug(f' release: {path}')
        self.dfs.release(fh)


def main(mount_point,filesystem):
    FUSE(FuseDFS(filesystem), mount_point,nothreads=True, foreground=True)

if __name__ == '__main__':
    main(sys.argv[1],sys.argv[2])
