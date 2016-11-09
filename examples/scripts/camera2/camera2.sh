#!/bin/bash

ih-crop --input /path/to/your/image --output crop.png --ystart 280 --yend "y - 175" --xstart 1000 --xend 3200
ih-color-filter --input crop.png --output thresh.png --logic "((g - b) > 0)"
ih-contour-chop --input thresh.png --output chop.png --binary thresh.png --basemin 1000
ih-contour-cut --input chop.png --binary chop.png --output final.png --resize
