---
title: "Untar/Unzip Multiple Files in One Command"
meta_title: ""
description: "A quick tip showing how to untar or unzip multiple archive files in one go using find and tar."
date: 2015-08-05T00:00:00Z
image: ""
categories: ["bioinformatics", "bash"]
authors: ["Sukhdeep Singh"]
tags: ["bash", "linux", "tips"]
draft: false
---

Hola!

Ungzipping all files in one line:

```bash
# For *.gz
find -name '*.gz' -exec tar xzv '{}' ';'

# For *.tar.gz
find -name '*.tar.gz' -exec tar xzvf '{}' ';'
```

It uses all the files that `find` outputs and sends them to `tar`. The same can be applied to any other archive format, just change the respective parameters.
