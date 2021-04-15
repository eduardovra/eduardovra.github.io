---
layout: post
title:  Hotwire and Stimulus for Javascript sprinkles
#date:   2021-04-15 00:00:00 -0300
description: An overview on how to add behavior using Stimulus
img: stimulus2.png
tags: [Hotwire, Javascript]
---

Following up my [previous][hotwire-first-look] Hotwire article, now we're going to take a look at Stimulus: the component responsible for adding behavior to your pages without bloating them with Javascript.

### What it is ? Stimulus

Stimulus is a micro Javascript framework, intended to be used as a tool to add the little sprinkles every web app needs.

Key points:

* It's not supposed to be used for templates rendering: it's preferable to keep this task to the backend. So every time a new chunk of HTML is needed, it should be fetched from the server
* The binding between controllers and the HTML elements are set using declarative tags
* State is kept within the DOM, and not on Javascript objects
* Lifecycle hooks are provided to allow initialization of each controller instance
* Controllers are small, re-usable javascript components

Controllers are Javascript objects that are attached to HTML elements using tag annotations. Stimulus constantly monitors new elements on the page looking for a specific attribute to match for a corresponding controller.

### What can we do with it ? Controllers
* Respond to user interaction with action callbacks
* Read and write values to elements
* Access data attributes on elements to store state

### How it works ?
Show how to write a simple HTML and js file and bridge them together

Consider the following HTML snippet, taken from the official guidebook:

```html
<div data-controller="hello">
  <input data-hello-target="name" type="text">
  <button data-action="click->hello#greet">Greet</button>
</div>
```

Things to notice here:

* A data attribute _data-controller_ indicates Stimulus should create an instance of the default class in _hello_controller.js_ and bind it to the _\<div>_ element
* The _data-hello-target_ attribute tells that this element should be bound to the controller's scope, so we can access his value
* The _data-action_ attribute assigns the _greet()_ method as an action callback to be called when the _\<button>_ element gets clicked

Now the corresponding Stimulus controller:

```javascript
// src/controllers/hello_controller.js
import { Controller } from "stimulus"

export default class extends Controller {
  static targets = [ "name" ]

  greet() {
    const element = this.nameTarget
    const name = element.value
    console.log(`Hello, ${name}!`)
  }
}
```

What is happening:

* The _targets_ variable, denotes that Stimulus must for elements within the controller's scope, which have a data attribute _data-hello-target_ with a value of _"name"_. This element is going to be placed in a property called _nameTarget_
* When the button is clicked, the _greet()_ method is called and value of the input field is printed to the console


### Example code
Construct the simplest example possible, I was thinking about form validation

### Final thoughts
Conclude and comment on next steps



[hotwire-first-look]: {% post_url 2021-04-10-a-first-look-at-hotwire %}
