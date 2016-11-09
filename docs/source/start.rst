Getting Started
===============

There are 3 main ways of accessing the software.

1. Library Access
	The image processing and statistics functions can be accessed by importing ih.
	Within your script you create objects out of individual plant images and process them
	directly.  Ex:
	
	.. code-block:: python
	
		# import ih
		import ih.imgproc
		# load your image as an object
		plant = ih.imgproc.Image("/home/user/image.png", outputdir = "/home/user/")
		# execute processing functions, in this simple case,
		# the image is converted to grayscale, then thresholded.
		plant.convertColor("bgr", "gray")
		plant.threshold(127)
		# write the output
		plant.write("threshold.png")
		
	This method is good for testing and adjusting your image processing workflow,
	but does not scale well for large sets of images.
2. Command Line Access
	ih comes with dozens of micro-scripts providing individual access to each
	function.  Each script takes an input image, and writes an output image.  The
	previous example would be done with two commands as follows:
	
	.. code-block:: bash
	
		#!/bin/bash
		ih-convert-color --input "/home/user/image.png" --output "/home/user/gray.png" --intype "bgr" --outtype "gray"
		ih-threshold --input "/home/user/gray.png" --output "/home/user/threshold.png" --thresh 127
		
	This method is slightly different than the previous one in a few aspects.  The names of the command line
	scripts will not exactly match the names of the functions.  Because each script takes an image and
	writes an image, it is important to chain the output of one command into the input of the next command.
	This method can also be used to test your workflow.  Super computer workflows use this method for processing,
	so familiarity with command-line arguments are helpful, and ensure your large-scale runs process correctly.
	
3. Workflow Generation
	Super computer workflow generation and submission is complicated enough that there isn't a simple
	starter script, but it can be broken down into three major steps.  Each step is handled by user defined
	json template files.
	
	i. Image Loading
		Input images can range from automated systems such as LemnaTec, to pictures taken by hand.
		Besides the images themselves being different, the format of the input also differs greatly
		from source to source.  This step sets up the base job submission directory, and loads 
		images into a database, to keep the format consistent for all inputs.  Loading requires
		a template that defines where and how to load images into the database, as well as metadata
		to load for each image.  Metadata for images is not defined for each individual image, but
		rather, is loaded from the directory structure / names of the images.
	ii. Image Processing
		This step requires two inputs, a workflow template file, and a config file.  The workflow template
		file defines what image-processing scripts to use, and in what order.  Additionally, which numeric
		variables to extract are defined in the workflow template files.  The config file is for several
		pieces of system information, such as environment variables, and job cluster size.
	iii. Statistics
		This step also requires two inputs, a workflow template file, and a config file.  The workflow template
		file is identical to that of the previous step, except using statistic processing scripts.  The
		config file for this step is completely identical to that of the previous step.  Statistics workflows
		require that data has been processed, which means an image-processing workflow must be run first.
		Additionally, statistics workflows are still a work in progress.
		
The next session details several tutorials of how to use ih, for both local and distributed computing.  It
is recommended that you familiarize yourself with local computing examples before jumping into generating
super computer workflows.  Implementation details of specific functions can be found in further sections.
