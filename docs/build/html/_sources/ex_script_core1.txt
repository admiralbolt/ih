Core Processing Example #1
===========================
This section will detail a shorter script that provides details on how to get started with
script form image processing.  The script will detail how to use several core functions
to load, save, and show images.

Python Script
-----------------------
:download:`Download Script <../../examples/scripts/core1/core1.txt>`

:download:`Download Image <../../examples/scripts/core1/base.png>`

.. code-block:: python

	import ih.imgproc

	plant = ih.imgproc.Image("/path/to/your/image")

	plant.save("base")
	plant.show("base")
	plant.write("base.png")

	plant.convertColor("bgr", "gray")
	plant.save("gray")
	plant.show("gray")
	plant.write("gray.png")

	plant.threshold(50)
	plant.save("thresh50")
	plant.show("thresh50")
	plant.restore("gray")

	plant.threshold(75)
	plant.save("thresh75")
	plant.show("thresh75")
	plant.restore("gray")

	plant.threshold(100)
	plant.save("thresh100")
	plant.show("thresh100")
	plant.restore("gray")

	plant.wait()
	plant.restore("thresh50")
	plant.write("thresh50.png")

This script shows how to get started with ih.  Let's talk about it block by block:

.. code-block:: python

	import ih.imgproc
	plant = ih.imgproc.Image("/path/to/your/image")

These two lines setup your image.  The first line imports the ih imgproc module,  this module contains
all of ih's image processing functionality.  The second line creates an Image object named 'plant'.
The plant object now has properties that define it, and methods we can perform on it.  The rest of the script
deals specifically with the methods we can perform on our image objects.

.. code-block:: python

	plant.save("base")
	plant.show("base")
	plant.write("base.png")

These three lines use three separate methods on our plant object, :py:meth:`~ih.imgproc.Image.save`,
:py:meth:`~ih.imgproc.Image.show`, and :py:meth:`~ih.imgproc.Image.write`. Each of these
methods performs exactly what its named -- the save method saves the image for future use, the show method
displays the image, and the write method writes the image to a file.  Each method has an argument
passed into it, determining the name to be used in each case.  Calling plant.save("base") saves the image
with the name base, plant.show("base") shows the image with the window title base, and plant.write("base.png")
writes the image to a file named base.png.  Here's what our base image looks like:

.. image:: ../../examples/scripts/core1/base.png
	:align: center

|

.. code-block:: python

	plant.convertColor("bgr", "gray")
	plant.save("gray")
	plant.show("gray")
	plant.write("gray.png")

The :py:meth:`~ih.imgproc.Image.convertColor` method performs a color spectrum shift, changing our image from a color image i.e. "bgr"
to a gray scale image i.e. "gray".  It should be noted, that all methods overwrite the current image -- which is way the save / restore
functionality is so important.  Additionally, converting an image to gray scale from color is an important non-linear shift.
A color image is called "bgr" because of the three colors in the image, blue, green, and red.  Each pixel has a value for
each of these colors, or channels.  Converting to gray condenses the image to a single channel -- intensity.
This means that you **cannot** use :py:meth:`~ih.imgproc.Image.convertColor` to restore color to a gray scale image.
Although we do not use it in this example, the reason for saving the base image is to restore color in a future step.
The last three lines of this block of code perform the exact same function as the previous block, only using
different names for saving, showing, and writing.  Here's what our gray scale image looks like:

.. image:: ../../examples/scripts/core1/gray.png
	:align: center

|

.. code-block:: python

	plant.threshold(50)
	plant.save("thresh50")
	plant.show("thresh50")
	plant.restore("gray")

Now that we have a gray scale image, we perform a :py:meth:`~ih.imgproc.Image.threshold` on it.  This simply
checks the value of each pixels intensity, and checks to see if it beats the cutoff we specify.  In this case,
if the pixel has an intensity greater than 50, we keep it.  Intensity values range from 0 to 255.  The
:py:meth:`~ih.imgproc.Image.save` and :py:meth:`~ih.imgproc.Image.show` methods should be familiar,
but the fourth line contains a new method, :py:meth:`~ih.imgproc.Image.restore`.  This method restores
the image to a previously saved image.  In the previous block we saved our gray scale image under the name 'gray'.
Here, we simply restore that image after thresholding.  The purpose of this is to compare multiple threshold values.
We restore the gray image at the end of each thresholding block to use the same image for thresholding.  Here's the
result of thresholding by 50:

.. image:: ../../examples/scripts/core1/thresh50.png
	:align: center

|

.. code-block:: python

	plant.threshold(75)
	plant.save("thresh75")
	plant.show("thresh75")
	plant.restore("gray")

This block is identical to the previous one, except we use a threshold value of 75 instead of 50,
and we rename our saved image and displayed image accordingly.  Here's the result of thresholding
by 75:

.. image:: ../../examples/scripts/core1/thresh75.png
	:align: center

|

.. code-block:: python

	plant.threshold(100)
	plant.save("thresh100")
	plant.show("thresh100")
	plant.restore("gray")

This block is identical to the previous one, except we use a threshold value of 100 instead of 75,
and we rename our saved image and displayed image accordingly.  Here's the result of thresholding
by 100:

.. image:: ../../examples/scripts/core1/thresh100.png
	:align: center

|

.. code-block:: python

	plant.wait()
	plant.restore("thresh50")
	plant.write("thresh50.png")

The final block introduces a new method, :py:meth:`~ih.imgproc.Image.wait`.  This method
simply halts execution until a key is pressed, then destroys all displayed windows.  This
means that once this point in the script is hit, there should be 5 open windows, the base image,
the gray image, and one for each of the three thresholds.  After execution is resumed,
we restore the threshold by 50, and write it to a file.

Command Line Script
-------------------
:download:`Download Script <../../examples/scripts/core1/core1.sh>`

:download:`Download Image <../../examples/scripts/core1/base.png>` (The image is identical to the one above)

.. code-block:: bash

	#!/bin/bash

	ih-convert-color --input "/path/to/your/image" --output "gray.png" --intype "bgr" --outtype "gray"
	ih-threshold --input "gray.png" --output "thresh50.png" --thresh 50
	ih-threshold --input "gray.png" --output "thresh75.png" --thresh 75
	ih-threshold --input "gray.png" --output "thresh100.png" --thresh 100

This bash script performs the exact same workflow as the one above.  Although not major, it is important to note the
differences between library and command line access.  Command line access loads and writes an image at each step,
whereas library access loads once, and only writes when you tell it to.  Additionally, script names are close to that
of the method, and all follow lower case format, with words separated by dashes, and ih pre-pendening all commands.
The most notable difference, is that a restore method is unnecessary with command-line input.  We simply reuse the gray.png
file we wrote once.  Additionally, there is no initial setup, you simply begin processing.  The arguments passed into the
command line arguments match identically with the method arguments above.
