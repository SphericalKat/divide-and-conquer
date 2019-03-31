import os


def join_files(output_name):
    file = open(output_name, 'wb')
    file_names = os.listdir('split')
    file_names.sort()
    print(file_names)

    for file_name in file_names:
        chunk = open(os.path.join('split', file_name), 'rb')
        file.write(chunk.read())

    file.close()


if __name__ == "__main__":
    join_files('test_archive_joined.zip')
