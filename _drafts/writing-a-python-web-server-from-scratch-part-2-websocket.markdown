---
layout: post
title: "Writing a Python Web Server From Scratch - Part 2: WebSocket"
#date: 2021-06-28 00:00:00 -0300
description: This is the second part of a series of posts detailing how I built a Python Web Server supporting HTTP and WebSocket protocols from scratch.
img: websocket.png
tags: [python, asyncio, asgi, http, websocket]
---

Following the first [Post][first-post] on the "Writing My Own Web Server" series, now we're going to find out more about the WebSocket protocol.

It allows applications to establish a persistent full-duplex connection between server and client, and this enables a series a interesting possibilities.

### WebSocket use cases

Any web application that needs some kind of real-time interactivity can benefit from the use of WebSockets. Bellow there's a list with some areas:

* Chatting
* Online games
* Financial applications
* Social feeds (for news, tweets, etc)
* Collaborative editing of documents

As of today, all modern browsers support the WebSocket protocol.

### How the protocol works

The process of connection starts with the handshaking phase.

#### Handshake

After connecting to the server, the client sends a regular HTTP GET request with some special headers to denote its intention of upgrading the connection to the WebSocket mode.

```
GET /chat HTTP/1.1
Upgrade: websocket
Connection: Upgrade
Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==
Sec-WebSocket-Version: 13
```

At this point, the server might either accept or refuse the upgrade attempt. In order to accept, it must return a response with the following format:

```
HTTP/1.1 101 Switching Protocols
Upgrade: websocket
Connection: Upgrade
Sec-WebSocket-Accept: s3pPLMBiTxaQ9kYGzzhZRbK+xOo=
```

#### Frame format

Once the handshake is done, the communication starts using a standard binary frame format to exchange messages:

```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-------+-+-------------+-------------------------------+
|F|R|R|R| opcode|M| Payload len |    Extended payload length    |
|I|S|S|S|  (4)  |A|     (7)     |             (16/64)           |
|N|V|V|V|       |S|             |   (if payload len==126/127)   |
| |1|2|3|       |K|             |                               |
+-+-+-+-+-------+-+-------------+ - - - - - - - - - - - - - - - +
|     Extended payload length continued, if payload len == 127  |
+ - - - - - - - - - - - - - - - +-------------------------------+
|                               |Masking-key, if MASK set to 1  |
+-------------------------------+-------------------------------+
| Masking-key (continued)       |          Payload Data         |
+-------------------------------- - - - - - - - - - - - - - - - +
:                     Payload Data continued ...                :
+ - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - +
|                     Payload Data continued ...                |
+---------------------------------------------------------------+
```

Talk about flags FIN and MASK. Masking key and payload length.

Let's start by worrying about the `opcode` field only. It defines what kind of payload this frame carries. The most essential values are:

* **0x1**: Payload contains UTF-8 encoded text
* **0x2**: Payload contains a binary string (a bytes array)
* **0x8**: A control frame for connection close. Payload may contain the close status code

### The ASGI standard for WebSocket connections

#### Scope format

```python
{
    "type": "websocket",
    "asgi": {"version": "3.0"},
    "http_version": "1.1",
    "scheme": "ws", # wss when using encrypted connection
    "path": "/ws",
    "query_string": b"q=search",
    "headers": [
        [b"accept-language", b"en-US,en;q=0.9,pt-BR;q=0.8,pt;q=0.7"],
    ],
}
```

#### Event types sent by the server

* `"websocket.connect"`: A client is attempting to establish a connection
* `"websocket.receive"`: The client sent a data frame
* `"websocket.disconnect"`: The client is closing the connection

#### Event types sent by the application

* `"websocket.accept"`: The application accepted the connection
* `"websocket.send"`: The application is sending data
* `"websocket.close"`: The application is closing the connection

### Extending the server to handle WebSockets

Explain the code

### To conclude

Next steps ??

### References

* [Awesome guide from Mozilla explainting how to implement the protocol](https://developer.mozilla.org/en-US/docs/Web/API/WebSockets_API/Writing_WebSocket_servers)
* [RFC for the The WebSocket Protocol](https://datatracker.ietf.org/doc/html/rfc6455)
* [ASGI Version 3.0](https://github.com/django/asgiref/tree/3.0)

[first-post]: {% post_url 2021-06-28-writing-a-python-web-server-from-scratch-part-1-http %}
