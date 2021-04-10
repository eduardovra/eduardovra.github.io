---
layout: post
title:  "A first look at Hotwire"
date:   2021-04-10 16:05:01 -0300
description: My first impressions of this new way of building web apps
img: hotwire.jpg
tags: [Hotwire, Javascript]
---

With the arrival of the new kid on the block for web development: Hotwire's project, I've been wondering how this new technology works and how can one possibly benefit from using it. Being something coming from [DHH][twitter-dhh] and the folks from [Basecamp][basecamp], who are famous for bringing up Ruby on Rails to the web dev scene, I thought it was a topic worth studying.

### The Hotwire's approach

The goal of the project is to provide a set of tools and practices, that allows building web applications that behave as SPAs, but writing as little Javascript code as possible. Such tools were initially developed by Basecamp, being the foundation for building their new email service: [Hey][hey]. Those tools were documented and later published as open source projects on [Github][hotwire-site].

Hotwire is divided into two parts: Turbo and Stimulus. Turbo is the component responsible for rendering, and Stimulus is used when additional behavior (Javascript sprinkles) is needed. For this post, I'll be focusing exclusively in Turbo's set of tools.

Key points:

* For simplicity, rendering should be done all in one place: exclusively in the backend
* To behave as an single-page application, the frontend should avoid re-constructing the entire page on each interaction. Instead, it should do only incremental chances as needed
* HTML is used as the primary data format for communication (instead of JSON), as browsers can handle this format really fast. That's where the "HTML over the wire" expression came from
* The same solution created for the web app, must also work for native mobile applications (Turbo Native). Rewriting the application once again in each mobile platform is not desirable; So it's imperative to provide a way of reusing functionality

### Turbo Drive and Turbo Frames

To use Hotwire, the first thing we need to do is to include the Javascript library provided by the project in the <head> tag. This library will perform all the heavy lifting of DOM manipulation for us. More information on how to do this can be found [here][turbo-installing].

The next thing would be to divide the HTML page into Turbo Frame segments. These segments are going to be rendered when the browser performs a full page load, but also when incremental changes to the state of the application occur.
This leads us to the first benefit of the technology: reuse of HTML templates.

A Turbo Frame is just an HTML tag with an ID attribute, that wraps a chunk of elements. It looks like this:

```html
<turbo-frame id="message_1">
  <h1>My message title</h1>
  <p>My message content</p>
  <a href="/messages/1/edit">Edit this message</a>
</turbo-frame>
```

The Turbo frames are scoped pieces of content. That means, when an action is carried out by the user within the frame, only this specific frame is going to be updated. This is accomplished by Turbo Drive, which intercepts form submissions and links clicked on the frame, preventing full page reloads. An Ajax request is performed instead, and the response containing a Turbo Frame with a matching ID will be rendered accordingly. Notice that all of this is achieved with no JS code written whatsoever, and very few changes to the backend. Nifty!

Another interesting feature is that Turbo Frames can be lazily loaded. This alone can speed up initial page loads, by avoiding fetching content not visible.
The caching of lazy-loaded frames can be more effective too, as it allows the separation of contents with a higher frequency of change from contents that rarely change within the page, thereafter maximizing the chances of a cache hit.

### Turbo Streams

Turbo Streams are a set of CRUD-like actions, provided to allow incremental changes to the DOM. The actions provided are limited to 5: **Append, Prepend, Replace, Update** and **Remove**.

These actions can be sent from the backend as a response of an Ajax call, or pushed to the frontend, when a persistent connection (like a websocket) is active. The format of the tags are like these:

```html
<turbo-stream action="append" target="messages">
  <template>
    <div id="message_1">
      This div will be appended to the element with the DOM ID "messages".
    </div>
  </template>
</turbo-stream>
```

By using Turbo Streams, it's possible to execute multiple actions in response to an event, so that, multiple parts of a page are updated reflecting the new state of the application.

The catch here really is: you still need to manage the UI state somewhere, but it now happens to be in the backend. So the complexity didn't vanish, it just changed places. And that's in line with the project's purpose: allow the application to be written in your favorite programming language, as much as possible.

### Framework integrations

The Hotwire set of tools are not designed to be used specifically with Ruby on Rails framework, although a reference implementation is provided.
Other frameworks have followed on the trail, and most of them already have at least an in-progress implementation.

Googling around was not too difficult to find some repositories:

* [https://github.com/hotwired/hotwire-rails][hotwire-rails]
* [https://github.com/tonysm/turbo-laravel][turbo-laravel]
* [https://github.com/hotwire-django/turbo-django][turbo-django]
* [https://github.com/deriegle/express-hotwire][express-hotwire]

### To sum up

It seems DHH and Basecamp are trying to change the web development paradigm once again, as the Ruby on Rails framework did before.
The Hotwire project is an attempt to bring simplicity back to the web development practice, resembling the golden years when Rails was first released.

If you want to build a web application writing the least Javascript possible, but still want to deliver a good user experience, Hotwire's Turbo seems to be a good way to go.

[twitter-dhh]: https://twitter.com/dhh/status/1341420143239450624?lang=en
[basecamp]: https://basecamp.com
[hey]: https://hey.com
[hotwire-site]: https://hotwire.dev
[turbo-installing]: https://turbo.hotwire.dev/handbook/installing
[hotwire-rails]: https://github.com/hotwired/hotwire-rails
[turbo-laravel]: https://github.com/tonysm/turbo-laravel
[turbo-django]: https://github.com/hotwire-django/turbo-django
[express-hotwire]: https://github.com/deriegle/express-hotwire
