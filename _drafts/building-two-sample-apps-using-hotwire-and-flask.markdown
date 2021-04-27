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

## Project setup

The project uses python 3.8 and a *Pipenv* file is provided to ease the installation of dependencies. Just clone the repo, perform a <code>pipenv install</code> and you're all set.

Each example is located within its sub folder and is a complete separate Flask application. To run the server, activate the pipenv environment, <code>cd</code> to the folder and run the <code>flask run</code> command.

## Image loader with no Javascript

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
sequence = 0

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

## Recipe creator with auto-completion

In this example app, we'll be building an interactive recipe creator, where the user is allowed to select from a previously defined set of ingredients and add them to a list as they please. The ingredient selector is composed of an input field equipped with auto completion for a better user experience.

The search input field fetches ingredients from the server on the fly as you type. These ingredients are show bellow the field, and when the user clicks on one of them, the ingredient is added to the recipe on the right. If you click on the same ingredient more that once, the amount is added up to the list on the recipe.
The panel on the right shows the list of currently selected ingredients and have a small button allowing the user to remove each of them.

![A gif showing the autocomplete application working](/assets/img/hotwire-autocomplete.gif)

The HTML section of the code:

{% raw %}
``` html
<!-- index.html -->
<div class="flex-container">
  <div class="flex-item">
    <h2>Add ingredient</h2>

    <div data-controller="search"
        data-search-url-value="{{ url_for('search') }}?q=%s">
      <div>
        <input type="search" data-action="search#findResults" />
      </div>
      <div>
        <turbo-frame id="search-results" data-search-target="results">
        </turbo-frame>
      </div>
    </div>
  </div>

  <div class="flex-item">
    <h2>Recipe</h2>
    <ul>
      {% include '_recipe.html' %}
    </ul>
  </div>
</div>
```
{% endraw %}

The interesting part here is the use of a Stimulus controller to allow fetching the auto completion suggestion as the user types in an ingredient's name. The 
data attribute `data-controller="search"` on the outer div makes the binding to the Javascript object.
A callback method is set to be called when the user types something using `data-action="search#findResults"`.
A Turbo Frame was set to hold the search results and a *target* data attribute was placed to ensure access to it from the controller.

Now for the HTML partials:

{% raw %}
``` html
<!-- _search.html -->
<turbo-frame id="search-results">
  {% for ingredient in ingredients %}
    <div>
      <a href="{{ url_for('add', ingredient=ingredient.name) }}"
          data-turbo-frame="recipe">
        <strong>{{ ingredient.strong }}</strong>{{ ingredient.non_strong }}
      </a>
    </div>
  {% endfor %}
</turbo-frame>

<!-- _recipe.html -->
<turbo-frame id="recipe">
  {% for ingredient, amount in recipe.items() %}
    <li>
      {{ ingredient }} <span>{{ amount }}</span>
      <span>
        <a href="{{ url_for('exclude', ingredient=ingredient) }}">
          <button type="button" aria-label="Close">
            <span aria-hidden="true">&times;</span>
          </button>
        </a>
      </span>
    </li>
  {% endfor %}
</turbo-frame>
```
{% endraw %}

As we can see, the *search-results* frame is used to render the auto completion items. Each item is an anchor targeting a method for exclusion of ingredients on the server. A data attribute `data-turbo-frame="recipe"` is set to indicate that the Ajax response from this call should be rendered within the context of another frame, called `recipe`.

On the *recipe* frame, there's a list of currently selected ingredients, showing the placed amount of each them. A link for exclusion is also set to call the respective method on the server.

Let's proceed and see how the Stimulus controller was put together. Note that I used a slightly different syntax for the controller because it was written directly in the body of the HTML.

``` javascript
application.register("search", class extends Stimulus.Controller {
  static get targets() {
    return [ "results" ]
  }

  static get values() {
    return { url: String }
  }

  findResults(event) {
    const q = encodeURIComponent(event.target.value)
    const url = this.urlValue.replace(/%s/g, q)
    this.resultsTarget.src = this.urlValue.replace(/%s/g, q)
  }
})
```

This may seem confusing at first, but let's break it up. At the top of the class, the *targets* and *values* statements define the elements and attributes that we're interested in. The `results` element being the Turbo Frame used for displaying the search results, and the `url` value being a template string holding the URL along with the query string that the server expects.

When the user types a new character, the `findResults()` method is triggered. It uses the *url* value provided from the server along with the input string provided by the user in the field, to build a new *src* attribute for the Turbo Frame. Turbo will detect this change on the element and trigger an Ajax call to the server allowing the contents to be updated based upon the provided response.

In the server side code, just simple methods for rendering the HTML templates, and a dummy search method filtering on the list of ingredients available.

``` python
recipe = defaultdict(int)

@app.route("/")
def index():
    return render_template("index.html", recipe=recipe)

@app.route("/add/<ingredient>")
def add(ingredient):
    recipe[ingredient] += 1
    return render_template('_recipe.html', recipe=recipe)

@app.route("/exclude/<ingredient>")
def exclude(ingredient):
    del recipe[ingredient]
    return render_template('_recipe.html', recipe=recipe)

@app.route("/search")
def search():
    q = request.args.get("q")

    ingredients = [
        {
            "name": ingredient,
            "strong": ingredient[:len(q)],
            "non_strong": ingredient[len(q):],
        }
        for ingredient in INGREDIENTS
        if q and ingredient.lower().startswith(q.lower())
    ]

    return render_template('_search.html', ingredients=ingredients)
```

## Wrapping up

As we go through these examples, we can see how the design can be HTML centric when using Hotwire. Of course both examples were very simplistic cases of applications, but it's noticeable that a lot can be achieved by using just plain HTML and a few sprinkles of Javascript.

Building these apps helped me a lot to sink in the concepts, I hope reading about it was worth for you too. Project based learning is a quiet effective way of internalizing concepts, and writing about it helps even more.

Last but not least, I just wanted to mention that both application ideas were inspired by discussions I've read on the [Hotwire official forum][hotwire-forum]. It's a really nice place to discuss ideas regarding how to use this project.

[hotwire-first-look]: {% post_url 2021-04-10-a-first-look-at-hotwire %}
[stimulus]: {% post_url 2021-04-20-hotwire-and-stimulus-for-javascript-sprinkles %}
[flask]: https://flask.palletsprojects.com/
[examples-repo]: https://github.com/eduardovra/hotwire-flask-demo
[hotwire-forum]: https://discuss.hotwire.dev/
