---
layout: post
title: "Writing a Python Web Server From Scratch - Part 1: HTTP"
date: 2021-06-28 00:00:00 -0300
description: This is the first part of a series of posts detailing how I built a Python Web Server supporting HTTP and WebSocket protocols from scratch.
img: HTTP_logo.png
tags: [python, asyncio, asgi, http, websocket]
---

In this series of posts, I'll discuss why and how I built a fully functional Web Server, supporting both HTTP and WebSocket protocols. This server has been written totally in Python, with no external dependencies, and it's only about 200 lines of code. It's meant to be used for running [ASGI][asgi] applications, so it's compatible with frameworks like [FastAPI][fastapi] and [Quart][quart].

TL;DR [Here][repository] is the repository with the complete implementation.

It's important to mention that a program that small was only possible due to the focus on simplicity it was given. If it were to be 100% compliant to the standards and also worrying about performance and security, this would be another story.

Having taken this out of the way, if you're interested in knowing what's happening under the surface when writing your web apps, this article is for you.

But first, let's take a walk on the philosophical side, and reflect on why this kind of project can be a good idea.

### What's the point of reinventing the wheel ?

Most people underestimate the importance of practicing and reading good code to enhance your skills as a developer. But the reality is, being developers, we have access to thousands of open-source projects, and they are good opportunities to discover very clever ways of using programming languages to solve real problems. Nevertheless, randomly sweeping GitHub repositories to read code is not something that ever worked for me, hence, the idea of creating an application was something that helped me focus the research efforts.

Personally, I find it more productive to focus on more recent codebases, for example, [Starlette][starlette]. If you dig into it, you'll find cool ideas. Besides, its code is not so difficult to read, compared with older projects like [Flask][flask], which carry the burden of maintaining compatibility and supporting multiple versions of Python over time.

My interest here was to get a more in-depth understanding of web protocols, particularly WebSockets, and also to see how Async programming is being used in the real world. This project was never a commitment to creating some production-ready server, but instead, something that I did to carve knowledge, practice programming and have fun. That said, I think not every code your write must be a piece of art, and you shouldn't be afraid of creating something humble that just serves the sole purpose of getting better. Sometimes your attention should be more focused on the process and less on the outcome.

But for the record, I totally agree that it's usually not a good idea to reinvent the wheel in your job.

### Defining goals

For this project, I didn't want to set strict rules or milestones. Instead, the basic goal was to build something that worked, drawing inspiration from other projects. The approach was basically to get an MVP of the server, then iterate again, and again, adding more features each time. And I intended to keep this process as long as I was still getting value out of it. I got the ball rolling by defining the base case that the server should be able to handle.

Consider the following application:

```python
import uvicorn
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

That was the simplest thing I could come up with in terms of functionality to support. Here, if we're to mock [uvicorn's][uvicorn] behavior, all we need to implement is a HTTP GET request/response cycle. Of course, the server will need an ASGI interface to communicate with the application as well. All thing considered, the job was basically creating a Python application that converts HTTP protocol messages to the ASGI interface, and vice-versa.

Let's begin by having a look on how HTTP works.

### The HTTP protocol

Luckily, [HTTP][] is a text based protocol, and it's fairly easy to parse. The basic format of the *Request* message is this:

```
GET / HTTP/1.1\r\n
Accept-Language: en-US,en;q=0.9,pt-BR;q=0.8,pt;q=0.7\r\n
User-Agent: Mozilla/5.0 Chrome/91.0.4472.114 Safari/537.36\r\n
\r\n
```

It's composed of a series of lines, each of them terminated by a `\r\n` char sequence. The first line is called the *Request Line*. It contains the method, path and HTTP version used, and it's often seen in apache's *access_log* file. This is then followed by a list of headers, defined as key-value pairs separated by colons. The list is terminated by a blank line (also containing a `\r\n`). After the headers, an additional body portion may exists, depending on the kind of request (a Form POST for instance).

The layout of the *Response* is rather similar:

```
HTTP/1.1 200 OK\r\n
Content-Type: text/html; charset=UTF-8\r\n
Content-Length: 38\r\n
\r\n
<html><body>Hello World!</body></html>
```

The only difference would be the *Request Line* being replaced by a *Status Line*, that contains the status code for the response.

Now let's see about the other end of the server: how to communicate with the application.

### The ASGI standard

The ASGI (Asynchronous Server Gateway Interface) standard establishes an interface for the server and application to communicate (by application I mean the Web Framework along with your code, considering the server sees it as only one thing).

An ASGI server is required to create the event loop and launch the application each time a connection is established. In terms of format, it expects the app to be a Callable that adheres to the following signature:

```python
# Implemented using a function...
async def app(scope, receive, send):
    ...

# ...or using a class
class FastAPI:
    async def __call__(self, scope, receive, send):
        ...
```

Let's break down these parameters.

#### Scope

This is a dictionary containing details about the connection. For HTTP it will be like this:

```python
{
    "type": "http":,
    "asgi" : {"version": "3.0"},
    "http_version": "1.1",
    "method": "GET",
    "scheme": "https",
    "path": "/",
    "query_string": b"q=search",
    "headers": [
        [b"accept-language", b"en-US,en;q=0.9,pt-BR;q=0.8,pt;q=0.7"],
    ],
    # ...
}
```

Notice that some fields are presented as *unicode strings* (like `"method"`), and others are presented as *binary strings* (like `"query_string"`).

#### Receive

This is a callback *coroutine* provided by the server to enable the application to receive events from the connection. The *coroutine* has no parameters and must return a dictionary with details about the event.

For HTTP connections, there's only one event type that can be returned: `"http.request"`. It contains the payload of the request, and can be split among several parts. That means, the app might have to call `receive()` multiple times until an event with the `"more_body"` flag is received as `False`.

#### Send

It's a callback *coroutine* as well, but it's intended to be called by the application when it needs to send some data. This *coroutine* expects a dictionary to be provided as a parameter, containing details about the event being sent.

The send *coroutine* has two event types:

* `"http.response.start"` used by the app to send the response headers
* `"http.response.body"` used by the app to send the body of the response. This event can be sent multiple times for chunked payloads, the same way as the event present on `receive()`

### The Request-Response cycle in ASGI

The HTTP protocol operates on a basic Request-Response cycle. This means, the connection is always initiated by the client, and the server can only send data back once it's requested.

The basic outline of a connection cycle happens like this:

1. The client (a Browser, usually), connects to the server, which promptly accepts it
2. The client pushes the request data to the server
  * Once we get the headers in the server, we're ready to build the connection scope and invoke the application
  * At this point, the application can call the `receive()` function to get the body of the request (if any)
3. App calls `send()` function to send the response headers
  * The server saves the data but don't pushes it yet
4. The app call the `send()` function once again to push the response body data. At this point, the server formats the HTTP response headers and pushes them through the socket along with the body
5. When all the response data is sent, the server closes the connection
6. At last, the application finishes its execution, and the control flow is returned to the server

For now, you may find the ASGI interface separation of receive and send methods seeming to be overkill. But it was intentionally designed this way, and it will make much more sense when we're implementing the WebSocket protocol.

Ok, so if you're a programmer and have reached this point without seeing any code, your eyes must be bleeding by now. Then let's get to it (finally).

### Show me the code

The idea here is to create a Python module that can replace the *uvicorn's* import statement, keeping the same behavior while serving the sample app.

For now, we're only intending to support the HTTP protocol, therefore the MVP could be something like this:

```python
import asyncio

async def handler(app, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    response_headers = []
    scope = await build_scope(reader)

    async def receive():
        # App's pulling the body of the request
        content_length = get_content_length(scope)
        return {
            "type": "http.request",
            "body": await reader.read(content_length),
            "more_body": False,
        }

    async def send(event):
        nonlocal response_headers

        # App's sending the response headers
        if event["type"] == "http.response.start":
            response_headers = build_http_headers(scope, event)
        # App's sending the response body
        elif event["type"] == "http.response.body":
            # The headers should only be pushed once the body is received
            if response_headers:
                writer.writelines(response_headers)
                response_headers = []

            writer.write(event["body"])
            await writer.drain()

            if event.get("more_body", False) is False:
                # Close connection
                writer.close()
                await writer.wait_closed()

    # Invoke the app!
    await app(scope, receive, send)

async def run_server(app, host, port):
    async def wrapped_handler(reader, writer):
        return await handler(app, reader, writer)

    server = await asyncio.start_server(wrapped_handler, host, port)
    async with server:
        await server.serve_forever()

def run(app, host, port):
    print(f"Listening on http://{host}:{port}")
    asyncio.run(run_server(app, host, port))
```

Some functions were omitted for brevity, but as you can see, the implementation is quite small and easy to follow through. We leverage the `asyncio.start_server()` function to spawn a TCP server on the host and port selected by the user. Whenever a client connects to the server, the `handler()` *coroutine* is going to be called, and we use the `reader` and `writer` objects to interact with the underlying socket. It works pretty much as file IO.

An interesting factor is the usage of *inner functions* (also called *closures*). They inherit the context variables present in the parent function and therefore can hold state in-between calls. Sometimes make sense to use *inner functions* as an alternative to full-blown classes and objects.

Besides these details, the rest of the code is basically just about handling dictionaries and string manipulation.

#### Parsing HTTP headers

These are the routines responsible for parsing the HTTP protocol headers and create the `scope` dictionary that is going to be provided for the app. I used the built-in module `urllib` to parse the URL and separate the path from the query_string.

```python
from urllib.parse import urlparse

async def build_scope_headers(reader):
    headers = []

    while True:
        header_line = await reader.readuntil(b"\r\n")
        header = header_line.rstrip()
        if not header:
            break
        key, value = header.split(b": ", 1)
        headers.append([key.lower(), value])

    return headers


async def build_scope(reader):
    request_line = await reader.readuntil(b"\r\n")
    request = request_line.decode().rstrip()
    method, path, protocol = request.split(" ", 3)
    url = urlparse(path)
    __, http_version = protocol.split("/")
    headers = await build_scope_headers(reader)

    return {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": http_version,
        "method": method,
        "scheme": "http",
        "path": url.path,
        "query_string": url.query.encode(),
        "headers": headers,
    }
```

#### Formating the HTTP response headers

This function will receive the response status code and headers and format an HTTP response message to be sent back.

```python
def build_http_headers(scope, event):
    http_version = scope["http_version"]
    status = HTTPStatus(event["status"])
    status_line = f"HTTP/{http_version} {status.value} {status.phrase}\r\n"

    headers = [status_line.encode()]
    for header_line in event.get("headers", []):
        headers.append(b": ".join(header_line))
        headers.append(b"\r\n")
    headers.append(b"\r\n")

    return headers
```

### Wrapping-up and next steps

In this post, I tried to cover the basic motivation why I think it's a good idea to undertake a personal project and how this helps to guide your open-source codebases exploration. On the technical side, I introduced the HTTP protocol and the ASGI interface. In the end, we got a single-threaded server capable of handling concurrent HTTP connections using asynchronous programming.

If you liked the article, you should try running the sample app using this server to see it in action. Just drop the Python script in your project's folder and you're good to go (the server has no external dependencies). Any Python version >= 3.7 should work. Tinker with the code and try to improve it, it won't be hard :D

In the next post, I'll go over the details of implementing the WebSocket protocol. Things will get more interesting, as we're going to deal with persistent connections, state, and a lot more event types. That's when Async programming starts to shine.

[repository]: https://github.com/eduardovra/simple-asgi-webserver
[asgi]: https://asgi.readthedocs.io/en/latest/index.html
[fastapi]: https://github.com/tiangolo/fastapi
[quart]: https://github.com/pgjones/quart
[starlette]: https://github.com/encode/starlette
[flask]: https://github.com/pallets/flask
[uvicorn]: https://github.com/encode/uvicorn
[http]: https://developer.mozilla.org/en-US/docs/Web/HTTP
