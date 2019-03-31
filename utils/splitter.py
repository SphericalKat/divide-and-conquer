def split_file(file_name, no_of_users=1):
    file = open(file_name, 'rb')
    extension = file_name.split(".")[1]
    data = file.read()
    file.close()
    print(len(data))
    chunk_size = len(data) // no_of_users

    if len(data) % no_of_users != 0:
        chunk_size += 1

    no_of_chunks = len(data) // chunk_size
    if len(data) % chunk_size != 0:
        no_of_chunks += 1

    print(chunk_size)

    files = ["chunk" + str(i) + "." + extension for i in range(no_of_chunks)]
    for i in range(no_of_users):
        file = open(files[i % no_of_chunks], 'wb')
        file.write(data[:chunk_size])
        file.close()
        data = data[chunk_size:]

# if __name__ == "__main__":
#     split_file("test.jpg", 3)
