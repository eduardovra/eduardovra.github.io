---
layout: post
title:  Hotwire and Stimulus for Javascript sprinkles
#date:   2021-04-15 00:00:00 -0300
description: An overview on how to add behavior using Stimulus
img: stimulus.png
tags: [Hotwire, Javascript]
---

Following up my on [previous][hotwire-first-look] Hotwire article, now we're going to take a look at Stimulus: the component responsible for adding behavior to your pages without bloating them with Javascript.

### Stimulus controllers

Stimulus is a Javascript framework, intended to be used as a tool to add the little sprinkles every web app needs.

The building blocks of a Stimulus application are the _controllers_. Controllers are Javascript objects that are connected to HTML elements using tag annotations. Stimulus constantly monitors new elements on the page looking for a specific attribute to match for a corresponding controller. When it finds one, an instance of the controller is created and then connected to the element on the DOM.

As you'll see, Stimulus follows the _Convention over Configuration_ practice. This alone can help to reduce the amount of boilerplate code one needs to write. Most naming conventions will be self-explanatory, once we go through the examples.

Controllers allow us to:

* Respond to user interaction with action callbacks
* Read, write and monitor elements
* Access data attributes on elements to store values, keeping state in the DOM

Other highlights:

* Controllers are small, re-usable javascript components
* They are not supposed to be used for templates rendering: it's preferable to keep this task to the backend. So every time a new chunk of HTML is needed, it should be fetched from the server
* The binding between controllers and the HTML elements are set using declarative tags
* The state is kept within the DOM, and not on Javascript objects
* Lifecycle hooks are provided to allow initialization of each controller instance

### Show me the code

I'm a big fan of learning by examples, so let's jump right into the code. Consider the following HTML snippet, taken from the official guidebook:

```html
<div data-controller="hello">
  <input data-hello-target="name" type="text">
  <button data-action="click->hello#greet">Greet</button>
</div>
```

Things to notice here:

* A data attribute _data-controller_ indicates Stimulus should create an instance of the default class in _hello_controller.js_ and bind it to the _\<div>_ element
* The _data-hello-target_ attribute tells that this element should be bound to the controller's scope so that we can access his value later
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

* The _targets_ property declares that Stimulus must look for elements within the controller's scope, which have a data attribute _data-hello-target_ with a value of _"name"_. This element is going to be placed in a property called _nameTarget_
* When the button is clicked, the _greet()_ method is called and value of the input field is printed to the console

### Another example: slide-show

Consider another example extracted from the official guidebook, a slide-show application:

```html
<div data-controller="slideshow" data-slideshow-index-value="1">
  <button data-action="slideshow#previous"> ← </button>
  <button data-action="slideshow#next"> → </button>

  <div data-slideshow-target="slide">🐵</div>
  <div data-slideshow-target="slide">🙈</div>
  <div data-slideshow-target="slide">🙉</div>
  <div data-slideshow-target="slide">🙊</div>
</div>
```

The first difference you'll notice here is the presence of a new data attribute on the root _\<div>_: _data-slideshow-index-value_. It's used to keep the index of the currently selected slide. More on this later.

We also have a whole bunch of HTML with all slides already in place. But if you're working with Turbo, these slides could also be lazily loaded Turbo Frames. Notice that the target value _"slide"_ is used in multiple elements. No "IDs" are needed in any of the _divs_.

The corresponding controller:

```javascript
import { Controller } from "stimulus"

export default class extends Controller {
  static targets = [ "slide" ]
  static values = { index: Number }

  next() {
    this.indexValue++
  }

  previous() {
    this.indexValue--
  }

  indexValueChanged() {
    this.showCurrentSlide()
  }

  showCurrentSlide() {
    this.slideTargets.forEach((element, index) => {
      element.hidden = index != this.indexValue
    })
  }
}
```

A lot is going on here, so let’s break it up.

#### Targets property

We can see a different usage of the _targets_ property. Because there's more than one element with the _"slice"_ value, an additional property _slideTargets_ (plural) was created by Stimulus. Using this variable we can loop through all corresponding elements.

#### Values property

Besides the _targets_ property, there's a second special property called _values_. It's used to denote that Stimulus should look for a data attribute named _data-slideshow-index-value_ that will contain a value with the _Number_ type. After found, this value will be automatically cast to the type specified (Number), and stored in a property called _indexValue_.

This can be used both to allow the backend to pass in some initial values to the controller, but also as a storage to keep state. Stimulus will keep the property on the controller object and the data attribute on the HTML element in sync.

#### Value change callback

Another difference in this example is the usage of the special method called _indexValueChanged_. Stimulus will look for methods following this name convention and call them automatically when the value of the attribute changes. We can see this happening in the _next_ and _previous_ methods, which modify _indexValue_ and causes the triggering of the callback. The callback then calls _showCurrentSlide_ method to update the slide visible on the screen.

### Final thoughts

As mentioned in the project's [guidebook][guidebook], Stimulus is a framework with very modest ambitions. It provides a set of tools and practices to help us build the frontend of our applications, enforcing the separation of content and behavior. This tool couples very well with Turbo to assist developers in crafting dynamic web applications, keeping the focus on simplicity.

I highly recommend reading the [official][guidebook] documentation, as it covers each aspect of the framework more deeply, and explains in more detail the reasoning behind the design decisions.

In the next posts, I'll be creating a full-featured simple app to demonstrate how Turbo and Stimulus can be used together to build a real application.


[hotwire-first-look]: {% post_url 2021-04-10-a-first-look-at-hotwire %}
[guidebook]: https://stimulus.hotwire.dev/handbook/origin
