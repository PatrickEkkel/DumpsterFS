from adapters.http import HttpReaderWriter

data_reader_writer = HttpReaderWriter()

print(data_reader_writer.write_file('/somefile/','somedata'))
