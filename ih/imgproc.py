"""
This file is part of Image Harvest.

Image Harvest is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Image Harvest is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Image Harvest.  If not, see <http://www.gnu.org/licenses/>.

.. module:: imgproc
    :platform: Mac, Linux
    :synopsis: Image processing function wrappers to opencv.

.. moduleauthor:: Avi Knecht <avi@kurtknecht.com>

"""

import os
import cv2
import numpy as np
import math
import conf
import sqlite3
import pymeanshift as pms
import traceback
import json
import random

class ColorFilter(object):

    """
    Color Filtration logic container.
    """
    def __init__(self, filter):
        self.tokens = {
            "True": True,
            "False": False,
            "and": lambda left, right: np.logical_and(left, right),
            "or": lambda left, right: np.logical_or(left, right),
            ">": lambda left, right: left > right,
            "<": lambda left, right: left < right,
            ">=": lambda left, right: left >= right,
            "<=": lambda left, right: left <= right,
            "=": lambda left, right: left == right,
            "+": lambda left, right: left + right,
            "-": lambda left, right: left - right,
            ".": lambda left, right: left * right,
            "/": lambda left, right: left / right,
            "max": lambda left, right: np.maximum(left, right),
            "min": lambda left, right: np.minimum(left, right),
            "not": lambda left, right: np.invert(left),
            "(": "(",
            ")": ")",
        }
        self.filterString = filter
        self.emptyRes = True
        return

    def _createArgList(self):
        s = self.filterString.replace("(", " ( ")
        s = s.replace(")", " ) ")
        self.filter = []
        for item in s.split():
            if item in self.tokens:
                self.filter.append(self.tokens[item])
            else:
                try:
                    val = int(item)
                    self.filter.append(val)
                except:
                    raise Exception("Invalid logic string.")
        #self.filter = [self.tokens[x] if x in self.tokens else int(x) for x in s.split()]
        return

    def _find(self, what, start = 0):
        return [i for i,x in enumerate(self.filter) if x == what and i >= start]

    def _parens(self):
        left_1st = self._find("(")
        if not left_1st:
            return False, -1, -1
        left = left_1st[-1]
        right = self._find(")", left + 2)[0]
        return True, left, right

    def _eval(self, filter):
        return filter[1](filter[0], filter[2])

    def _formattedEval(self, filter):
        if not filter:
            return self.emptyRes
        if len(filter) == 1:
            return filter[0]

        has_parens, l_paren, r_paren = self._parens()

        if not has_parens:
            return self._eval(filter)

        filter[l_paren:r_paren + 1] = [self._eval(filter[l_paren+1:r_paren])]
        self.emptyRes = self._eval
        return self._formattedEval(filter)

    def apply(self, image, roi):
        self.tokens["r"] = image[:,:,2].astype(float)
        self.tokens["g"] = image[:,:,1].astype(float)
        self.tokens["b"] = image[:,:,0].astype(float)
        self.tokens["i"] = np.add(np.add(self.tokens["r"], self.tokens["g"]), self.tokens["b"])
        self.tokens["high"] = np.maximum(np.maximum(self.tokens["r"], self.tokens["g"]), self.tokens["b"])
        self.tokens["low"] = np.minimum(np.minimum(self.tokens["r"], self.tokens["g"]), self.tokens["b"])
        self._createArgList()
        result = cv2.cvtColor(np.where(self._formattedEval(self.filter), 255, 0).astype(np.uint8), cv2.COLOR_GRAY2BGR)
        image[roi[0]:roi[1], roi[2]:roi[3]] = cv2.bitwise_and(image[roi[0]:roi[1], roi[2]:roi[3]], result[roi[0]:roi[1], roi[2]:roi[3]])
        return image



class Image(object):

    """
    An individual image.  Each image is loaded in as its own instance of the Image class for processing.
    """
    def __init__(self, input, outputdir = ".", writename = None, dev = False, db = None, dbid = None):
        """
        :param input: The input resource, either a path to an image or a raw numpy array.
        :type resource: numpy.ndarray or str
        :param outputdir: The directory to write output files
        :type outputdir: str
        :param writename: The name to write the output file as, should include extension.
        :type writename: str
        :param dev: Dev mode will do something...
        :type dev: bool
        """
        if os.path.isdir(outputdir):
            self.states = {}
            self._loadDb(db, dbid)
            self.input = input
            self.fname, self.image = self._loadResource(input)
            self.y = self.image.shape[0]
            self.x = self.image.shape[1]
            self.outputdir = os.path.abspath(outputdir)
            if writename:
                self.writename = writename
            elif isinstance(input, np.ndarray):
                self.writename = "out.png"
            else:
                self.writename = os.path.basename(input)
            self.dev = dev
            self.window = 1
        else:
            raise Exception("Invalid output!")
        return

    def _closeDb(self):
        if self.conn:
            self.conn.close()
        return

    def _loadDb(self, db, dbid):
        if db:
            if os.path.isfile(db):
                if dbid:
                    self.dbid = dbid
                    self.conn = sqlite3.connect(db, check_same_thread = False)
                    self.conn.row_factory = sqlite3.Row
                    result = self.conn.execute("select pegasusid from images where pegasusid=?", (self.dbid,))
                    if not result.fetchone():
                        raise Exception("Invalid pegasusid given!")
                    self._addColumn("error")
                else:
                    raise Exception("A database id must be provided if you give a database.")
            else:
                raise Exception("Invalid database given!")
        else:
            self.conn = False
        return

    def _addColumn(self, column, tablename = "images"):
        if self.conn:
            if column not in [row["name"] for row in self.conn.execute("PRAGMA table_info(" + tablename + ");")]:
                self.conn.execute("alter table " + tablename + " add column " + column + ";")
                self.conn.commit()
        return


    def _loadROIArg(self, arg, i):
        vals = {
            0: 0,
            1: self.y,
            2: 0,
            3: self.x
        }
        arg = str(arg)
        if arg == "-1":
            return vals[i]
        arg = arg.replace("x", str(self.x)).replace("y", str(self.y)).replace(" ","")
        if "-" in arg:
            try:
                left, right = arg.split("-")
                return int(left) - int(right)
            except:
                raise Exception("Could not load roi fragment '%s'" % (arg,))
        elif "+" in arg:
            try:
                left, right = arg.split("+")
                return int(left) + int(right)
            except:
                raise Exception("Could not load roi fragment '%s'" % (arg,))
        elif "/" in arg:
            try:
                left, right = arg.split("/")
                return int(left) / int(right)
            except:
                raise Exception("Could not load roi fragment '%s'" % (arg,))
        elif "*" in arg:
            try:
                left, right = arg.split("*")
                return int(left) / int(right)
            except:
                raise Exception("Could not load roi fragment '%s'" % (arg,))
        else:
            return int(arg)


    def _loadROI(self, roi):
        """
        :param roi: The region of interest to load.
        :type roi: list or file
        :return: The region of interest of form [ystart, yend, xstart, xend]
        :rtype: list
        :raises OSError: if the input path does not exist.

        Loads a region of interest, either a path to an roi or a raw list.
        """
        if not roi:
            roi = [-1, -1, -1, -1]
        if isinstance(roi, list):
            return [self._loadROIArg(z, i) for i,z in enumerate(roi)]
        else:
            if os.path.isfile(roi):
                try:
                    with open(roi, "r") as rh:
                        r = json.load(rh)
                        if all(x in r for x in ["xstart", "xend", "ystart", "yend"]):
                            return [self._loadROIArg(r["ystart"], 0), self._loadROIArg(r["yend"], 1), self._loadROIArg(r["xstart"], 2), self._loadROIArg(r["xend"], 3)]
                        else:
                            raise Exception("Input roi file '%s' needs xstart, xend, ystart, and yend definitions!" % (roi,))
                except Exception as e:
                    print traceback.format_exc()
                    raise Exception("Input roi file '%s' is not valid json!" % (roi,))
            else:
                raise Exception("Input path to roi file '%s' does not exist!" % (roi,))
        return

    def _writeROI(self, roi, output):
        """
        :param roi: The region of interest to write.
        :type roi: list
        """
        try:
            with open(self.outputdir + "/" + output, "w") as wh:
                wh.write(json.dumps({"ystart": roi[0], "yend": roi[1], "xstart": roi[2], "xend": roi[3]}, indent = 4))
        except:
            raise Exception("Could not write roi.")
        return

    def _loadBins(self, binlist):
        """
        :param bin: The bin to load
        :type bin: list or file
        """

        if isinstance(binlist, list):
            return binlist
        else:
            if os.path.isfile(binlist):
                try:
                    with open(binlist, "r") as rh:
                        return json.load(rh)
                except:
                    raise Exception("Bin list not valid json!")
            else:
                raise Exception("Bin file does not exist.")
        return

    def _loadResource(self, resource):
        """
        :param resource: The resource to load.
        :type resource: numpy.ndarray or file
        :return: The image
        :rtype: numpy.ndarray
        :raises OSError: if the input path does not exist.

        Loads a resource, either a path to an image or a raw numpy array.
        """
        if isinstance(resource, np.ndarray):
            return ("unknown", resource.copy())
        else:
            if resource in self.states:
                return (resource, self.states[resource].copy())
            elif os.path.isfile(resource):
                image = cv2.imread(resource)
                if image is not None:
                    return (os.path.basename(resource), image)
                else:
                    if self.conn:
                        self.conn.execute("update images set error =? where pegasusid = ?", ("Load Error, input is not an image.", self.dbid))
                        self.conn.commit()
                    raise Exception("Input is not an image.")
            else:
                if self.conn:
                    self.conn.execute("update images set error = ? where pegasusid = ?", ("Load Error, input path doesn't exist or specified resource is not a saved state.", self.dbid))
                    self.conn.commit()
                raise Exception("Input path to resource does not exist.")
        return

    def _getMergedContour(self):
        """
        Assumes that image is already binary.
        """
        if self._isColor():
            binary = cv2.inRange(self.image.copy(), np.array([1, 1, 1], np.uint8), np.array([255, 255, 255], np.uint8))
        else:
            binary = self.image.copy()
        contours,hierarchy = cv2.findContours(binary, cv2.RETR_EXTERNAL, 2)
        merged = []
        for cnt in contours:
            for point in cnt:
                merged.append([point[0][0], point[0][1]])
        return np.array(merged, dtype=np.int32)

    def drawContours(self):
        """
        A helper function that draws all detected contours in the image onto the image.
        """
        if self._isColor():
            binary = cv2.inRange(self.image.copy(), np.array([1, 1, 1], np.uint8), np.array([255, 255, 255], np.uint8))
        else:
            binary = self.image.copy()
        contours, hierarchy = cv2.findContours(binary, cv2.RETR_EXTERNAL, 2)
        for cnt in contours:
            cv2.drawContours(self.image, [cnt], 0, (random.randint(127, 255), random.randint(127, 255), random.randint(127, 255)), -1)
        return

    def _colorHistogram(self):
        """
        :return: A list of histograms, corresponding to R, G, B.
        :rtype: List of numpy arrays.

        Calculates a normalized colorHistogram of the current image.
        The intensity is normalized between 0 and 255.
        """
        returnhist = []

        for ch in range(0, 3):
            hist_item = cv2.calcHist([self.image], [ch], None, [256], [1,255])
            cv2.normalize(hist_item, hist_item, 0, 255, cv2.NORM_MINMAX)
            hist = np.int32(np.around(hist_item))
            returnhist.append(hist)
        return returnhist

    def _isColor(self, image = None):
        image = self.image if image is None else image
        return len(image.shape) == 3

    def save(self, name):
        """
        :param name: The name to save the image under.
        :type name: str OR any hashable type.

        This function saves the current image in the 'states' variable under
        the specified name.  It can then be reloaded using the :py:meth:`~ih.imgproc.Image.restore`
        method.
        """
        self.states[name] = self.image.copy()
        return

    def restore(self, name):
        """
        :param name: The name the image is saved under.
        :type name: str OR any hashable type.

        Reloads a previously saved image from the 'states' variable.
        """
        if name in self.states:
            self.image = self.states[name].copy()
            self.y = self.image.shape[0]
            self.x = self.image.shape[1]
        else:
            print "Invalid state specified."
        return

    def list(self):
        """
        Lists all saved states.
        """
        for state in self.states:
            print state
        return

    def destroy(self):
        """
        Destroys all currently open windows.
        """
        cv2.destroyAllWindows()
        return

    def wait(self):
        """
        Waits until a key is pressed, then destroys all windows and
        continues program execution.
        """
        cv2.waitKey(0)
        self.destroy()
        return

    def split(self, channel):
        """
        :param channel: The channel to select from the image.
        :type channel: int

        This function is a wrapper to the OpenCV function
        `split <http://docs.opencv.org/2.4/modules/core/doc/operations_on_arrays.html#split>`_.
        Splits an image into individually channels, and selects a single channel
        to be the resulting image (Remember, color images have channel order BGR).
        No validation is done on channel number, so it is possible to provide a
        channel number that does not exist.  For example, calling split on an
        bgr image with channel = 2 will extract the red channel from the image.
        """
        self.image = cv2.split(self.image)[channel]
        return

    def equalizeHist(self):
        """
        This function is a wrapper to the OpenCV function
        `equalizeHist <http://docs.opencv.org/2.4/modules/imgproc/doc/histograms.html#equalizehist>`_.
        This function equalizes the histogram of a grayscale image by stretching
        the minimum and maximum values to 0 and 255 respectively.
        If this is run on a color image it will be converted to gray scale first.
        """
        if self._isColor():
            self.image = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
        self.image = cv2.equalizeHist(self.image)
        return

    def equalizeColor(self):
        """
        This function calls the :py:meth:`~ih.imgproc.Image.equalizeHist` function
        on each individual channel of a color image, and then returns the merged
        result.
        """
        if self._isColor():
            b, g, r = cv2.split(self.image)
            b = cv2.equalizeHist(b)
            g = cv2.equalizeHist(g)
            r = cv2.equalizeHist(r)
            self.image = cv2.merge([b, g, r])
        return

    def show(self, title = None, state = None):
        """
        :param title: The title to give the display window, if left blank one will be created.
        :type title: str
        :return: None

        Displays the image in a window.  Utilizes the :py:meth:`~ih.imgproc.Image.resize` function.
        If a title is not specified, the window will be named 'windowX' where X is the number of times
        show has been called.
        """
        cv2.imshow(title if title else "window " + str(self.window), self.resize(state))
        self.window += 1
        return

    def resizeSelf(self, scale = None, width = None, height = None):
        """
        :param scale: Value to scale image by.
        :type scale: float
        :param width: Target width of image.
        :type width: int
        :param height: Target height of image.
        :type height: int

        Resizes the current image.  If scale is set, it simply resizes the
        width and height of the image based on the scale.  If only one of width
        or height is set, it scales the other accordingly.  If both width
        and height are set, it scales the image to the exact size specified.
        """
        if scale or width or height:
            if scale:
                self.image = cv2.resize(self.image, (int(self.x * scale), int(self.y * scale)))
            elif width and height:
                self.image = cv2.resize(self.image, height, width)
            elif width:
                scale = float(width) / float(self.x)
                self.image = cv2.resize(self.image, (int(self.x * scale), int(self.y * scale)))
            elif height:
                scale = float(height) / float(self.y)
                self.image = cv2.resize(self.image, (int(self.x * scale), int(self.y * scale)))
            self.y = self.image.shape[0]
            self.x = self.image.shape[1]
        return

    def addWeighted(self, image, weight1, weight2):
        """
        :param image: The image to add.
        :type image: str of np.ndarray
        :param weight1: The weight to apply to the current image.
        :type weight1: float
        :param weight2: The weight to apply to the additional image.
        :type weight2: float

        This function is a wrapper to the OpenCV function
        `addWeighted <http://docs.opencv.org/2.4/modules/core/doc/operations_on_arrays.html#addweighted>`_.
        This function adds/blends an additional image to the current based on the provided
        weights.  Both positive and negative weights can be used.
        """
        self.image = cv2.addWeighted(self.image, weight1, self._loadResource(image)[1], weight2, 0)
        return

    def resize(self, state = None):
        """
        If the image is larger than conf.maxArea, resize its total area down to conf.maxArea.
        This function is primarily used for viewing purposes, and as such, it does not resize
        the base image, but creates a copy to resize instead.
        """
        if (state):
          im = self.states[state].copy()
          if (im.shape[0] * im.shape[1] > conf.maxArea):
              scale = 1 / math.sqrt((im.shape[1] * im.shape[0]) / conf.maxArea)
              return cv2.resize(im, (int(im.shape[1] * scale), int(im.shape[0] * scale)))
        elif (self.image.shape[0] * self.image.shape[1] > conf.maxArea):
            scale = 1 / math.sqrt((self.image.shape[1] * self.image.shape[0]) / conf.maxArea)
            return cv2.resize(self.image.copy(), (int(self.x*scale), int(self.y*scale)))
        else:
            return self.image

    def write(self, name = None):
        """
        Writes the current image to the given output directory, with the given name.
        """
        writename = self.writename if not name else name
        cv2.imwrite(self.outputdir + "/" + writename, self.image)
        return

    def convertColor(self, intype, outtype):
        """
        :param intype: The input image type
        :type intype: str
        :param outtype: The output image type
        :type outtype: str
        :return: The converted image.
        :rtype: numpy.ndarray
        :raises: KeyError

        Converts the given image between color spaces, based on the given types.
        Supported types are: bgr, gray, hsv, lab, and ycrcb.  Note, you cannot
        restore color to a gray image with this function, for that you must use
        bitwise_and with an appropriate mask + image.
        """
        if intype in conf.colors:
            if outtype in conf.colors[intype]:
                for code in conf.colors[intype][outtype]:
                    self.image = cv2.cvtColor(self.image, code)
            else:
                raise KeyError(outtype + " is not a valid output type for the input type: " + intype)
        else:
            raise KeyError(intype + " is not a valid image type.")
        return

    def threshold(self, thresh, max = 255, type = "binary"):
        """
        :param thresh: Threshold value.
        :type thresh: int
        :param max: Write value for binary threshold.
        :type max: int
        :param type: Threhsold type.
        :type type: str
        :return: The thresholded image.
        :rtype: numpy.ndarray
        :raises KeyError: if the specified threshold type doesn't exist.

        Thresholds the image based on the given type.  The image must be
        grayscale to be thresholded.  If the image is of type 'bgr' it is
        automatically converted to grayscale before thresholding.
        Supported types are: binary, inverse, truncate, tozero, and otsu.
        """
        if self._isColor():
            self.convertColor("bgr", "gray")
        if type in conf.thresholds:
            self.image = cv2.threshold(self.image, thresh, max, conf.thresholds[type])[1]
        else:
            raise KeyError(type + " is not a valid threshold type.")
        return

    def rotateColor(self, color):
        """
        :param color: Color shift to perform.  Should be [b, g, r].
        :type color: list

        Shifts the entire color of the image based on the values in
        the color list.
        """
        b, g, r = cv2.split(self.image.astype(np.uint16))
        np.clip(np.add(b, color[0]), 0, 255, out = b)
        np.clip(np.add(g, color[1]), 0, 255, out = g)
        np.clip(np.add(r, color[2]), 0, 255, out = r)
        self.image = cv2.merge([b, g, r]).astype(np.uint8)
        return

    def knn(self, k, labels, remove = []):
        """
        :param k: Number of nearest neighbors to use
        :type k: int
        :param labels: Path to label file.  More info below
        :type labels: file
        :param remove: Labels to remove from final image.
        :type remove: list

        This function is a wrapper to the OpenCV function `KNearest <http://docs.opencv.org/modules/ml/doc/k_nearest_neighbors.html>`_.
        The label file should contain training data in json format, using the label name of keys, and all
        the colors matching that label as an array value.  Each color should be a list of 3 values, in BGR order.
        That is:

        .. code-block:: python

            {
            "plant": [
                [234, 125, 100],
                [100, 100, 100]
            ],
            "pot": [
                ...
            }

        When creating your label file, make sure to use helpful names.  Calling each set of colors "label1", "label2" e.t.c
        provides no meaningful information.  The remove list is the list of matched labels to remove from the final image.
        The names to remove should match the names in your label file exactly. For example, let's say you have the labels
        "plant", "pot", "track", and "background" defined, and you only want to keep pixels that match the "plant" label.
        Your remove list should be specified as ["pot", "track", "background"].
        """
        if (os.path.isfile(labels)):
            with open(labels, "r") as rh:
                data = json.load(rh)
                labelMap = []
                trainData = []
                response = []
                for index,key in enumerate(data.keys()):
                     labelMap.append(key)
                     for color in data[key]:
                         trainData.append(color)
                         response.append(index)
                trainData = np.array(trainData, dtype = np.float32)
                response = np.array(response)
                knn = cv2.KNearest()
                knn.train(trainData, response)
                fim = self.image.copy().reshape((-1, 3)).astype(np.float32)
                ret, results, neighbors, dist = knn.find_nearest(fim, k)
                ires = np.in1d(results.ravel(), [i for i,x in enumerate(labelMap) if x not in remove])
                final = cv2.cvtColor(np.where(ires, 255, 0).astype(np.uint8).reshape((self.y, self.x)).astype(np.uint8), cv2.COLOR_GRAY2BGR)
                self.bitwise_and(final)
        else:
            print "Cannot find label file."
        return


    def kmeans(self, k, criteria, maxiter = 10, accuracy = 1.0, attempts = 10, flags = "random", labels = None):
        """
        :param k: Number of colors in final image.
        :type k: int
        :param criteria: Determination of how the algorithm stops execution.  Should be one of 'accuracy', 'iteration', or 'either'.
        :type criteria: str
        :param maxiter: Maximum number of iterations of the algorithm.
        :type maxiter: int
        :param accuracy: Minimum accuracy before algorithm finishes executing.
        :type accuracy: float
        :param attempts: Number of times the algorithm is executed using different initial guesses.
        :type attempts: int
        :param flags: How to determine initial centers should be either 'random' or 'pp'.
        :type flags: str

        This function is a wrapper to the OpenCV function `kmeans <http://docs.opencv.org/modules/core/doc/clustering.html>`_
        Adjusts the colors in the image to find the most compact 'central' colors.  The amount of colors
        in the resulting image is the specified value 'k'.  The colors are chosen based upon the minimum
        amount of adjustment in the image necessary.  The criteria parameter determines when the algorithm
        stops.  If 'accuracy' is specified, the algorithm runs until the specified accuracy is reached.  If 'iteration'
        is specified, the algorithm runs the specified number of iterations.  If 'either' is specified, the algorithm
        runs until one of the conditions is satisfied.  The flags parameter determines the initial central colors,
        and should be either 'random' -- to generate a random initial guess -- or 'pp' to use center initialization by Arthur and Vassilvitskii.
        """
        if flags in conf.centers:
            if criteria in conf.ktermination:
                reshaped = self.image.reshape((-1,3))
                reshaped = np.float32(reshaped)
                ret, label, center = cv2.kmeans(reshaped, k, (conf.ktermination[criteria], maxiter, accuracy), attempts, conf.centers[flags], bestLabels = labels)
                center = np.uint8(center)
                res = center[label.flatten()]
                self.image = res.reshape((self.image.shape))
            else:
                raise KeyError(criteria + " is not a valid termination type.  Should be one of 'accuracy', 'iteration', or 'either'")
        else:
            raise KeyError(flags + " is not a valid center type.  Should be either 'random' or 'pp'.")
        return


    def meanshift(self, spatial_radius, range_radius, min_density):
        """
        :param spatial_radius: Spatial Radius
        :type spatial_radius: int
        :param range_radius: Range Radius.
        :type range_radius: int
        :param min_density: Minimum Density.
        :type min_density: int
        :return: The mean-shifted image.
        :rtype: numpy.ndarray

        Segments the image into clusters based on nearest neighbors.  This function
        is a wrapper to the `pymeanshift <https://code.google.com/p/pymeanshift/>`_
        module.  For details on the algorithm itself: `Mean shift: A robust approach toward feature space analysis <http://dx.doi.org/10.1109/34.1000236>`_.
        """
        (self.image, labels_image, number_regions) = pms.segment(self.image, spatial_radius = spatial_radius, range_radius = range_radius, min_density = min_density)
        return

    def adaptiveThreshold(self, value, adaptiveType, thresholdType, blockSize, C):
        """
        :param value: Intensity value for the pixels based on the thresholding conditions.
        :type param: int
        :param adaptiveType: Adaptive algorithm to use, should be either 'mean' or 'gaussian'.
        :type adaptiveType: str
        :param thresholdType: Threshold type, should be either 'binary' or 'inverse'.
        :type thresholdType: str
        :param blockSize: The window size to consider while thresholding, should only be an odd number.
        :type blockSize: int
        :param C: A constant subtracted from the calculated mean in each window.
        :type C: int

        Thresholds an image by considering the image in several different windows instead of the image
        as a whole.  This function is a wrapper to the OpenCV function `adaptiveThreshold <http://docs.opencv.org/modules/imgproc/doc/miscellaneous_transformations.html#adaptivethreshold>`_.
        Specifying 'mean' for adaptiveType calculates a simple mean of the area, wheras specifying 'gaussian' calculates a weighted sum
        based upon a `Gaussian Kernel <http://docs.opencv.org/modules/imgproc/doc/filtering.html#Mat getGaussianKernel(int ksize, double sigma, int ktype)>`_.
        Specifying 'binary' for thresholdType means that a particular intensity value must beat the threshold to be kept, whereas
        specifying 'inverse' means that a particular intensity value must lose to the threshold to be kept.
        Similar to a normal thresholding function, the image must be converted to grayscale first.  This can be done using the
        :meth:`~ih.imgproc.Image.convertColor` function, however, if your image is of type 'bgr', this is handled automatically.
        """
        if self._isColor():
            self.convertColor("bgr", "gray")
        if adaptiveType in conf.adaptives:
            if thresholdType == "binary" or thresholdType == "inverse":
                self.image = cv2.adaptiveThreshold(self.image, value, conf.adaptives[adaptiveType], conf.thresholds[thresholdType], blockSize, C)
            else:
                raise Exception("Threshold type: " + thresholdType + " must be either binary or inverse.")
        else:
            raise Exception("Adaptive type: " + adaptiveType + " is not a valid adaptive threshold type, should be either 'mean' or 'gaussian'")
        return

    def blur(self, ksize, anchor = (-1, -1), borderType = "default"):
        """
        :param ksize: The size of the kernel represented by a tuple (width, height).  Both numbers should be odd and positive.
        :type ksize: tuple
        :param anchor: The anchor point for filtering.  Default is (-1, -1) which is the center of the kernel.
        :type anchor: tuple
        :param borderType: The type of border mode used to extrapolate pixels outside the image.
        :type borderType: str

        Smoothes an image using the normalized box filter.  This function is a wrapper to the OpenCV function
        `blur <http://docs.opencv.org/modules/imgproc/doc/filtering.html#blur>`_.  Increasing the kernel size increase
        the window considered when applying a blur.  The anchor by default is the center of the kernel,
        however you can alter the anchor to consider different areas of the kernel.  When blurring on the edge
        of the image, values for pixels that would be outside of the image are extrapolated.  The method
        of extrapolation depends on the specified 'borderType', and can be one of 'default', 'constant',
        'reflect', or 'replicate'.
        """
        if borderType in conf.borders:
            self.image = cv2.blur(self.image, ksize, anchor = anchor, borderType = conf.borders[borderType])
        else:
            raise Exception("Invalid border type, should be one of: " + ",".join(conf.borders.keys()) + ".")
        return

    def medianBlur(self, ksize):
        """
        :param ksize: The size of the kernel (ksize x ksize).  Should be odd and positive.
        :type ksize: int

        This function smoothes an image using the median filter.  The kernel is set to size (ksize, ksize).
        The anchor position is assumed to be the center.  This function is a wrapper to the opencv function
        `medianBlur <http://docs.opencv.org/modules/imgproc/doc/filtering.html#medianBlur>`_.
        """
        self.image = cv2.medianBlur(self.image, ksize)
        return

    def gaussianBlur(self, ksize, sigmaX = 0, sigmaY = 0, borderType = "default", roi = None):
        """
        :param ksize: The size of the kernel represented by a tuple (width, height).  Both numers should be odd and positive.
        :type ksize: tuple
        :param sigmaX: The standard deviation in the x direction.  If 0, the value is calculated based on the kernel size.
        :type sigmaX: float
        :param sigmaY: The standard deviation in the y direction.  If 0, the value is equal to sigmaX.
        :type sigmaY: float
        :param borderType: The type of border mode used to extrapolate pixels outside the image.
        :type borderType: str

        This function blurs an image based on a Gaussian kernel.  When blurring on the edge
        of the image, values for pixels that would be outside of the image are extrapolated.  The method
        of extrapolation depends on the specified 'borderType', and can be one of 'default', 'constant',
        'reflect', or 'replicate'.  This function is a wrapper to the OpenCV function `GaussianBlur <http://docs.opencv.org/modules/imgproc/doc/filtering.html#gaussianblur>`_.
        """
        if borderType in conf.borders:
            sigmaY = sigmaX if sigmaY == 0 else sigmaY
            roi = self._loadROI(roi)
            ystart, yend, xstart, xend = roi
            self.image[ystart:yend, xstart:xend] = cv2.GaussianBlur(self.image[ystart:yend, xstart:xend], ksize, sigmaX, sigmaY, borderType = conf.borders[borderType])
        else:
            raise Exception("Invalid border type, should be one of: " + ",".join(conf.borders.keys()) + ".")
        return

    def normalizeByIntensity(self):
        """
        Normalizes each channel of the pixel by its intensity.  For each pixel, the intensity is defined as
        :math:`I = R + G + B`, where :math:`R,G,B` are the color values for that pixel.  We calculate new color values by
        multiplying the original number by 255, and dividing by the intensity, that is, :math:`r = \\frac{255 \\cdot R}{I}
        , g = \\frac{255 \\cdot G}{I}, b = \\frac{255 \\cdot B}{I}`.
        """
        f = self.image.astype(float)
        combined = np.add(np.add(f[:,:,0], f[:,:,1]), f[:,:,2])
        scaled = np.multiply(f, [255])
        self.image = np.divide(scaled, combined[:,:,None]).astype(np.uint8)
        return

    def morphology(self, morphType, ktype, ksize, anchor = (-1, -1), iterations = 1, borderType = "default"):
        """
        :param morphType: The type of morphology to perform.  Should be dilate, erode, open, close, gradient, tophat, or blackhat.
        :type morphType: str
        :param ktype: the type of the kernel, should be rect, ellipse, or cross.
        :type ktype: str
        :param ksize: The size of the kernel represented by a tuple (width, height).  Both numbers should be odd and positive.
        :type ksize: tuple
        :param anchor: The anchor point for filtering.  Default is (-1, -1) which is the center of the kernel.
        :type anchor: tuple
        :param iterations: The number of times to perform the specified morphology.
        :type iterations: int
        :param borderType: The type of border mode used to extrapolate pixels outside the image.
        :type borderType: str

        This function performs morphological operations based on the inputted values. This function is
        a wrapper to the OpenCv function `morphologyEx <http://docs.opencv.org/modules/imgproc/doc/filtering.html#morphologyex>`_. When performing the morphology on the edges
        of the image, values for pixels that would be outside of the image are extrapolated.  The method
        of extrapolation depends on the specified 'borderType', and can be one of 'default', 'constant',
        'reflect', or 'replicate'.
        """
        if morphType in conf.morph:
            if ktype in conf.kernels:
                if borderType in conf.borders:
                    kernel = cv2.getStructuringElement(conf.kernels[ktype], ksize, anchor)
                    self.image = cv2.morphologyEx(self.image, conf.morph[morphType], kernel, anchor = anchor, iterations = iterations, borderType = conf.borders[borderType])
                else:
                    raise Exception("Invalid border type, should be one of: " + ",".join(conf.borders.keys()) + ".")
            else:
                raise Exception("Invalid kernel type, should be one of: " + ",".join(conf.kernels.keys()) + ".")
        else:
            raise Exception("Invalid morphology type, should be one of: " + ",".join(conf.morph.keys()) + ".")

    def _findSeed(self, seedMask):
        bname, binary = self._loadResource(seedMask)
        if self._isColor(binary):
            binary = cv2.cvtColor(binary, cv2.COLOR_BGR2GRAY)
        contours, hierarchy = cv2.findContours(binary, cv2.RETR_EXTERNAL, 2)
        size = 0
        select = 0
        for cnt in contours:
            if cv2.contourArea(cnt) > size:
                select = cnt
                size = cv2.contourArea(cnt)
        return tuple(select[0][0])

    def floodFill(self, mask, low, high, writeColor = (255, 255, 255), connectivity = 4, fixed = False, seed = (0,0), findSeed = False, seedMask = None, binary = False):
        """
        :param mask: A binary image corresponding to the area you don't want to fill.
        :type mask: str or np.ndarray
        :param seed: The beginning point to use for filling.
        :type seed: Tuple (x, y)
        :param low: Maximal lower brightness/color difference between the currently observed pixel and one of its neighbors belonging to the component, or a seed pixel being added to the component.
        :type low: Tuple (b, g, r) or (i,)
        :param high: Maximal upper brightness/color difference between the currently observed pixel and one of its neighbors belonging to the component, or a seed pixel being added to the component.
        :type high: Tuple (b, g, r) or (i,)
        :param writeColor: The color to write to the filled region.  Default (255, 255, 255).
        :type writeColor: tuple (b, g, r) or (i,)
        :param connectivity: The number of neighboring pixels to consider for the flooding operation.  Should be 4 or 8.
        :type connectivity: int
        :param fixed: If True, calculates color differences relative to the seed.
        :type fixed: boolean
        :param findSeed: If True, picks a seed point based on contours in the seedMask image.
        :type findSeed: boolean
        :param seedMask: Binary image to select seed from.
        :type seedMask: str or np.ndarray
        :param binary: Specify if input image is binary.
        :type binary: boolean

        This function is a wrapper to the OpenCV function `floodFill <http://docs.opencv.org/2.4/modules/imgproc/doc/miscellaneous_transformations.html#floodfill>`_.
        This function floods the region of an image based on calculated color differences from neighbors or from the seed.  When flooding a binary
        image all input color tuples should have 1 value instead of 3.
        """
        print low,high,writeColor
        mname, mask = self._loadResource(mask)
        if self._isColor(mask):
            mask = cv2.cvtColor(mask, cv2.COLOR_BGR2GRAY)
        if binary and self._isColor():
            self.convertColor("bgr", "gray")
        # Mask is required to be 2 pixels wider and taller than the image
        adjmask = np.zeros((self.y + 2, self.x + 2), np.uint8)
        adjmask[1:1+self.y, 1:1+self.x] = mask
        channels = 3 if len(self.image.shape) == 3 else 1
        if len(low) == channels:
            if len(high) == channels:
                if len(writeColor) == channels:
                    if connectivity == 4 or connectivity == 8:
                        if findSeed and seedMask:
                            seed = self._findSeed(seedMask)
                        if fixed:
                            cv2.floodFill(self.image, adjmask, seed, writeColor, low, high, connectivity | cv2.FLOODFILL_FIXED_RANGE)
                        else:
                            cv2.floodFill(self.image, adjmask, seed, writeColor, low, high, connectivity)
                    else:
                        raise Exception("Invalid value for connectivity, should be either 4 or 8.")
                else:
                    raise Exception("Incorrect number of values for write color.  Number of values should match input image channels (%s)" % (channels,))
            else:
                raise Exception("Incorrect number of values for high difference.  Number of values should match input image channels (%s)" % (channels,))
        else:
            raise Exception("Incorrect number of values for low difference.  Number of values should match input image channels (%s)" % (channels,))
        return

    def fill(self, roi, color):
        """
        :param roi: A list corresponding to the area of the image you want.  List should be of the form [ystart, yend, xstart, xend]
        :type roi: list or roi file
        :param color: A list corresponding to BGR values to fill the corresponding area with.
        :type color: list

        Fills the given roi with the given color.
        """
        roi = self._loadROI(roi)
        ystart, yend, xstart, xend = roi
        self.image[ystart:yend, xstart:xend] = color
        return



    def crop(self, roi, resize = False):
        """
        :param roi: A list corresponding to the area of the image you want.  List should be of the form [ystart, yend, xstart, xend]
        :type roi: list or roi file
        :param resize: If True, actually adjusts the size of the image, otherwise just draws over the part of the image not in the roi.
        :type resize: bool

        This function crops the image based on the given roi [ystart, yend, xstart, xend].  There are two crop options,
        by default, the function doesn't actually resize the image.  Instead, it sets each pixel not in the roi to black.
        If resize is set to True, the function will actually crop the image down to the roi.
        """
        roi = self._loadROI(roi)
        ystart, yend, xstart, xend = roi
        if (resize):
            self.image = self.image[ystart: yend, xstart: xend]
            self.x = self.image.shape[1]
            self.y = self.image.shape[0]
        else:
            maxx = self.x
            maxy = self.y
            off = [0, 0, 0] if self._isColor() else [0]
            self.image[0:ystart, 0:maxx] = off
            self.image[yend:maxy, 0:maxx] = off
            self.image[0:maxy, 0:xstart] = off
            self.image[0:maxy, xend:maxx] = off
        return

    def mask(self):
        """
        This function convers the image to a color mask by performing the following operations:

        1. convertColor("bgr", "gray")
        2. threshold(0)
        3. convertColor("gray", "bgr")
        """
        self.convertColor("bgr", "gray")
        self.threshold(0)
        self.convertColor("gray", "bgr")
        return

    def contourChop(self, binary, basemin = 100):
        """
        :param binary: The binary image to find contours of.
        :type binary: str of np.ndarray
        :param basemin: The minimum area a contour must have to be considered part of the foreground.
        :type basemin: int

        This function works very similiarly to the :py:meth:`~ih.imgproc.Image.contourCut`
        function, except that this function does not crop the image, but removes
        all contours that fall below the threshold.
        """

        bname, binary = self._loadResource(binary)
        if self._isColor(binary):
            binary = cv2.cvtColor(binary, cv2.COLOR_BGR2GRAY)
        contours = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[0]
        for cnt in contours:
            if (cv2.contourArea(cnt) < basemin):
                cv2.drawContours(self.image, [cnt], -1, (0, 0, 0), -1)
        return

    def getBounds(self):
        """
        :return: The bounding box of the image.
        :rtype: list

        This function finds the bounding box of all contours in the image, and
        returns a list of the form [miny, maxy, minx, maxx]
        """
        binary = self.image.copy()
        if self._isColor(binary):
            binary = cv2.cvtColor(binary, cv2.COLOR_BGR2GRAY)
        contours = cv2.findContours(binary, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)[0]
        minx = binary.shape[1]
        miny = binary.shape[0]
        maxx = 0
        maxy = 0
        for cnt in contours:
            x,y,w,h = cv2.boundingRect(cnt)
            if (x < minx):
                minx = x
            if (y < miny):
                miny = y
            if (x + w > maxx):
                maxx = x + w
            if (y + h > maxy):
                maxy = y + h
        return [miny, maxy, minx, maxx]

    def contourCut(self, binary, basemin = 100, padding = [0, 0, 0, 0], resize = False, returnBound = False, roiwrite = "roi.json"):
        """
        :param binary: The binary image to find contours of.
        :type binary: str or np.ndarray
        :param basemin: The minimum area a contour must have to be considered part of the foreground.
        :type basemin: int
        :param padding: Padding add to all sides of the final roi.
        :type padding: int
        :param returnBound: If set, instead of cropping the image, simply write the detected roi.
        :type returnBound: bool
        :param resize: Whether or not to resize the image.
        :type resize: bool

        This function crops an image based on the size of detected contours in the image --
        clusters of pixels in the image.  The image is cropped such that all contours
        that are greater than the specified area are included in the final output image.
        image is cropped such that all contours that are greater than the specified area are
        included in the final output image.  If returnBound is set, instead of actually
        cropping the image, the detected roi is written to a file instead.  Otherwise,
        the detected roi is passed into the :py:meth:`~ih.imgproc.Image.crop` function,
        with the given resize value.  This function is useful for getting accurate
        height and width of a specific plant, as well as removing outlying clusters
        of non-important pixels.
        """
        bname, binary = self._loadResource(binary)
        if self._isColor(binary):
            binary = cv2.cvtColor(binary, cv2.COLOR_BGR2GRAY)
        contours = cv2.findContours(binary, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)[0]
        minx = binary.shape[1]
        miny = binary.shape[0]
        maxx = 0
        maxy = 0
        for cnt in contours:
            x,y,w,h = cv2.boundingRect(cnt)
            if (basemin < cv2.contourArea(cnt)):
                if (x < minx):
                    minx = x
                if (y < miny):
                    miny = y
                if (x + w > maxx):
                    maxx = x + w
                if (y + h > maxy):
                    maxy = y + h
        roi = [0 if miny - padding[0] < 0 else miny - padding[0], binary.shape[0] if maxy + padding[1] > binary.shape[0] else maxy + padding[1], 0 if minx - padding[2] < 0 else minx - padding[2], binary.shape[1] if maxx + padding[3] > binary.shape[1] else maxx + padding[3]]
        if returnBound:
            self._writeROI(roi, roiwrite)
        self.crop(roi, resize)
        return

    def edges(self, threshold1, threshold2, apertureSize = 3, L2gradient = False):
        """
        :param threshold1: First threshold for the hysteresis procedure.
        :type threshold1: int
        :param threshold2: Second threshold for the hysteresis procedure.
        :type threshold2: int
        :param apertureSize: aperture size used for the Sobel operator.  Must be odd, postive, and less than 8.
        :type apertureSize: int
        :L2gradient: Used to calculate Image gradient magnitude, if true then :math:`L = \sqrt{(dI/dx)^2 + (dI/dy)^2}`, if false then :math:`L = dI/dx + dI/dy`.
        :type L2gradient: bool

        This function calculates the edges of an image using the Canny edge detection algorithm using the Sobel operator.  This function is a wrapper to the OpenCV function `Canny <http://docs.opencv.org/modules/imgproc/doc/feature_detection.html#canny>`_.
        """
        self.image = cv2.Canny(self.image, threshold1, threshold2, apertureSize = apertureSize, L2gradient = L2gradient)
        return

    def colorFilter(self, logic, roi = None):
        """
        :param logic: The logic you want to run on the image.
        :type logic: str
        :param roi: The roi you want to apply the filter to
        :type roi: list or roi file

        This function applies a color filter defined by the input logic, to a
        targeted region defined by the input roi. The logic string itself is fairly complicated.
        The string supports the following characters: '+', '-', '*', '/', '>', '>=',
        '==', '<', '<=', 'and', 'or', '(', ')', 'r', 'g', 'b', 'max', and 'min' as well as any numeric
        value.  The logic string itself must be well formed -- each
        operation, arg1 operator arg2, must be surrounded by parenthesis, and the entire statement
        must be surrounded by parenthesis.  For example,
        if you want to check the intensity of the pixel, your logic string would be:
        '(((r + g) + b) < 100)'.  This string in particular will only keep pixels whose
        intensity is less than 100.  Similar rules apply for 'and' and 'or' operators.
        Let's say we only want to keep pixels whose intensity is less than 100, OR both
        the red and blue channels are greater than 150, the logic string would be:
        '((((r + g) + b) < 100) or ((r > 150) and (b > 150)))'.  The more complex
        your logic is the harder it is to read, so you may want to consider breaking
        up complex filtering into multiple steps for readability.  Finally, despite
        the fact this function solves arbitrary logic, it is very fast.
        """
        filter = ColorFilter(logic)
        roi = self._loadROI(roi)
        self.image = filter.apply(self.image, roi)
        return

    def bitwise_not(self):
        """
        Inverts the image.  If the given image has multiple channels (i.e. is a color image) each channel is processed independently.
        """
        self.image = cv2.bitwise_not(self.image)
        return

    def bitwise_and(self, comp):
        """
        :param comp: The comparison image.
        :type comp: str or np.ndarray
        :return: The resulting mask.
        :rtype: numpy.ndarray

        Performs logical AND between the input image and the comp image.
        The comp input is very versatile, and can be one of three input types,
        an image, a path, or a saved state.  An image input is a raw numpy array,
        and this input type will be passed through to the function without modification.
        If a path is specified, ih attempts to load the file as an image, and pass it
        to the function.  Finally, the input is checked against the currently saved
        image states.  If it matches, the corresponding state is passed to the function.
        The function assumes that the two input images are of matching type --
        if they are not an error will be thrown.  By default, images loaded from a
        path are loaded as 'bgr' type images.
        For more information on states, see :py:meth:`~ih.imgproc.Image.save`.
        """
        self.image = cv2.bitwise_and(self.image, self._loadResource(comp)[1])
        return

    def bitwise_or(self, comp):
        """
        :param comp: The comparison image.
        :type comp: str or np.ndarray
        :return: The resulting mask.
        :rtype: numpy.ndarray

        Performs logical OR between the input image and the comp image.
        The comp input is very versatile, and can be one of three input types,
        an image, a path, or a saved state.  An image input is a raw numpy array,
        and this input type will be passed through to the function without modification.
        If a path is specified, ih attempts to load the file as an image, and pass it
        to the function.  Finally, the input is checked against the currently saved
        image states.  If it matches, the corresponding state is passed to the function.
        The function assumes that the two input images are of matching type --
        if they are not an error will be thrown.  By default, images loaded from a
        path are loaded as 'bgr' type images.
        For more information on states, see :py:meth:`~ih.imgproc.Image.save`.
        """
        self.image = cv2.bitwise_or(self.image, self._loadResource(comp)[1])
        return

    def bitwise_xor(self, comp):
        """
        :param comp: The comparison image.
        :type comp: str or np.ndarray
        :return: The resulting mask.
        :rtype: numpy.ndarray

        Performs exclusive logical OR between the input image and the comp image.
        The comp input is very versatile, and can be one of three input types,
        an image, a path, or a saved state.  An image input is a raw numpy array,
        and this input type will be passed through to the function without modification.
        If a path is specified, ih attempts to load the file as an image, and pass it
        to the function.  Finally, the input is checked against the currently saved
        image states.  If it matches, the corresponding state is passed to the function.
        The function assumes that the two input images are of matching type --
        if they are not an error will be thrown.  By default, images loaded from a
        path are loaded as 'bgr' type images.
        For more information on states, see :py:meth:`~ih.imgproc.Image.save`.
        """
        self.image = cv2.bitwise_xor(self.image, self._loadResource(comp)[1])
        return

    def extractLabels(self, fname, meta_labels):
        """
        :param fname: The output file name to write.
        :type fname: str
        :param meta_labels: A dictionary containing required meta info.
        :type meta_labels: dict

        Meta labels should look like:

        .. code-block:: python

            meta_labels {
                "label_name": roi,
                "label_name2": roi
            }
        """
        data = {}
        for labelname in meta_labels:
            roi = self._loadROI(meta_labels[labelname])
            ystart, yend, xstart, xend = roi
            data[labelname] = [list(x.astype(int)) for x in np.reshape(self.image[ystart: yend, xstart: xend], ((yend - ystart) * (xend - xstart), 3))]
        print data
        with open(fname, "w") as wh:
            json.dump(data, wh)
        return

    def extractFinalPath(self):
        """
        This function writes the absolute path of the output file to the database.
        """
        if self.conn:
             finalpath = "/".join(os.path.abspath(self.input).split("/")[-6:])
             self._addColumn("outputPath")
             self.conn.execute("update images set outputPath=? where pegasusid=?", (finalpath, self.dbid))
             self.conn.commit()
        return

    def extractMoments(self):
        """
        :return: A dictionary corresponding to the different moments of the image.
        :rtype: dict

        Calculates the moments of the image, and returns a dicitonary based on them.
        Spatial moments are prefixed with 'm', central moments are prefixed with 'mu',
        and central normalized moments are prefixed with 'nu'.  This function
        is a wrapper to the OpenCV function `moments <http://docs.opencv.org/modules/imgproc/doc/structural_analysis_and_shape_descriptors.html#moments>`_.
        """
        moments = cv2.moments(cv2.inRange(self.image, np.array([1, 1, 1], np.uint8), np.array([255, 255, 255], np.uint8)))
        if self.conn:
            for id in moments:
                self._addColumn(id)
                self.conn.execute("update images set " + id + "=? where pegasusid=?", (moments[id], self.dbid))
            self.conn.commit()
            return
        else:
            return moments

    def extractDimsFromROI(self, roi):
        """
        :param roi: The roi to calculate height from.
        :type roi: list or roi file

        :return: A list corresponding to the calculated height and width of the image.
        :rtype: list

        Returns a list with the follwoing form: [height, width].  This functions differs
        from the :py:meth:`~ih.imgproc.Image.extractDimensions` in the way that height
        is calculated.  Rather than calculating the total height of the image,
        the height is calculated from the top of the given ROI.
        """

        pot = self._loadROI(roi)
        plant = self.getBounds()
        height = pot[0] - plant[0]
        width = plant[3] - plant[2]
        if self.conn:
            self._addColumn("height")
            self._addColumn("width")
            self.conn.execute("update images set height=?,width=? where pegasusid=?", (height, width, self.dbid))
            self.conn.commit()
            return
        else:
            return [height, self.x]


    def extractDimensions(self):
        """
        :return: A list corresponding to the height and width of the image.
        :rtype: list

        Returns a list with the following form: [height, width]
        """
        bounds = self.getBounds()
        height = bounds[1] - bounds[0]
        width = bounds[3] - bounds[2]
        if self.conn:
            self._addColumn("height")
            self._addColumn("width")
            self.conn.execute("update images set height=?,width=? where pegasusid=?", (height, width, self.dbid))
            self.conn.commit()
            return
        else:
            return [height, width]

    def extractMinEnclosingCircle(self):
        """
        :return: The center, and radius of the minimum enclosing circle.
        :rtype: int

        Returns the center and radius of the minimum enclosing circle of all
        non-black pixels in the image.  The point of this function
        is not to threshold, so the contours are generated from
        all the pixels that fall into the range [1, 1, 1], [255, 255, 255].
        """
        circle = cv2.minEnclosingCircle(self._getMergedContour())
        if self.conn:
            self._addColumn("circle_centerx")
            self._addColumn("circle_centery")
            self._addColumn("circle_radius")
            self.conn.execute("update images set circle_centerx=?, circle_centery=?, circle_radius=? where pegasusid=?", (circle[0][0], circle[0][1], circle[1], self.dbid))
            self.conn.commit()
        else:
            return circle

    def extractConvexHull(self):
        """
        :return: The area of the convex hull.
        :rtype: int

        Returns the area of the convex hull around all non black pixels in the image.
        The point of this function is not to threshold, so the contours are generate from
        all the pixels that fall into the range [1, 1, 1], [255, 255, 255]
        """
        hull = cv2.contourArea(
                 cv2.approxPolyDP(
                    cv2.convexHull(
                        self._getMergedContour()
                    ), 0.001, True
                ))
        if self.conn:
            self._addColumn("convex_hull_area")
            self.conn.execute("update images set convex_hull_area=? where pegasusid=?", (hull, self.dbid))
            self.conn.commit()
        else:
            return hull

    def extractPixels(self):
        """
        :return: The number of non-black pixels in the image.
        :rtype: int

        Returns the number of non-black pixels in the image.  Creates
        a temporary binary image to do this.  The point of this function
        is not to threshold, so the binary image is created by all
        pixels that fall into the range [1, 1, 1], [255, 255, 255].
        """
        pixelCount = cv2.countNonZero(cv2.inRange(self.image, np.array([1, 1, 1], np.uint8), np.array([255, 255, 255], np.uint8)))
        if self.conn:
            self._addColumn("pixels")
            self.conn.execute("update images set pixels=? where pegasusid=?", (pixelCount, self.dbid))
            self.conn.commit()
            return
        else:
            return pixelCount

    def extractColorData(self, nonzero = True, returnhist = False):
        """
        :param nonzero: Whether or not to look at only nonzero pixelsself.  Default true.
        :type nonzero: bool
        :return: Mean & median for each channel.
        :rtype: list

        This function calculates a normalized histogram of each individual color channel of
        the image, and returns the mean & median of the histograms for the channels
        specified.  Because images are imported with the channels ordered as B,G,R,
        the output list is returned the same way.  The returned list always looks like
        this: [ [BlueMean, BlueMedian], [GreenMean, GreenMedian], [RedMean, RedMedian] ].
        Mean values always come before median values.  If nonzero is set to true (default)
        the function will only calculate mediapytn and means based on the non-black pixels.
        If you are connected to a database, the entire histogram is saved to the database,
        not just the mean and median.
        """
        hist = self._colorHistogram()
        if returnhist:
            return hist
        colors = [    [np.mean(hist[0][np.nonzero(hist[0])] if nonzero else hist[0]), np.median(hist[0][np.nonzero(hist[0])] if nonzero else hist[0])],
                    [np.mean(hist[1][np.nonzero(hist[1])] if nonzero else hist[1]), np.median(hist[1][np.nonzero(hist[1])] if nonzero else hist[1])],
                    [np.mean(hist[2][np.nonzero(hist[2])] if nonzero else hist[2]), np.median(hist[2][np.nonzero(hist[2])] if nonzero else hist[2])]
                ]
        if self.conn:
            self._addColumn("rmean")
            self._addColumn("rmed")
            self._addColumn("gmean")
            self._addColumn("gmed")
            self._addColumn("bmean")
            self._addColumn("bmed")
            query = "update images set rmean=?,rmed=?,gmean=?,gmed=?,bmean=?,bmed=?"
            values = [colors[2][0], colors[2][1], colors[1][0], colors[1][1], colors[0][0], colors[0][1]]
            for x,c in enumerate(["bhist", "ghist", "rhist"]):
                for i in range(0, 256):
                    self._addColumn(c + str(i))
                    query += "," + c + str(i) + "=?"
                    values.append(int(hist[x][i]))
            query += " where pegasusid=?"
            values.append(self.dbid)
            self.conn.execute(query, tuple(values))
            self.conn.commit()
            return
        else:
            return colors

    def extractColorChannels(self):
    	"""
    	This function extracts the total number of pixels of each color value
        for each channel.
    	"""
        b, g, r = cv2.split(self.image)
        bdata, gdata, rdata = [], [], []
        for i in range(0, 256):
            bdata.append(np.count_nonzero(np.where(b == i, True, False)))
            gdata.append(np.count_nonzero(np.where(g == i, True, False)))
            rdata.append(np.count_nonzero(np.where(r == i, True, False)))
        data = [bdata, gdata, rdata]
        if self.conn:
            query = "update images set "
            values = []
            for x,c in enumerate(["b", "g", "r"]):
                for i in range(0, 256):
                    self._addColumn(c + str(i))
                    if i == 0 and c == "b":
                        query += c + str(i) + "=?"
                    else:
                        query += "," + c + str(i) + "=?"
                    values.append(data[x][i])
            query += " where pegasusid=?"
            values.append(self.dbid)
            self.conn.execute(query, tuple(values))
            self.conn.commit()
            return
        else:
            return (bdata, gdata, rdata)

    def extractBins(self, binlist):
        """
        :param binlist: The specified bins (color ranges) to count.
        :type binlist: list
        :return: The number of pixels that fall in each bin.
        :rtype: list

        This function counts the number of pixels that fall into the range as
        specified by each bin.  This function expects the input to be a list of
        dictionaries as follows:

        .. code-block:: python

             binlist = [
                {"name": "bin1",
                 "min": [B, G, R],
                 "max": [B, G, R]
                },
                {"name": "bin2",
                ...
            ]

        Each range is defined by 6 values.  A minimum and maximum blue,
        green, and red value. The returned list is very similar to the
        input list, except a 'count' key is added to each dictionary:

        .. code-block:: python

            returnlist = [
                {"name": "bin1",
                "min": [B, G, R],
                "max": [B, G, R],
                "count": VALUE
                },
                ...
            ]

        Where 'VALUE' is the number of pixels that fall into the
        corresponding range.
        A list is used instead of a dictionary as the base structure
        to maintain order for writing to the output database.  When
        using this function within a workflow, the order you specify
        your bins is the order in which they will show up in the
        database, and the name you specify for you bin will be
        the column name in the database.
        """
        binlist = self._loadBins(binlist)
        for i in range(0, len(binlist)):
            binlist[i]["count"] = cv2.countNonZero(cv2.inRange(self.image, np.array(binlist[i]["min"], np.uint8), np.array(binlist[i]["max"], np.uint8)))
        if self.conn:
            for bin in binlist:
                self._addColumn(bin["name"])
                self.conn.execute("update images set " + bin["name"] + "=? where pegasusid=?", (bin["count"], self.dbid))
            self.conn.commit()
            return
        else:
            return binlist
