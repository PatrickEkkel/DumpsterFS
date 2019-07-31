# DumpsterFS


Portable filesystem that is designed to be compatible with services like Hastebin, Github, Pastebin and other services that allow uploading text files. Performance will be poor and its more a proof of concept than a real working solution, i am just trying to have some fun with fileystems. Currently it can only write to disk or run as an in memory file system, in the future its planned to implement Hastebin and Git as possible options for a filesystem and maybe more crazy services that come to my mind. 

At this moment i have no build system in place, so if you want to run it install the following.

## installation for Ubuntu  
apt-get install Python3.7  
apt-get install pip3  

pip3 install fusepy  
pip3 install numpy  

git clone this repository and start with `python3 fuse_dfs.py /your_mount_point/`  

Tests can be run with `python3 tests.py`, there is still not much going with tests, but i got it all setup for writing unit tests :-) 

its currently configured to dump all the blocks into /tmp/local_dfs. In the future we will make this configurable. For unit testing purposed i have also included an in memory filesystem. 

I have not tested it anywhere else besides my laptop, so i could be missing something.   


## Known shortcomings  
- big files, it can't handle big files, because writing is done in one large operation and the write method expects that you deal with offset and streams, this is a must have if this filesystem is going to be of any use,

- user permissions, the filesystem does not support user permissions, this is more something that is nice to have, not really a priority 

- missing implementation, rename, symlinks, stat, rmdir are not implemented 

