import socket
import time
import os
import logging
from concurrent.futures import ThreadPoolExecutor

#Note: DO NOT CALL BY LOCALHOST

# Configurations
HOST = '0.0.0.0'
PORT = 80
# Get the directory where the script (server.py) is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Join that directory with your folder name
WEB_FILE = os.path.join(BASE_DIR, "web_file")
LOG_FILE = os.path.join(BASE_DIR, "server_log.txt")

# Logging format
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(message)s' # Custom format
)

# Special error class for effecient handling
class HTTPError(Exception):
    def __init__(self, status_code, message):
        self.status_code = status_code
        self.message = message

class request:
    def __init__(self, raw_line):
        self.raw_line = raw_line
        self.type = "keep-alive" # Default for HTTP/1.1
        self.if_modified_since = None
        self.content = b""
        self.content_length = 0
        self.last_modified = None
        self.status = "200 OK"
        self.content_type = ""
        self.protocol = "HTTP/1.1"
        self.method = ""
        self.path = ""

        self.lines = self.raw_line.split("\r\n")
        request_line = self.lines[0].split()
        if len(request_line) == 3: # Check if request consist of three parts
            self.method = request_line[0]
            self.path = request_line[1]
            self.protocol = request_line[2]
        else:
            self.status = "114514 NOT OKAY" # Using the status as a switch by assigning an impossible status
            return
        if self.path == "/": # Special case for empty request
            self.status = "228922 NO SOUL" # Using the status as a switch by assigning an impossible status
            return

        # Process connection type: Stay-alive or Close
        if "HTTP/1.0" in self.protocol:
            self.type = "close" # Default for HTTP/1.0

        #for testing
        #print("if mod:", self.if_modified_since,"\n")
        #print("last mod:",self.last_modified,"\n")
        #print("Stat:",self.status,"\n")
        #print("Type:",self.type,"\n")
        #print("Method:",self.method,"\n")
        #print("Path:",self.path,"\n")
        #print("Protocal:",self.protocol,"\n")

    
    def process(self):
        try:        
            if self.status == "228922 NO SOUL":
                raise HTTPError("400 Bad Request", "Empty request")
            if self.status == "114514 NOT OKAY":  
                raise HTTPError("400 Bad Request", "Bad format")
            if self.method not in ["GET", "HEAD"]: # Check if request is GET or HEAD
                raise HTTPError("400 Bad Request", f"Method {self.method} not supported")
            if ".." in self.path: # Check if there's directry traversal attempting to leave current folder
                raise HTTPError("403 Forbidden", "Directory traversal not allowed")
            filename = os.path.join(WEB_FILE, os.path.normpath(self.path.removeprefix("/")))
            print("Filename:", filename, "\n")
            if filename == "" or not os.path.exists(filename): # Check if file exists
                raise HTTPError("404 Not Found", "File does not exist")
            if not os.access(filename, os.R_OK):
                raise HTTPError("403 Forbidden", "Access denied")

            # If all checks pass, begin reading

            # Calculating current time
            mtime = os.path.getmtime(filename)
            self.last_modified = time.strftime('%a, %d %b %Y %H:%M:%S GMT', time.gmtime(mtime))

            # Checking if request has If-Modified-Since:      
            for line in self.lines:
                if line.startswith("If-Modified-Since:"):
                    self.if_modified_since = line.split(": ", 1)[1].strip()
                    if self.if_modified_since == self.last_modified: # Check if file has not been modified since
                        raise HTTPError("304 Not Modified", self.last_modified)

            # A simple list of file type
            ext = os.path.splitext(filename)[1].lower() # gets ".jpg"
            mapping = {
                ".html": "text/html",
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".png": "image/png",
                ".txt": "text/plain",
                ".css": "text/css"
            }
            self.content_type = mapping.get(ext, "application/octet-stream")

            # Read the file
            with open(filename, "rb") as f:
                full_content = f.read()
                self.content_length = len(full_content)
                f.close

                if self.method == "HEAD":
                    self.content = b"" # Clear the body for HEAD
                else:
                    self.content = full_content # Keep the body for GET

        # Centralised error handling
        except HTTPError as e:
            self.status = e.status_code
            self.content = f"<h1>{e.status_code}</h1><p>{e.message}</p>".encode('utf-8')
            self.content_type = "text/html"
            if self.method == "HEAD":
                self.content = b""
            self.content_length = len(self.content)

        except Exception as e:
            # Catch-all for unexpected crashes (500 error) (for testing only)
            self.status = "500 Internal Server Error"
            self.content = b"Internal Server Error"
            self.content_type = "text/html"
            if self.method == "HEAD":
                self.content = b""
            self.content_length = len(self.content)

    def log_request(self, client_addr):
        # Getting information
        access_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        filename = self.path if self.path else "UNKNOWN"
        response_status = self.status
        # Construct the log line
        log_entry = f"{client_addr} | {access_time} | {filename} | {response_status}"
        
        # Write to file
        logging.info(log_entry)
        print(f"Logged: {log_entry}\n") 

    # Construct the reply    
    def get_http_bytes(self,client_addr):
        header = f"{self.protocol} {self.status}\r\n"
        header += f"Content-Length: {self.content_length}\r\n"
        header += f"Content-Type: {self.content_type}\r\n" 
        if self.last_modified:
            header += f"Last-Modified: {self.last_modified}\r\n"
        header += f"Connection: {self.type}\r\n"
        header += "\r\n"
        
        print(f"Sending Response to {client_addr}: {self.status} | Size: {self.content_length} bytes\n")
        return header.encode('utf-8') + self.content

def client_handler(client_socket, client_addr):
    client_socket.settimeout(60) # Timeout set to 10 minute

    try:
        while True: # Infinite loop for Keep-Alive
            try:
                data = client_socket.recv(4096).decode('utf-8') # Waiting to receive data
                print(f"Data received from {client_addr}\n")
            except (socket.timeout, ConnectionResetError):
                print(f"Client {client_addr} timed out, connection ended.\n")
                break # Disconnetion due to timeout or browser closing
            if not data: 
                print(f"Client {client_addr} closed the connection.\n")
                break # Client closed connection
            message = request(data) # Formatting request
            message.process() # Processing request
            message.log_request(client_addr) # logging request
            client_socket.sendall(message.get_http_bytes(client_addr)) # Sending reply
            if message.type == "close": # End connection if it's HTTP/1.0
                break
    finally:
        client_socket.close()


def server_main():
    # Ensure the folder exists
    if not os.path.exists(WEB_FILE):
        os.makedirs(WEB_FILE)
        print("WARNING: Web file storage not detected! New folder created.\n")
    print("web file storage ready.\n")

    # Create socket using IPV4, TCP 
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Make sure the port is avaliable immediately after closing the server for quicker testing
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # Binding the address
    server.bind((HOST, PORT))
    # Begin listening
    server.listen(30)
    print(f"Server started. IP:{HOST}, PORT:{PORT}\n")

    # Using ThreadPoolExecutor for ad-hoc threading, limit set to 50 due to limitations of project
    with ThreadPoolExecutor(max_workers=50) as executor:
        while True:
            client_sock, addr = server.accept()
            print(f"Accepted connection from {addr}\n")
            executor.submit(client_handler, client_sock, addr)

#failsafe to prevent accidental execution during threading
if __name__ == "__main__":
    server_main()