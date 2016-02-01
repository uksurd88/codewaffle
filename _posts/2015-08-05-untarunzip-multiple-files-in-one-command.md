---
layout: post
title: Untar/Unzip multiple files in one command
categories: 
  - None
tags: []
published: true
link: null
image: 
  feature: null
  credit: null
  creditlink: null
comments: true
excerpt: A post showing how to untar/unzip multiple files in one go.
---


Hola!
Ungzipping all files in one line 
{% highlight css %}
For *.gz
find -name '*.gz' -exec tar xzv '{}' ';'
For *.tar.gz
find -name '*.tar.gz' -exec tar xzvf '{}' ';'
{% endhighlight %}

It uses all the files that ‘find’ outputs and send it to tar. Same can be applied to any other archive, just change the respective parameters.
