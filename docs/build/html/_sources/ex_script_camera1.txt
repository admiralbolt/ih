Camera Processing Example #1
=============================
This section will detail a shorter script that provides details on how to process
an image manually taken with a camera.

Python Script
-----------------------
:download:`Download Script <../../examples/scripts/camera1/camera1.txt>`

:download:`Download Image <../../examples/scripts/camera1/IMG_6050.JPG>`

.. code-block:: python

  import ih.imgproc

  plant = ih.imgproc.Image("/path/to/your/image")

  plant.crop([0, "y - 210", 0, "x"])
  plant.write("crop.png")

  plant.colorFilter("(g > 200)")
  plant.write("thresh.png")

  plant.contourChop(plant.image, 300)
  plant.write("chop.png")

  plant.contourCut(plant.image, resize = True)
  plant.write("final.png")

This script has only four processing steps but produces a very good result.  Let's
look at each block

.. code-block:: python

	import ih.imgproc
	plant = ih.imgproc.Image("/path/to/your/image")

These two lines setup your image.  The first line imports the ih image processing
module, the second loads our image.  Here's what our base image looks like:

.. image:: ../../examples/scripts/camera1/IMG_6050_small.jpeg
  :align: center

|

.. code-block:: python

  plant.crop([0, "y - 210", 0, "x"])
  plant.write("crop.png")

First, we :py:meth:`~ih.imgproc.Image.crop` the image to simply remove the pot.  All ROI's are of the form
[ystart, yend, xstart, xend], so in this case we are only removing the bottom
210 pixels from the image.  We then write the image:

.. image:: ../../examples/scripts/camera1/IMG_6050_crop.png
  :align: center

|

.. code-block:: python

  plant.colorFilter("(g > 200)")
  plant.write("thresh.png")

Next, we apply a :py:meth:`~ih.imgproc.Image.colorFilter` to the image, with the
logic "g > 200".  This means that we only keep pixels in the image whose green
channel is greater than 200.  We then write the image:

.. image:: ../../examples/scripts/camera1/IMG_6050_thresh.png
  :align: center

|

.. code-block:: python

  plant.contourChop(plant.image, 300)
  plant.write("chop.png")


We then use the :py:meth:`~ih.imgproc.Image.contourChop` function to remove
small contours from the image.  This takes advantage of the fact that the
plant is completely connected, and the noise around it isn't.  We then write
the image:

.. image:: ../../examples/scripts/camera1/IMG_6050_chop.png
  :align: center

|

.. code-block:: python

  plant.contourCut(plant.image, resize = True)
  plant.write("final.png")

Finally, we use the :py:meth:`~ih.imgproc.Image.contourCut` function to
crop the image to just the plant, and write our final result:

.. image:: ../../examples/scripts/camera1/IMG_6050_final.png
  :align: center

Command Line Script
-------------------
:download:`Download Script <../../examples/scripts/camera1/camera1.sh>`

:download:`Download Image <../../examples/scripts/camera1/IMG_6050.JPG>` (The image is identical to the one above)

.. code-block:: bash

  #!/bin/bash

  ih-crop --input /path/to/your/image --output crop.png --ystart 0 --yend "y - 210" --xstart 0 --xend "x"
  ih-color-filter --input crop.png --output thresh.png --logic "(g > 200)"
  ih-contour-chop --input thresh.png --output chop.png --binary thresh.png --basemin 300
  ih-contour-cut --input chop.png --binary chop.png --output final.png --resize


This bash script performs the exact same workflow as the one above.  Although not major, it is important to note the
differences between library and command line access.  Command line access loads and writes an image at each step,
whereas library access loads once, and only writes when you tell it to.  Additionally, script names are close to that
of the method, and all follow lower case format, with words separated by dashes, and ih pre-pendening all commands.
The most notable difference, is that a restore method is unnecessary with command-line input.  We simply reuse the gray.png
file we wrote once.  Additionally, there is no initial setup, you simply begin processing.  The arguments passed into the
command line arguments match identically with the method arguments above.
