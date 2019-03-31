def join_files(file_names):
    file = open("joined_file.jpg", 'wb')

    for file_name in file_names:
        chunk = open(file_name, 'rb')
        file.write(chunk.read())

    file.close()


# if __name__ == "__main__":
#     l = ['chunk0.jpg', 'chunk1.jpg', 'chunk2.jpg']
#     join_files(l)
