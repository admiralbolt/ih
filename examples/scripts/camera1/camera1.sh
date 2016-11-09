#!/bin/bash

ih-crop --input /path/to/your/image --output crop.png --ystart 0 --yend "y - 210" --xstart 0 --xend "x"
ih-color-filter --input crop.png --output thresh.png --logic "(g > 200)"
ih-contour-chop --input thresh.png --output chop.png --binary thresh.png --basemin 300
ih-contour-cut --input chop.png --binary chop.png --output final.png --resize
