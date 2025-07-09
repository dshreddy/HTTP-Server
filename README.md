# TinyFlask 

A lightweight HTTP server **built from scratch** in Python with Flask-like routing, multithreading, dynamic URL parameters, gzip compression, and graceful shutdown.

## 🚀 Features

- ✅ **Flask-style Routing**: Define endpoints using `@app.route(path, methods=["GET"])`
    Usage Example
    
- 🧠 **Dynamic URL Parameters**: e.g. `/files/tmp/{filename}`
- 💬 **Custom Request & Response Objects** for clean endpoint code
- 🔥 **Multithreaded**: Each client is handled in a separate thread
- ⏳ **Idle Timeout**: Closes inactive client connections after 2 minutes
- 📦 **Gzip Compression** (if `Accept-Encoding: gzip` is sent)
- 🛑 **Graceful Shutdown**: Closes all sockets and threads by just pressing `q`
- 🖨️ **Thread-aware Logging**: Logs include thread name, log levels, and colors

## 🛠️ Usage

### 1. Install dependencies

No external dependencies required. Just Python 3.7+

### 2. Example Server

```python
from tiny_flask.server import HTTPServer
from tiny_flask.request import Request
from tiny_flask.response import Response

app = HTTPServer(port=4221)

@app.route("/", methods=["GET"])
def home(request: Request):
    return "Welcome to the Tiny Flask server!"

@app.route("/files/tmp/{filename}", methods=["GET"])
def file_reader(request: Request, filename: str):
    try:
        with open(f"./tmp/{filename}", "r") as f:
            return f.read()
    except FileNotFoundError:
        res = Response(status_code="404", reason="Not Found")
        res.body = f"File `{filename}` not found."
        return res
```

# Built with ❤️ 
