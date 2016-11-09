#!/bin/bash

ih-color-filter --input "/path/to/your/image" --output "logic0.png" --logic "(((r + g) + b) > 350)"
ih-color-filter --input "/path/to/your/image" --output "logic1.png" --logic "(r >= 250)"
ih-color-filter --input "/path/to/your/image" --output "logic2.png" --logic "((b > 150) and (b < 220))"
ih-color-filter --input "/path/to/your/image" --output "logic3.png" --logic "((((b max g) max r) - ((b min g) min r)) > 20)"
ih-color-filter --input "/path/to/your/image" --output "logic4.png" --logic "((((r + g) + b) > 700) or (((r + g) + b) < 100))"
ih-color-filter --input "/path/to/your/image" --output "logic5.png" --logic "((r - g) > 50)"
ih-color-filter --input "/path/to/your/image" --output "logic6.png" --logic "(((g - r) > 15) and (b < g))"