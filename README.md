# MTA-Project

This is the code to produce an interactive visualization which can be found at arettines.com/MTA-Graphic.  I used pandas v0.17.1 to organize and process the large amounts of data involved.  The visualization itself is built in html using the javascript libraries d3.v3.min.js, topojson.v1.min.js, and d3.tip.v0.6.3.js, which can be found at http://labratrevenge.com/d3-tip/javascripts/d3.tip.v0.6.3.js.

In order to produce the simplified polygonal map of NYC, I used the awesome site at http://www.mapshaper.org/, which takes a topojson file and runs the Visvalingam algorithm to produce a new topojson file with fewer edges.
