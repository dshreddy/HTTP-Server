from tiny_flask.server import HTTPServer
from tiny_flask.request import Request
from tiny_flask.response import Response
import os

app = HTTPServer(port=4221) # Starts listening by default

@app.route('/')
def home(request: Request):
    return 'Welcome to the Tiny Flask server!'

@app.route('/echo/{string}')
def echo(request: Request, string):
    return string

@app.route('/user-agent')
def user_agent(request: Request):
    if "user-agent" in request.headers:
        return request.headers["user-agent"]
    else:
        response = Response(status_code=400, reason="Malformed Request")
        response.body = "The HTTP request sent is malformed and doen't contain user-agent header in it"
        return response

@app.route('files/{name}', methods=["GET"])
def send_file(request: Request, name: str):
    files_dir = "./tmp"
    file = os.path.join(files_dir, name)
    if os.path.isfile(file):
        data = ""
        with open(file, "rb") as f:
            data = f.read().decode()
        response = Response()
        # response.add_header("content-type", "application/octet-stream")
        response.body = data
        return response
    else:
        response = Response(status_code=500, reason="Not Found")
        response.body = "You're requesting for a file which does not exist on this server"
        return response

@app.route('files/{name}', methods=["POST"])
def send_file(request: Request, name: str):
    files_dir = "./tmp"
    file = os.path.join(files_dir, name)
    content = request.body
    with open(file, "wb") as f:
        f.write(content.encode())
    response = Response(status_code=201, reason="Created")
    response.body = "File created/overwritten successfully"
    return response