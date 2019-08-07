# DumpsterFS


Portable filesystem that is designed to be compatible with services like Hastebin, Github, Pastebin and other services that allow uploading text files. Performance will be poor and its more a proof of concept than a real working solution, i am just trying to have some fun with fileystems. Currently it can only write to disk or run as an in memory file system, in the future its planned to implement Hastebin and Git as possible options for a filesystem and maybe more crazy services that come to my mind. 

At this moment i have no build system in place, so if you want to run it install the following.

## installation for Ubuntu  
apt-get install Python3.7  
apt-get install pip3  

pip3 install fusepy  
pip3 install numpy  

git clone this repository and start with `python3 fuse_dfs.py /your_mount_point/`  

Tests can be run with `python3 tests.py`, this will generate some residue in /tmp/local_dfs, nothing to be concerned of, in future versions i will switch the testing over to a in memory filesystem

its currently configured to dump all the blocks into /tmp/local_dfs. In the future we will make this configurable. For unit testing purposed i have also included an in memory filesystem. 

## Features

- basic filesystem operations (mkdir,create file, read file) are working
- It can even handle deep directory nesting and things like find, touch, cat o_0 
- Mediocre read and write speeds for people that dislike performance,
- accidental copy on write implementation, because it needs to be compatible with Hastebin (meaning write once, write again somewhere else)

I have not tested it anywhere else besides my laptop, so i could be missing something.   

## Known shortcomings  
- user permissions, the filesystem does not support user permissions, this is more something that is nice to have, not really a priority 

- missing implementation, rename, symlinks, stat, rmdir are not implemented 

- block size is limited to 4096 bytes because the current implementation does not support block appending after it is being written and fusepy delivers files in 4096 byte chunks, so that is what the maximum block size is at the moment. 


