# DumpsterFS


Portable filesystem that is designed to be compatible with services like Hastebin, Github, Pastebin and other services that allow uploading text files. Performance will be poor and its more a proof of concept than a real working solution, i am just trying to have some fun with fileystems. 

It supports two different storage backends at the moment, you can choose to write and read from your local filesystem, it will store everything in /tmp/local_dfs. Or you can choose to store everything to your local hastebin instance, it will assume that your hastebin instance is running at http://localhost:7777 

The directory or location of Hastebin cannot be changed by configuration right now. This is something that i am going to add later!  

At this moment i have no build system in place, so if you want to run it install the following.

## installation for Ubuntu  
apt-get install Python3.7  
apt-get install pip3  

pip3 install fusepy  
pip3 install numpy  

git clone this repository and start with `python3 fuse_dfs.py /your_mount_point/ <storage_option>`

for storage options there are two valid values, 'hastebin and local'. If you choose to go for hastebin, make your sure you have a local hastebin instance running, one way to get it running quickly is by spinning up a docker container. I suggest using this one. https://hub.docker.com/r/rlister/hastebin  


Tests can be run with `python3 tests.py`, this will generate some residue in /tmp/local_dfs, nothing to be concerned of, in future versions i will switch the testing over to a in memory filesystem

Currently configured to dump all the fileblocks into /tmp/local_dfs. In the future i will make this configurable. 

## Features

- basic filesystem operations (mkdir,create file, read file) are working
- It can even handle deep directory nesting and things like find, touch, cat o_0 
- Mediocre read and write speeds for people that dislike performance,
- accidental copy on write implementation, because it needs to be compatible with Hastebin (meaning write once, write again somewhere else)

I have not tested it anywhere else besides my laptop, so i could be missing something.   

## Known shortcomings  
- user permissions, the filesystem does not support user permissions, this is more something that is nice to have, not really a priority 

- symlinks are not yet implemented  

- block size is limited to 4096 bytes because the current implementation does not support block appending after it is being written and fusepy delivers files in 4096 byte chunks, so that is what the maximum block size is at the moment. 


## Planned features 

- Implement missing filesystem calls, currently the fuse implementation is not complete, i want to aim for at least POSIX compliance.
- Hardbin Adapter, persist everything on hardbin which is connected to the IPFS!
- Yaml settings, so configuring everything will be as easy and quick
- Distributable package for several linux distro's, (Ubuntu, CentOS, Archlinux)



