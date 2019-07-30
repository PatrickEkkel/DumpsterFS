#!/usr/bin/env python
from __future__ import with_statement

from dumpsterfs import DumpsterFS
from filesystems import LocalFileSystem
import logging
import os
import sys
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
    def __init__(self, root):
        self.root = root
        self.dfs = DumpsterFS(LocalFileSystem())
        self.fd = 0

    # Helpers
    # =======

    def _full_path(self, partial):
        if partial.startswith("/"):
            partial = partial[1:]
        path = os.path.join(self.root, partial)
        return path

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
        dirents = ['.', '..']
        dirents.extend(self.dfs.list_dir(path))
        #logger.debug(f'readdir: {dirents}')
        for r in dirents:
            yield r


    def readlink(self, path):
        print('readlink')
        pathname = os.readlink(self._full_path(path))
        if pathname.startswith("/"):
            # Path name is absolute, sanitize it.
            return os.path.relpath(pathname, self.root)
        else:
            return pathname

    def mknod(self, path, mode, dev):
        print('mknod')
        print   (path)
        return os.mknod(self._full_path(path), mode, dev)

    def rmdir(self, path):
        full_path = self._full_path(path)
        return os.rmdir(full_path)

    def mkdir(self, path, mode):
        result = self.dfs.create_dir(path)
        logger.debug(f'mkdir: {result} ')

    def statfs(self, path):
        print('statfs')
        full_path = self._full_path(path)
        stv = os.statvfs(full_path)
        return dict((key, getattr(stv, key)) for key in ('f_bavail', 'f_bfree',
            'f_blocks', 'f_bsize', 'f_favail', 'f_ffree', 'f_files', 'f_flag',
            'f_frsize', 'f_namemax'))

    def unlink(self, path):
        return os.unlink(self._full_path(path))

    def symlink(self, name, target):
        return os.symlink(name, self._full_path(target))

    def rename(self, old, new):
        return os.rename(self._full_path(old), self._full_path(new))

    def link(self, target, name):
        return os.link(self._full_path(target), self._full_path(name))

    def utimens(self, path, times=None):
        return os.utime(self._full_path(path), times)

    # File methods
    # ============

    def open(self, path, flags):
        self.fd += 1
        logger.debug(f'open: ' + path)
        return self.fd

    def create(self, path, mode, fi=None):
        self.fd += 1
        logger.debug(f'create: {path} fd: {self.fd} ')
        self.dfs.create_new_file(path)
        return self.fd

    def read(self, path, length, offset, fh):

        #if length and offset:
        logger.debug(f'read: {path} {length} {offset}')
        #else:
        #    logger.debug(f'read: {path} ')

        result = self.dfs.read_file(path)
        if result is None:
            return []
        #os.lseek(fh, offset, os.SEEK_SET)
        #return os.read(fh, length)

    def write(self, path, buf, offset, fh):
        logger.debug(f' write: {path} {offset}')
        #print(buf)
        #print(offset)
        print(type(buf))
        self.dfs.write_file(path, buf,update_index=False)
        #os.lseek(fh, offset, os.SEEK_SET)
        #return os.write(fh, buf)
        return len(buf)
    def truncate(self, path, length, fh=None):
        print('truncate')
        #full_path = self._full_path(path)
        #with open(full_path, 'r+') as f:
        #    f.truncate(length)

    # disable flush, there is no need to do writebacks and file cleanup
    #def flush(self, path, fh):

        #print(fh)
        #return os.fsync(fh)

    def release(self, path, fh):
        logger.debug(f' release: {path}')


def main():
    FUSE(FuseDFS('/home/patrick/fuse_test'), '/home/patrick/External', nothreads=True, foreground=True)

if __name__ == '__main__':
    main()
