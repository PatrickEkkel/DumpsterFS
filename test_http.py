from adapters.http import HttpReaderWriter
from adapters.localfilesystem import LocalDataReaderWriter
http_data_reader_writer = HttpReaderWriter()
lfs_data_reader_writer = LocalDataReaderWriter()


#print(http_data_reader_writer.write_file('/somefile/','somedata'))
#print(lfs_data_reader_writer.write_file('somefilelol','somedata'))
print(http_data_reader_writer.file_exists('agumerterterefoyaq'))
