Image Processing
================

This page contains specific implementation details of image processing functions.
Additionally, the next page contains an interactive image processing function viewer.
It allows for adjusting inputs and seeing results of many different functions
on several different sample input images.  Before talking about processing functions,
we are first going to talk about inputting resources.

.. _resource-image:

.. raw:: html

	<h3>Images</h3>

Images are mostly input at the beginning of processing,
but there area few functions such as :meth:`~ih.imgproc.Image.bitwise_and`
that take additional images as inputs.  When first loading the image,
it can be constructed with either a path to the image or a raw numpy array.
When loading an additional image into a function, it can be a path, a numpy array,
or a state.  Loading an image from a path simply requires a string of an absolute or relative path
to the image.

.. code-block:: python

	plant = ih.imgproc.Image("/path/to/your/image.png")

Most of the time other methods of input are not required, but they can
be useful in certain circumstances.  OpenCV represnts images as numpy arrays --
effectively, a large matrix that has a blue, green, and red value at each of the indices.
By allowing images to be loaded in as a numpy array directly, Image Harvest can be used in
conjunction with any other image tool that also uses OpenCV or represents images as numpy arrays.

.. code-block:: python

	im = cv2.imread("/path/to/your/image.png")
	plant = ih.imgproc.Image(im)

Finally, you can pass in a state to a function to use a previously saved image.
Because states require you to save something first, you cannot instantiate an
image with a state.  This is particularly useful when recoloring a thresholded image:

.. code-block:: python

	plant = ih.imgproc.Image("/path/to/your/image.png")
	plant.save("base")
	plant.convertColor("bgr", "gray")
	plant.threshold(127)
	plant.bitwise_and("base")

.. raw:: html

	<h3>ROI's</h3>

Regions Of Interest can also be input as either a list, or a json file.  If a region of interest is input as a list it should be of the form:

.. code-block:: python

    [ystart, yend, xstart, xend]

If a ROI is input as a json file, it should look like the following:

.. code-block:: python

    {
        "ystart": YOUR_VALUE,
        "yend": YOUR_VALUE,
        "xstart": YOUR_VALUE,
        "xend": YOUR_VALUE
    }

Each individual ROI argument has some special options.  Each argument can be auto-filled by using a value of -1.  For "xstart" and "ystart" this simply assigns a value of 0, but for "xend" and "yend" this fills the width and height of the image respectively. This isn't as necessary for the starting values, but can be useful for the ending values.  For example, let's say we want an roi that skips the first 400 pixels from the left / top side of our image:

.. code-block:: python

    # List style
    [400, -1, 400, -1]
    # Json style
    {
        "ystart": 400,
        "yend": -1,
        "xstart": 400,
        "xend": -1
    }

Instead of using -1 you can also use "x" and "y" to represent the full width and height respectively.
Adjusting the previous example:

.. code-block:: python

    # List style
    [400, "y", 400, "x"]
    # Json style
    {
        "ystart": 400,
        "yend": "y",
        "xstart": 400,
        "xend": "x"
    }

Finally, each individual argument can have a single arithmetic operation in it (except for multiplication).  Utilizing this, we can create fairly complex ROI's without too much effort.  For example, here is an ROI that targets only the bottom half of your image, and ignores 300 pixels on both the left and right sides:

.. code-block:: python

    # List style
    ["y / 2", "y", 300, "x - 300"]
    # Json style
    {
        "ystart": "y / 2",
        "yend": "y",
        "xstart": 300,
        "xend": "x - 300"
    }

.. autoclass:: ih.imgproc.Image
	:members:
