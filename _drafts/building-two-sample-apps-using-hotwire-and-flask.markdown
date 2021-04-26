---
layout: post
title:  Building two sample apps using Hotwire and Flask
#date:   2021-04-20 00:00:00 -0300
description: A walk through on building two sample applications using Hotwire and Flask
img: 1200px-Flask_logo.svg.png
tags: [Hotwire, Javascript, Python, Flask]
---

After covering up the basics on both [Turbo][hotwire-first-look] and [Stimulus][stimulus], we're good to go on building something using these tools. I've used Python's [Flask][flask] micro-framework on the server.

The first application is an image loader, where we're gonna see Turbo Drive, Frames and Streams all in action. No javascript was used in this example.
On the second app, we build an interactive tool for you to write a recipe, featuring a search field with autocompletion. In this example, we use a Stimulus controller and Turbo Drive and Turbo Frames to incrementally update the UI.

Bear in mind that the approach I've used is not necessarily the "best", as my focus was in demonstrating a couple use cases in the simplest way I could. These examples were conceived to be used for educational purposes only.

All the code is available in this [github repository][examples-repo].

### Project setup

The project uses python 3.8 and a *Pipenv* file is provided to ease the installation of dependencies. Just clone the repo, perform a <code>pipenv install</code> and you're all set.

Each example is located within its sub folder and is a complete separate Flask application. To run the server, activate the pipenv environment, <code>cd</code> to the folder and run the <code>flask run</code> command.

### Image loader with infinite scrolling

For the first example, I wanted to explore a simple case where Javascript is usually used for: dynamically pulling data from the server and appending to the DOM. This application is composed of a button to trigger the process of loading a new image and adding it to the UI. The number of images is displayed on the top of the screen and it's also kept within the server between page reloads.

![A gif showing the application working](/assets/img/hotwire-image-loader.gif)

```html
...

<turbo-frame id="images">
  {% for seq in range(0, counter) %}
    {% include '_image_loader.html' %}
  {% endfor %}
</turbo-frame>

<turbo-frame id="button">
  <form action="/add-image" method="post">
    <input type="submit" value="Load more" style="margin: 4px 2px;">
  </form>
</turbo-frame>
```

{% highlight html %}
<!-- _image_loader.html -->
<turbo-frame id="{{ seq }}" src="/get-image/{{ seq }}">
  <br />
  <img src="{{ url_for('static', filename='spinner.gif') }}" />
</turbo-frame>
{% endhighlight %}



### Recipe creator with auto-completion

### Wrapping up


[hotwire-first-look]: {% post_url 2021-04-10-a-first-look-at-hotwire %}
[stimulus]: {% post_url 2021-04-20-hotwire-and-stimulus-for-javascript-sprinkles %}
[flask]: https://flask.palletsprojects.com/
[examples-repo]: https://github.com/eduardovra/hotwire-flask-demo
