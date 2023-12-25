---
type: "posts"
topPost: false
title: "{{ replace .Name "-" " " | title }}"
date: {{ .Date }}

enableLeftSidebar: false
enablerightSidebar: false

draft: true
comment: false
toc: true
copyright: false
categories: 
  - 'futures trading'
featured: false
resources: 
  - src: "feature.jpg"
    title: "{{ .Name | urlize }}"
---
