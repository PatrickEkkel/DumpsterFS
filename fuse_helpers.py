import time
from stat import S_IFDIR, S_IFLNK, S_IFREG

def create_lstat(node_type=S_IFREG,st_nlink=1,st_ctime=time.time(), st_mtime=time.time(),st_atime=time.time()):

  # init the fileinfo struct, set default to regular file,
  # because we don't support directories atm
 return  {'st_atime': st_atime,
    'st_ctime': st_ctime,
    'st_gid': 1000,
    'st_mode': node_type,
    'st_mtime': st_mtime,
    'st_nlink': st_nlink,  # 1 because we don't support symlinks
    'st_uid': 1000 } # default to 1000, user ownership is not something we need
                     # right away
