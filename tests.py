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
print(dumpster_fs._get_index().__dict__)
#print(dumpster_fs.list_dir('/'))
