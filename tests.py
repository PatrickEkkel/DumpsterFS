import json
from dumpsterfs import DumpsterFS
from filesystems import LocalFileSystem

local_file_system = LocalFileSystem()
dumpster_fs = DumpsterFS(local_file_system)


#print(dumpster_fs._get_index().index)

print(dumpster_fs.read_file('/wat'))
#print(dumpster_fs.read_file('/henk_met_de_korte_achternaam'))
#dumpster_fs.create_new_file('/henk_met_de_korte_achternaam')
#block_pointer = dumpster_fs.write_file('/henk_met_de_korte_achternaam','stukkie tekst')
#print(block_pointer)
