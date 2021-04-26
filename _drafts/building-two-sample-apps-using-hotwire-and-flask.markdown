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

![A gif showing the image loader application working](/assets/img/hotwire-image-loader.gif)

The page is composed of a main HTML template and two partials as you'll see bellow. Styles were omitted for clarity.

{% raw %}
``` html
<!-- index.html -->
<h2>
  Images loaded: <turbo-frame id="counter">{{ counter }}</turbo-frame>
</h2>

<turbo-frame id="images">
  {% for seq in range(0, counter) %}
    {% include '_image_loader.html' %}
  {% endfor %}
</turbo-frame>

<turbo-frame id="button">
  <form action="/add-image" method="post">
    <input type="submit" value="Load more">
  </form>
</turbo-frame>

<!-- _image_loader.html -->
<turbo-frame id="{{ seq }}" src="/get-image/{{ seq }}">
  <img src="{{ url_for('static', filename='spinner.gif') }}" />
</turbo-frame>

<!-- _image.html -->
<turbo-frame id="{{ seq }}">
  <img src="https://picsum.photos/id/{{ seq }}/536/354" />
</turbo-frame>
```
{% endraw %}

The *index.html* file has 3 Turbo Frames:

* One containing the loaded images count. The use of the frame here will allow us to update this value dynamically from the server afterwards, using Turbo Streams.
* A placeholder frame for the images that are going to be referenced from the server when adding new images to the UI.
** The images frame includes the `_image_loader` partial. This segment demonstrates how we can place temporary content in a lazily loaded frame. A spinning gif in this case.
* And a frame for the form, which enables Turbo Drive on submission.

Now the python code for the server part.

``` python
@app.route("/", methods=["GET",])
def index():
    return render_template("index.html", counter=sequence)

@app.route("/add-image", methods=["POST",])
def add_image():
    sequence += 1
    html = render_template("_image_loader.html", seq=sequence)

    return turbo.stream([
        turbo.append(html, target="images"),
        turbo.update(sequence, target="counter"),
    ])

@app.route("/get-image/<seq>", methods=["GET",])
def get_image(seq):
    return render_template("_image.html", seq=seq)
```

This code is pretty straightforward, the root path providing the initial page load, and two additional methods for adding the images. When the user clicks on the *Load more* button, an Ajax request is performed to the */add-image* method. This method responds with a stream of two actions: one for appending the new image loader partial, and another one to update the incremented value of images loaded.

When the `_image-loader.html` partial is added to the DOM, Turbo immediately starts fetching the *src* of the frame, which will contain the actual image. Then it replaces its contents as soon as the response from the */get-image* method is received.

### Recipe creator with auto-completion

In this example app, we'll be building an interactive recipe creator, where the user is allowed to select from a previously defined list of ingredients and add them to a list as they please. The ingredient selector is composed of an input field equipped with auto completion for a better user experience.

There is a search input field which fetches ingredients from the server on the fly as you type. These ingredients are show bellow the field, and when the user clicks on one of them, the ingredient is added to the recipe on the left. If you click on some ingredient more that one, the amount is added up to the list on the recipe.
The panel on the left shows the list of currently selected ingredients and have a small button allowing the user to remove each of them.

![A gif showing the autocomplete application working](/assets/img/hotwire-autocomplete.gif)

### Wrapping up

What am I gonna say ?

[hotwire-first-look]: {% post_url 2021-04-10-a-first-look-at-hotwire %}
[stimulus]: {% post_url 2021-04-20-hotwire-and-stimulus-for-javascript-sprinkles %}
[flask]: https://flask.palletsprojects.com/
[examples-repo]: https://github.com/eduardovra/hotwire-flask-demo
