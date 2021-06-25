---
layout: post
title: "Writing a Python Web Server From Scratch - Part 1: HTTP"
#date:   2021-04-20 00:00:00 -0300
description: Building a Python Web Server supporting HTTP and WebSocket protocols
img: HTTP_logo.png
tags: [Python, ASGI, HTTP, WebSockets]
---

In this series of posts, I'll discuss why and how I built a fully functional Web Server, supporting both HTTP and WebSocket protocols. This server has been written totally in Python, with no external dependencies, and it's only about 200 lines of code. It's meant to be used for running ASGI applications, so it's compatible with frameworks like FastAPI and Quart.

It's important to mention that a program that small was only possible due to the focus in simplicity it was given. If it were to be 100% compliant to the standards, and also worrying about performance and security, this would be another story.

Having taken this out of the way, if you're interested in knowing what's happening under the surface when writing your web apps, this article is for you.

### What's the point of reinventing the wheel ?

The first question you may be asking yourself is "Why should I do this in the first place? There's a ton of servers freely available to use already..". It's a fair question, and you're probably right avoiding to reinvent the wheel in your job. But my point here was to build it for the sake of learning. This project was never a commitment to create some production ready server, but instead, something that I did to carve knowledge and practice programming. My interest was to get a more in-depth understanding of web protocols, particularly WebSockets, and also to see how Async programming is being used in the real world.

Most people underestimate the importance of practicing and reading good code to enhance your skills as a developer. But the reality is that all those open source projects are opportunities to discover very clever ways to use the language and solve real problems. What writer can possibly have created good books without reading a lot and getting references first?

For me personally, I find it more productive to focus on more recent codebases, for example Starlette. If you look into it, you'll find good ideas, and its code is not so difficult to read, comparing with older projects like Flask, that carry the burden of maintaining compatibility and supporting multiple version of Python over time.

### Defining goals

For this project, I didn't wanted to set strict rules or milestones. Instead, the basic goal was to build something that worked, getting inspiration from others projects. The approach was basically to get a MVP of the server, then iterate again and again, adding more features each time. And I intended to keep this process as long as I'm still getting value out of it. I got the ball rolling by defining the base case that the server should be able to handle.

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

That was the simplest thing I could come up with in terms of functionality to support. Hence, if we're to mock uvicorn's behavior, all we need to implement here is a HTTP GET request/response cycle. The application will need an ASGI interface to communicate with the server as well. All thing considered, the job was basically creating a Python application that converts HTTP protocol messages to the ASGI interface, and vice-versa.

Let's begin by having a look on how HTTP works.

### The HTTP protocol

Luckily, HTTP is a text based protocol, and it's fairly easy to parse. The basic format of the *Request* message is this:

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

An ASGI server is required to create the event loop and launch the application each time a connection is established. In terms of format, it expects the app to be a callable that adheres to the following signature:

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

This is a *coroutine* provided by the server to enable the application to receive events from the connection. The *courotine* has no parameters and must return a dictionary with details about the event.

#### Send

It's a *courotine* as well, but it's intended to be called by the application when it needs to send some data. This *courotine* expects a dictionary to be provided as a parameter, containing details about the event being sent.

### The Request-Response cycle

The HTTP protocol operates on a basic Request-Response cycle. This means, the connection is always initiated by the client, and the server can only send data back once it's requested.

The basic outline of a connection cycle happens like this:

* The client (browser, usually), connects to the server, which promptly accepts it
* The client pushed the request data to the server
  * Once we get the headers in the server, we're ready to build the connection scope and invoke the application
  * At this point, the application can call the receive function to get body of the request (if applicable)
* App calls the send function to send the response headers. The server then formats the HTTP response headers and pushes it through the socket
  * Optionally the app can call the send method once again to push the response body data (if applicable)
* Finally, the application finishes its execution, and the control flow is returned to the server, which closes the connection

For now, you may find the ASGI interface separation of receive and send methods seem to be overkill. But it was intentionally designed this way, and it will make much more sense when we're implementing the WebSocket protocol.

### Show me the code

Ok, so if you're a programmer and have reached this point without seeing any code, your eyes must be bleeding by now. Then let's get to it (finally).

The idea here is to create a Python module that can replace the *uvicorn's* import statement while keeping the same behavior within the sample app.

For now we're only intending to support the HTTP protocol, therefore the MVP could be something like this:

```python
import asyncio

async def handler(app, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    scope = build_scope(reader)

    async def receive():
        # App's pulling the body of the request
        content_length = get_content_length(scope)
        return {
            "type": "http.request",
            "body": await reader.read(content_length),
            "more_body": False,
        }

    async def send(event):
        # App's sending the response headers
        if event["type"] == "http.response.start":
            headers = build_http_headers(event)
            writer.writelines(headers)
            await writer.drain()
        # App's sending the response body
        elif event["type"] == "http.response.body":
            writer.writelines([event["body"], b"\r\n"])
            await writer.drain()

    # Invoke the app!
    await app(scope, receive, send)
    # Close connection
    writer.close()
    await writer.wait_closed()

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

Some functions were omitted for brevity, but as you can see, the implementation is quiet small and easy to follow through. We leverage `asyncio.start_server` function to spawn a TCP server on the host and port selected by the user. 

Try running a sample app using this server to see it in action. Just drop the Python script in your project's folder and you're good to go (the server has no external dependencies). Any Python version >= 3.7 should work.

### Next step: WebSocket support

In the next post, I'll go over the details of implementing the WebSocket protocol. Things will get more interesting, as we're going to have to deal with persistent connections, state and a lot more events types. That's when Async programming start to shine.
