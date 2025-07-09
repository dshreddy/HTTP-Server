import gzip
import io

class Response:
    def __init__(self, version="HTTP/1.1", status_code="200", reason="OK"):
        self.http_version = version
        self.status_code = status_code
        self.reason = reason
        self.headers = {}
        self.compressed = False
        self.body = ""
    
    def add_header(self, key, value):
        self.headers[key] = value
    
    def gzip_compression(self, input):
        buf = io.BytesIO()
        with gzip.GzipFile(fileobj=buf, mode='wb') as f:
            f.write(input.encode())
        return buf.getvalue()
    
    def compress(self):
        self.compressed = True
        self.body = self.gzip_compression(self.body)
        self.add_header("Content-Encoding", "gzip")

    def get(self):
        # Status line
        response = f"{self.http_version} {self.status_code} {self.reason}"
        # CRLF that marks the end of the status line
        response += "\r\n"

        # Headers 
        # NOTE: Header names are case-insensitive.
        for key, value in self.headers.items():
            response += f"{key.lower()}: {value}"
            response += "\r\n"

        # CRLF that marks the end of the headers
        response += "\r\n"

        if self.compressed:
            # Response body is already compressed using gzip compression
            response = response.encode() + self.body
        else:
            # Response body
            response += self.body
            # Encode the response into bit stream
            response = response.encode()
        
        return response
