GET = "GET"
POST = "POST"
PUT = "PUT"
DELETE = "DELETE"

class Request:
    def __init__(self, method: str, target: str, version: str, body: str = "") -> None:
        self.method = method # HTTP method
        self.target = target # Request target
        self.http_version = version # HTTP version
        self.headers = {}
        self.body = body
    
    def add_header(self, key, value):
        self.headers[key] = value

    def get(self):
        # Status line
        request = f"{self.method} {self.target} {self.http_version}"
        # CRLF that marks the end of the status line
        request += "\r\n"

        # Headers 
        # NOTE: Header names are case-insensitive.
        for key, value in self.headers.items():
            request += f"{key.lower()}: {value}" 
            request += "\r\n"

        # CRLF that marks the end of the headers
        request += "\r\n"

        # Request body
        request += self.body

        # Encode the request into bit stream
        request = request.encode()
        return request
