---
layout: post
title:  "Hotwire and Stimulus for Javascript sprinkles"
date:   2021-04-15 00:00:00 -0300
description: An overview on how to add behavior using Stimulus
img: stimulus2.png
tags: [Hotwire, Javascript]
---

Following up my [previous][hotwire-first-look] Hotwire article, now we're going to take a look at Stimulus: the component responsible for adding behavior to your pages without bloating them with Javascript.

### Purpose

Stimulus is a micro Javascript framework, intended to be used as a tool to add the little sprinkles every web app needs. The way it does that 

Key points:

* It's not supposed to be used for templates rendering: it's preferable to keep this task to the backend. So every time a new chunk of HTML is needed, it should be fetched from the server
* The binding between controllers and the HTML elements are set using declarative tags
* State is kept within the DOM, and not on Javascript objects
* Lifecycle hooks are provided to ease the process of initialization of each controller
* Controllers are small, re-usable javascript components

### Controllers

Controllers are used to separate contents from behavior, the same way CSS separates contents from presentation.



[hotwire-first-look]: {% post_url 2021-04-10-a-first-look-at-hotwire %}
