
cutter_types = {
    2: 'video/mp4',
    3: 'audio/mpeg',
}
def content_cutter(file_name):
    with open(f'.{file_name}', 'rb') as file:
        while chunk:= file.read(1024 * 1024):
            yield chunk
