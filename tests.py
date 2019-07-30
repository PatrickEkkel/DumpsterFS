import json
from dumpsterfs import DumpsterFS
from filesystems import LocalFileSystem

local_file_system = LocalFileSystem()
dumpster_fs = DumpsterFS(local_file_system)

#dumpster_fs.create_file('/ekkelsdir/mytextfiles','lekker lezens')
#dumpster_fs.create_file('/ekkelsdir/moredumps','garbage')
#dumpster_fs.create_file('/ekkelsdir/passwords','yourmom18765')
#dumpster_fs.create_file('/test','wat data')
#dumpster_fs.create_dir('/ekkelsdir')
#print(dumpster_fs._get_index())
dumpster_fs.create_dir('/some/nasty/dir/deep/down')
dumpster_fs.create_dir('/some/nasty/lol/lol/gekke/henkie')
dumpster_fs.create_dir('/foo/bar')
dumpster_fs.create_dir('/foo/bar/henk/bier/reeee')
dumpster_fs.create_dir('/foo/bar/3.0')
dumpster_fs.create_dir('/foo/bar/3.0/gerrit')
dumpster_fs.create_dir('/foo/bar/3.0/henk')
dumpster_fs.create_dir('/foo/bar/3.0/klaas/gerrit')



#print(dumpster_fs.list_dir('/foo/bar/3.0'))
print(dumpster_fs.list_dir('/foo/bar'))

#print(dumpster_fs._get_index().index['directory_dict'])
