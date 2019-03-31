def read_chunks(file_names):
    files = []
    for file_name in file_names:
        chunk = open(file_name, 'rb')
        files.append(chunk)
        return files
