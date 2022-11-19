import sys
from pathlib import Path
from socket import *
from urllib.parse import urlparse

CACHE_HIT_SUCCESS = 1
CACHE_HIT_FAIL = 0

REQUEST_LINE_METHOD_INDEX = 0
REQUEST_LINE_URL_INDEX = 1
REQUEST_LINE_HTTP_VERSION_INDEX = 2

RESPONSE_STATUS_LINE = 0
RESPONSE_STATUS_CODE_INDEX = 1

# Creates a cache folder.
# If file already exists, it's a no-op.
Path("cache").mkdir(parents=True, exist_ok=True)

# Replaces special characters of a given string to the corresponding file name.
def convert_to_file_name(str):
    discionary = {'\\':'+', '/':'_', ':':'1', '*':'2', '?':'3', '<':'4', '>':'5', '|':'6'}
    for i in str:
        if i in discionary.keys():
            str = str.replace(i, discionary[i])

    return str

# Searches for a file and reads its content from the cache folder.
# Returns
# - content of the file if it exists.
# - None if it doesn't exists.
def search_cache(file):
    # Pass url, inside hash it to file_name.
    path = Path('cache/{}'.format(file))
    if path.is_file():
        return path.read_text()
    else:
        return None

# Saves file to the cache.
def save_to_cache(response_body):
    path = Path('cache/{}'.format(file_name))
    path.touch()
    path.write_text(('HTTP/1.1 200 OK\nCache-Hit:{}\n\n'.format(CACHE_HIT_SUCCESS) + response_body + '\n\n'))

# Extracts the status code from response message.
def extract_response_status(response):
    s_header = response.decode().split('\n')
    status = int((s_header[RESPONSE_STATUS_LINE].split())[RESPONSE_STATUS_CODE_INDEX])
    return status

# Processes a response message returned from server.
def process_response(response):
    status = extract_response_status(response)
    print('Response recieved from server, and status code is {}!'.format(status))
    response_body = get_response_body(response)
    if status == 200:
        save_to_cache(response_body)
        resp = ('HTTP/1.1 200 OK\nCache-Hit:{}\n\n'.format(CACHE_HIT_FAIL) + response_body + '\n\n')
        print('Write to cache, save time next time...')
    elif status == 404 or status == 200:
        resp = ('HTTP/1.1 404 NOT FOUND\nCache-Hit:{}\n\n404 NOT FOUND\n\n'.format(CACHE_HIT_FAIL))
        print('No cache writing...')
    else:
        resp = ('HTTP/1.1 500 INTERNAL ERROR\nCache-Hit:{}\n\nUnsupported Error\n\n'.format(CACHE_HIT_FAIL))
        print('No cache writing...')
    return resp

# Extract content from requested file.
def get_response_body(response):
    # Everything after empty line is response body.
    split_cont = response.decode().split('\r\n\r\n')
    cont = split_cont[1]
    return cont

# Makes a call to the server and returns its response.
def call_server(_url, req_line):
    # Parsing requested URL to retrieve hostname, port, and path.
    parsed_url = urlparse(_url)    
    port = parsed_url.port if parsed_url.port != None else 80
    method = req_line[REQUEST_LINE_METHOD_INDEX]
    path = parsed_url.path
    http_version = req_line[REQUEST_LINE_HTTP_VERSION_INDEX]
    host_name = parsed_url.hostname
    
    print('Sending the following msg from proxy to server: \n{}'.format(method + ' ' + path + ' ' + http_version))
    print('host:{}\nConnection close\n\n'.format(host_name))

    sock = socket(AF_INET, SOCK_STREAM)    
    sock.connect((host_name, port))
    req = "GET {} HTTP/1.1\r\nHost:{}\r\n\r\n".format(path, host_name)
    sock.send(bytes(req.encode()))
    response = sock.recv(4096)
    resp = process_response(response)
    sock.close()
    return resp

# Prints client connection and message from client request.
def print_client_info():
    print('Recieved a client connection from: {}'.format(str(addr)))
    print("Recieved a message from this client: {}".format(bytes(header[0].encode())))

# Listening socket port number...
SERVER_PORT = int(sys.argv[1])

# Initialize socket.
_socket = socket(AF_INET, SOCK_STREAM)
_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
_socket.bind(('', SERVER_PORT))

_socket.listen(1)

# Here, the program runs indefinitely listening for the requests and processing them as they come.
while True:
    print('\n\n******************* Ready to serve... *******************')

    # Wait for client connection.
    client, addr = _socket.accept()

    # Get the client request.
    request = client.recv(4096).decode()

    # Parse HTTP headers.
    header = request.split('\n')
    request_line = header[REQUEST_LINE_METHOD_INDEX].split()
    url = request_line[REQUEST_LINE_URL_INDEX]
    file_name = convert_to_file_name(url)
        
    cached = search_cache(file_name)

    if cached != None:
        print_client_info()
        print('Yeah! The requested file is in the cache and is about to be sent to client!')
        content = cached
    else:
        print_client_info()
        print('Oops! No cache hit! Requesting origin server for the file...')
        content = call_server(url, request_line)

    client.send(content.encode())
    print('All done! Closing socket...')
    client.close()
