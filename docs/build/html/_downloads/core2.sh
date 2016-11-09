#!/bin/bash

ih-convert-color --input "base.png" --output "gray.png" --intype "bgr" --outtype "gray"
ih-gaussian-blur --input "gray.png" --output "blur.png" --kwidth 5 --kheight 5
ih-adaptive-threshold --input "blur.png" --output "thresh.png" --value 255 --adaptiveType "mean" --thresholdType "binary" --blockSize 15 --C 3
ih-bitwise-not --input "thresh.png" --output "invert.png"
ih-bitwise-and --input1 "base.png" --input2 "invert.png" --output "recolor.png"
ih-morphology --input "recolor.png" --output "morph.png" --morphType "open" --ktype "rect" --kwidth 3 --kheight 3
ih-color-filter --input "morph.png" --output "filter.png" --logic "(((max - min) > 40) and ((b - g) < 30))" --ystart "y - 350"
ih-threshold --input "filter.png" --output "binary.png" --thresh 0
ih-contour-cut --input "filter.png" --binary "binary.png" --output "final.png" --basemin 500 --resize

