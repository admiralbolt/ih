.. |br| raw:: html

	<br />

Arkansas Workshop July 2015
============================

Hello Arkansas State!  This workshop covers basic command line instructions and local processing of an image from LemnaTec.  Either look at the corresponding part of the  installation page for your computer (`Mac OS X <installation.html#mac-osx>`_, `Windows <installation.html#windows>`_) or head to the next section.

Command Line Crash Course
-------------------------
If you are unfamiliar with the command line, or have never opened the Terminal or Command Prompt app before, this section is for you.  There are several useful features available while using Image Harvest through a Python interpreter, which requires a small amount of command line knowledge -- namely the ability to navigate through directories.  For all operating systems, files are structured hierarchically in directories.  A directory almost always has a parent (represented by ".."), and it may contain files or more sub-directories.  The only directory not that doesn't have a parent is the root directory which is "/" for Mac OS X and Linux, and "C:\\" for Windows users.  Since all directories are children of the root directory, you can write the path to any file all the way from the root.  These types of paths are absolute paths.  "/Users/username/Downloads/file.txt" and "C:\\Users\\username\\Downlaods\\file.txt" are both examples of absolute paths.  The counterpart to absolute paths is relative paths, which is a path to any file written from where you are currently located.  If you are currently located in your Downloads folder, the relative path "file.txt" is the same as the absolute path "/Users/username/Downloads/file.txt".  These concepts apply to all operating systems, however, each uses different commands for achieving directory navigation.

Mac OS X
#########
First and foremost, the terminal app is located at /Applications/Utilities/Terminal.app.  There are only 3 important commands:

* cd -- Which stands for "change directory".  This command allows you to move your current location to a new directory as specified by an argument.  It can be either an absolute or a relative path.
* ls -- Which stands for "list".  This command lists all the files and folders in the current directory.
* pwd -- Which stands for "print working directory", and prints your current directory's absolute path.

Examples:

.. code-block:: bash

    # Move to your home folder.
    cd /Users/username/
    # Move to your downloads folder from your home folder.
    cd Downloads
    # Move up a folder -- back to your home folder.
    cd ..
    # List files in your home folder
    ls
    # List files in your home folder as a list
    ls -al
    # List files in your home folder as a list with coloring
    ls -alG
    # Print the absolute path to your home folder.
    pwd


Windows
########
The Command Prompt app can be opened by typing cmd into the windows search bar.  There are only 2 important commands:

* cd -- Which stands for "change directory".  This command allows you to move your current location to a new directory as specified by an argument.  It can be either an absolute or a relative path.
* dir -- Which stands for "directory".  This command both prints your current location, and prints files and directories in your current location.

Examples:

.. code-block:: bash

    # Move to your home folder
    cd C:\\Users\\username
    # Move to your downloads folder from your home folder.
    cd Downloads
    # Move up a folder -- back to your home folder.
    cd ..
    # List the path to your home folder, and the files in your home folder.
    dir

First Image
------------
If you have not already, look at the corresponding part of the installation page for your computer (`Mac OS X <installation.html#mac-osx>`_, `Windows <installation.html#windows>`_).  Once you've got Image Harvest installed, download the following image:

:download:`First Image <../images/sample/rgbsv1.png>`

Once it's saved, navigate to it from the command line -- By default either /Users/username/Downloads/ or C:\\Users\\username\\Downloads.  From there open up a python interpreter by typing the following command:

.. code-block:: bash

    python

You should see something like:

.. code-block:: bash

    Python 2.7.6 (default, Sep  9 2014, 15:04:36)
    [GCC 4.2.1 Compatible Apple LLVM 6.0 (clang-600.0.39)] on darwin
    Type "help", "copyright", "credits" or "license" for more information.
    >>>

The 3 right angle brackets are where you type your input.  Within the python interpreter
command line tools won't work, so when loading a file you need to already know it's path
or it will be difficult to find.  Execute the following lines from the python interpreter:

.. code-block:: python

    # Import the Image Harvest library
    import ih.imgproc
    # Load your downloaded image!
    plant = ih.imgproc.Image("rgbsv1.png")
    # Show your plant!
    plant.show()
    # Wait for user input, then destroy the window
    plant.wait()

You should see a window named "window 1" pop up with a smaller version of your image in it!
By calling the :py:meth:`~ih.imgproc.Image.wait` method, the window will be displayed until you press any key, and control is taken away from the python interpreter.  Every processing script begins by loading the library, and loading the image, and all Image Harvest functions are performed on a loaded image.  Using the python interpreter provides some powerful tools to adjust your analysis on the fly and test out function parameters through the use of "states".

.. code-block:: python

    # Save the current state under the name "base"
    plant.save("base")
    # Convert the plant to grayscale
    plant.convertColor("bgr", "gray")
    # Save the current state under the name "gray"
    plant.save("gray")
    # Threshold with a questionable value!
    plant.threshold(255)
    plant.show()
    plant.wait()

If done correctly, you should see a window named "window 2" that's completely black.  The threshold function thresholds by pixel intensity, which is an integer from 0 to 255, so thresholding by 255 means no pixels should make it through.
Since we saved states ("base" and "gray"), we can restore a previous state and try the thresholding operation again with adjusted parameters:

.. code-block:: python

    # Restore the gray state
    plant.restore("gray")
    # Threshold round 2
    plant.threshold(190)
    plant.show()
    plant.wait()

You should see a window name "window 3" that's only black and white, and you should be able to see the outline of the plant in black.  We can utilize states for more than just restoring a previous image:

.. code-block:: python

    # Save the black & white state!
    plant.save("binary")
    # Invert the color, display with name
    plant.bitwise_not()
    plant.show("Inverted Mask")
    # Convert the mask to bgr, combine it with the "base" state
    plant.convertColor("gray", "bgr")
    plant.bitwise_and("base")
    # Save the image and display it
    plant.save("recolored")
    plant.show("Recolored Image")
    plant.wait()

.. image:: ../../examples/workshops/arkansas_july_2015/inverted.png
    :align: left

.. image:: ../../examples/workshops/arkansas_july_2015/recolored.png
    :align: right

.. raw:: html

    <div class="row" style="clear:both;"></div><br />

This time, you should see two windows pop up, one named "Inverted Mask" and the other named "Recolored Image".  The inverted mask window shows our inverted thresholded image, and the recolored image window shows the final output of combining our mask with our base image.  We keep all the pixels that are in the mask, but we use the colors of the base image.  Utilizing a few more functions, we can finish the processing of our first image:

.. code-block:: python

    # Crop the pot out of the image.
    # ROI is of the form [ystart, yend, xstart, xend]
    plant.crop([300, 2150, 0, "x"])
    plant.save("cropped")
    plant.show("Cropped Image")
    # Resize the image to just the plant
    # See following paragraph for more info on contourCut
    plant.contourCut("cropped", resize = True)
    plant.show("Final Image")
    plant.write("final.png")
    plant.wait()


.. image:: ../../examples/workshops/arkansas_july_2015/cropped.png
    :align: left

.. image:: ../../examples/workshops/arkansas_july_2015/final.png
    :align: right


.. raw:: html

    <div class="row" style="clear:both;"></div><br />

You should see your final displayed image!  The :py:meth:`~ih.imgproc.Image.contourCut` function crops an image based on contours, or grouped areas of pixels, and only keeps contours in the image that have a minimum required area.  Since the plant is completely connected (unless processing has removed some pixels), it should have a large contour area, and thus is kept within the image.  Finally, we write our image with the name "final.png".

Python Script
-------------

:download:`Download Script <../../examples/workshops/arkansas_july_2015/firstimage.txt>`

:download:`Download Image <../images/sample/rgbsv1.png>` (same as above)

This script performs exactly the process we worked through only as a standalone python script.  Update the image path accordingly, and run it to see the same results, as well as windows for each step.


.. code-block:: python

    # Load the library & image
    import ih.imgproc
    plant = ih.imgproc.Image("/path/to/your/image")
    # Save & show the base image
    plant.save("base")
    plant.show("Base")
    # Convert to gray, save the image
    plant.convertColor("bgr", "gray")
    plant.save("gray")
    plant.show("Grayscale")
    # Threshold the image incorrectly AND correctly
    plant.threshold(255)
    plant.show("Threshold 255")
    plant.restore("gray")
    plant.threshold(190)
    plant.save("binary")
    plant.show("Threshold 190")
    # Recolor the image
    plant.bitwise_not()
    plant.convertColor("gray", "bgr")
    plant.bitwise_and("base")
    plant.save("recolor")
    plant.show("Recolored Image")
    # Crop the image, produce the final output
    plant.crop([300, 2150, 0, "x"])
    plant.save("cropped")
    plant.show("Cropped")
    plant.contourCut("cropped", resize = True)
    plant.show("Final")
    plant.write("final.png")
    plant.wait()


Day 2
------
Now that we have everything installed, we'll work through a pipeline for an image, extract some data, and compare to LemnaTec.

:download:`Team 1 Rice 0_0_2 <../../examples/workshops/arkansas_july_2015/0_0_2.png>`

:download:`The Pipeline <../../examples/workshops/arkansas_july_2015/pipeline.txt>`

The pipline:

.. code-block:: python

    import ih.imgproc

    # base plant
    plant = ih.imgproc.Image("0_0_2.png")
    plant.save("base")
    plant.show("base")

    # blur
    plant.blur((5, 5))
    plant.save("blur")
    plant.show("Blur")

    # meanshift
    plant.meanshift(4, 4, 40)
    plant.save("shift")
    plant.show("Meanshift")

    # colorFilter
    plant.colorFilter("(((g > r) and (g > b)) and (((r + g) + b) < 400))")
    plant.colorFilter("(((r max g) max b) - ((r min g) min b)) > 12)")
    plant.save("cf")
    plant.show("Color filter")

    # contourCut
    plant.contourCut("cf", basemin = 3000, resize = True)
    plant.save("cut")
    plant.show("Contour Cut")

    # recolor
    plant.convertColor("bgr", "gray")
    plant.threshold(0)
    plant.convertColor("gray", "bgr")
    plant.bitwise_and("base")
    plant.write("final.png")
    plant.show("Final")

    print plant.extractPixels()
    print plant.extractConvexHull()

    plant.wait()

That's a lot of code.  Let's break it down piece by piece:

Loading
#######

.. code-block:: python

    import ih.imgproc

    # base plant
    plant = ih.imgproc.Image("0_0_2.png")
    plant.save("base")
    plant.show("base")

This part should be fairly familiar -- we load the Image Harvest library with import ih.imgproc, we load our image "0_0_2.png", and we save & display it under the name "base".

Blur
#####

.. code-block:: python

    # blur
    plant.blur((5, 5))
    plant.save("blur")
    plant.show("Blur")

Here we call the :py:meth:`~ih.imgproc.Image.blur` function -- which does exactly that.  Blur can take a few arguments, but the most important and only required argument is the first which specifies the kernel size -- a larger kernel means a more blurry output image.  The kernel size is represented as two numbers: (width, height), and both the width and height must be odd and positive.  Try blurring with a kernel size of (15, 15) instead of (5, 5).

Why blur?  Blurring greatly reduces the noise in an image, which is random variations of pixel colors.  Reducing these variations helps us to more easily define a region in an image.  Look at the inside of the pot for example -- the edges between individual rocks have become much less distinct as a result of the blurring, which makes it easier to percieve as a single continuous region.  The next step continues to reduce variation and separate regions from each other.

Meanshift
#########

.. code-block:: python

    # meanshift
    plant.meanshift(4, 4, 40)
    plant.save("shift")
    plant.show("Meanshift")

Here we call the :py:meth:`~ih.imgproc.Image.meanshift` function, which performs mean shift segmentation of the image.  Mean shift segmentation groups regions in an image that are geographically close AND close in color.  The first two arguments define the geographically distance, and the third argument defines the color variation allowed.

Why meanshift?  Meanshift makes the next step in grouping an image into regions.  In this case, we have some very easily defined regions that are close both geographically and close in color.  The plant itself is completely connected and a similar shade of green.  The interior of the pot is contained within a single circle in the image, and is made of similarly colored rocks.  Both of these regions become much more uniform, and thus much easier to process as a result of this step.

Color Filter
############

.. code-block:: python

    # colorFilter
    plant.colorFilter("(((g > r) and (g > b)) and (((r + g) + b) < 400))")
    plant.colorFilter("(((r max g) max b) - ((r min g) min b)) > 12)")
    plant.save("cf")
    plant.show("Color filter")

Here we call the :py:meth:`~ih.imgproc.Image.colorFilter` function, which solves arbitrary color logic and then applies it to the image.  What does that mean?  Effectively, we create a color pattern, and we look for all pixels that match this color pattern.  So this pattern: "((g > r) and (g > b))", reads as: "Pixels whose green value is greater than their red value AND whose green value is greater than their blue value."  In natural language: "Pixels that are predominantely green."  The next pattern: "(((r + g) + b) < 400))", reads as: "Pixels whose red value plus green value plus blue value is less than 400."  In natural language: "Pixels that aren't too bright."  Finally we have the pattern: "(((r max g) max b) - ((r min g) min b)) > 12)", which reads as: "Pixels whose maximum value of r,g,b minus mimim value of r,g,b is greater than 12".  In natural language: "Pixels that aren't white, gray, or black."

Why colorFilter?  Processing power.  The colorFilter function is very fast, and can evaluate and apply complex logic in less than a second.  Additionally, since the function evalutes logic on a per-pixel basis, it can adapt to brightness changes or noise in images that a definite color range might miss.

Contour Cut
###########

.. code-block:: python

    # contourCut
    plant.contourCut("cf", basemin = 3000, resize = True)
    plant.save("cut")
    plant.show("Contour Cut")

Here we call the :py:meth:`~ih.imgproc.Image.contourCut` function, which crops an image based on contours in an image, which are connected regions of pixels.  The function searches for all contours in the image that are greater than the size of the basemin parameter, and crops the image to fit those contours.

Why contourCut?  Removal of edge noise.  The plant itself is completely connected, and thus will have the largest contour in the image by far.  Utilizing this, we can find a value that will keep our plant in the image, while removing a lot of edge noise from it.

Recoloring
##########

.. code-block:: python

    # recolor
    plant.convertColor("bgr", "gray")
    plant.threshold(0)
    plant.convertColor("gray", "bgr")
    plant.bitwise_and("base")
    plant.write("final.png")
    plant.show("Final")

What's really happening here, is we are creating a mask of our current image, and then overlaying it on our base image to extract our original color.  Blurring and segmenting our image changed its original color, and we want to restore that.  The first 3 lines create the mask.  We first convert the image to grayscale with :py:meth:`~ih.imgproc.Image.convertColor`, and then :py:meth:`~ih.imgproc.Image.threhsold` with a value of 0.  By thresholding the image with a value of 0, we keep every pixel from our grayscale image that has an intensity of at least 1.  This means we keep every non-black pixel from our grayscale image.  We then convert the image back to "bgr" from "gray", however, this does NOT restore color to the image.  Our binary image only has a single channel (intensity), but our color image has 3 channels (b, g, r).  We can't overlay our mask while it only has a single channel, so we convert it to "bgr" to give it 3 channels.  We then use :py:meth:`ih.imgproc.Image.bitwise_and` to overaly our mask on our base image.

Extraction
##########

.. code-block:: python

    print plant.extractPixels()
    print plant.extractConvexHull()

The print function is native to python and simply outputs information to the screen.  The :py:meth:`~ih.imgproc.Image.extractPixels` function returns the total number of non-zero pixels in the image, and the :py:meth:`~ih.imgproc.Image.extractConvexHull` function returns the area of the convexHull surrounding all non-black pixels in the image.

Extras
------

.. image:: ../../examples/workshops/arkansas_july_2015/shifted.png
    :align: center
