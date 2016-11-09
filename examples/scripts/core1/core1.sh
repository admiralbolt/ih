#!/bin/bash

ih-convert-color --input "/path/to/your/image" --output "gray.png" --intype "bgr" --outtype "gray"
ih-threshold --input "gray.png" --output "thresh50.png" --thresh 50
ih-threshold --input "gray.png" --output "thresh75.png" --thresh 75
ih-threshold --input "gray.png" --output "thresh100.png" --thresh 100
