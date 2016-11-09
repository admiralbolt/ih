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
"""

import cv2

"""
A dictionary used to map input-output types to a cv2 color code
"""
colors = {
    "bgr": {
        "gray": [cv2.COLOR_BGR2GRAY],
        "hsv": [cv2.COLOR_BGR2HSV],
        "lab": [cv2.COLOR_BGR2LAB],
        "ycrcb": [cv2.COLOR_BGR2YCR_CB]
    },
    "gray": {
        "bgr": [cv2.COLOR_GRAY2BGR],
        "hsv": [cv2.COLOR_GRAY2BGR, cv2.COLOR_BGR2HSV],
        "lab": [cv2.COLOR_GRAY2BGR, cv2.COLOR_BGR2LAB],
        "ycrcb": [cv2.COLOR_GRAY2BGR, cv2.COLOR_BGR2YCR_CB]
    },
    "hsv": {
        "bgr": [cv2.COLOR_HSV2BGR],
        "gray": [cv2.COLOR_HSV2BGR, cv2.COLOR_BGR2GRAY],
        "lab": [cv2.COLOR_YCR_CB2BGR, cv2.COLOR_BGR2LAB],
        "ycrcb": [cv2.COLOR_YCR_CB2BGR, cv2.COLOR_BGR2YCR_CB]
    },
    "lab": {
        "bgr": [cv2.COLOR_LAB2BGR],
        "gray": [cv2.COLOR_LAB2BGR, cv2.COLOR_BGR2GRAY],
        "hsv": [cv2.COLOR_LAB2BGR, cv2.COLOR_BGR2HSV],
        "ycrcb": [cv2.COLOR_LAB2BGR, cv2.COLOR_BGR2YCR_CB]
    },
    "ycrcb": {
        "bgr": [cv2.COLOR_YCR_CB2BGR],
        "gray": [cv2.COLOR_YCR_CB2BGR, cv2.COLOR_BGR2GRAY],
        "hsv": [cv2.COLOR_YCR_CB2BGR, cv2.COLOR_BGR2HSV],
        "lab": [cv2.COLOR_YCR_CB2BGR, cv2.COLOR_BGR2LAB]
    }
}

"""
A dicitonary used to map threshold-types to cv2 threshold codes
"""
thresholds = {
    "binary": cv2.THRESH_BINARY,
    "inverse": cv2.THRESH_BINARY_INV,
    "truncate": cv2.THRESH_TRUNC,
    "tozero": cv2.THRESH_TOZERO,
    "otsu": cv2.THRESH_BINARY + cv2.THRESH_OTSU
}

"""
A dictionary used to map adaptive-types to cv2 adaptive codes
"""
adaptives = {
    "mean": cv2.ADAPTIVE_THRESH_MEAN_C,
    "gauss": cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
    "gaussian": cv2.ADAPTIVE_THRESH_GAUSSIAN_C
}


"""
A dictionary used to map border-types to cv2 border codes
"""
borders = {
    "default": cv2.BORDER_DEFAULT,
    "constant": cv2.BORDER_CONSTANT,
    "reflect": cv2.BORDER_REFLECT,
    "replicate": cv2.BORDER_REPLICATE,
    "transparent": cv2.BORDER_TRANSPARENT,
    "wrap": cv2.BORDER_WRAP
}

"""
A dictionary used to map morphology types to cv2 morphology codes
"""
morph = {
    "dilate": cv2.MORPH_DILATE,
    "erode": cv2.MORPH_ERODE,
    "open": cv2.MORPH_OPEN,
    "close": cv2.MORPH_CLOSE,
    "gradient": cv2.MORPH_GRADIENT,
    "tophat": cv2.MORPH_TOPHAT,
    "blackhat": cv2.MORPH_BLACKHAT
}

"""
A dictionary used to map kernel types to cv2 kernel codes
"""
kernels = {
    "rect": cv2.MORPH_RECT,
    "ellipse": cv2.MORPH_ELLIPSE,
    "cross": cv2.MORPH_CROSS
}

"""
A dictionary used to map center types to cv2 center codes
"""
centers = {
    "random": cv2.KMEANS_RANDOM_CENTERS,
    "pp": cv2.KMEANS_PP_CENTERS
}

"""
A dictionary used to map termination types to cv2 termination codes
"""
ktermination = {
    "accuracy": cv2.TERM_CRITERIA_EPS,
    "iteration": cv2.TERM_CRITERIA_MAX_ITER,
    "either": cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER
}

"""
Defines the maximum size of a displayed image in total pixels.
"""
maxArea = 360000

"""
Defines imtype mapping
"""
typeMap = {
    "rgbsv": "rgb",
    "rgbtv": "rgb",
    "fluosv": "fluo",
    "fluotv": "fluo"
}

"""
Defines all optional / required keys for all templates.
"""

templateKeys = {
    "loading": {
        "required": ["path", "base", "data", "order"],
        "optional": ["translations", "filetype"],
        "data": {
            "required": ["type"],
            "type": ["value", "file", "date"],
            "value": {
                "required": ["value", "type"],
                "optional": ["translate", "case"]
            },
            "file": {
                "required": ["type", "value", "key", "keyColumn", "valueColumn"],
                "optional": ["translate", "separator"]
            },
            "date": {
                "required": ["type", "value", "format"],
                "optional": []
            }
        },
        "translations": {

        }
    },
    "config": {
        "required": ["version", "installdir", "profile"],
        "optional": ["cluster", "notify", "maxwalltime", "osg"],
        "maxwalltime": {
            "optional": ["images", "stats"]
        },
        "notify": {
            "required": ["email", "pegasus_home"]
        },
        "osg": {
            "required": ["tarball", "ssh"]
        }
    },
    "imgproc": {
        "required": ["workflows", "extract"],
        "optional": ["options"],
        "job": {
            "required": ["executable", "inputs", "outputs", "arguments", "name"],
            "optional": ["depends"]
        },
        "options": {
            "required": [],
            "optional": ["save-steps"]
        },
        "extract": {
            "required": ["workflows"],
            "optional": ["histogram-bin"],
            "workflows": {
                "required": [], # imtype are required, handled at run time.
                "optional": []
            },
            "histogram-bin": {
                "required": ["chunks", "group", "channels"],
                "optional": []
            }
        }
    },
    "stats": {
        "required": ["workflows"],
        "optional": ["options"],
        "job": {
            "required": ["executable", "inputs", "outputs", "arguments", "name"],
            "optional": ["depends"]
        }
    }
}

"""
Defines valid date format character
"""
dateFormat = ["Y", "y", "M", "m", "d", "B", "b"]
dateSep = ["/", "-", "_", " "]

"""
Defines required headers for output
"""
outHeaders = ["pegasusid", "experiment", "id", "date", "imtype", "path"]

"""
Defines ALL possible output headers
"""
allHeaders = outHeaders + ["error", "rowNum", "colNum"]

"""
Defines required files for job checking
"""
jobFiles = ["crawl.json", "config.json", "imgproc.json", "stats.json", "images.db"]
imgprocFiles = ["config.json", "imgproc.json", "images.db"]
statisticsFiles = ["config.json", "stats.json"]

workflowFile = "imgproc.json"
configFile = "config.json"
dbFile = "images.db"
statsFile = "stats.json"
outputdb = "output.db"


"""
Defines two things for stats functions.
'Required' columns are the metadata columns a function needs to execute properly.
'Exclude' columns are the metadata columns that become uninteresting after execution.
"""
statsColumns = {
    "histogramBins": {
        "ref": False,
        "add": ["name", "minr", "ming", "minb", "maxr", "maxg", "maxb"],
        "required": ["pegasusid", "experiment", "id", "date", "imtype", "imgname", "outputPath"],
        "exclude": ["all"],
        "overwrite": []
    },
    "ttest": {
        "ref": True,
        "add": [],
        "required": ["pegasusid", "date", "imtype"],
        "exclude": ["pegasusid", "path", "outputPath", "error", "id", "genotype", "treatment"],
        "overwrite": []
    },
    "treatmentComp": {
        "ref": True,
        "add": [],
        "required": ["pegasusid", "id", "genotype", "date", "treatment", "imtype"],
        "exclude": ["pegasusid", "id", "path", "outputPath", "error"],
        "overwrite": ["treatment"]
    },
    "shootArea": {
        "ref": True,
        "add": [],
        "required": ["pegasusid", "id", "genotype", "date", "treatment", "imtype"],
        "exclude": ["pegasusid", "imgname", "path", "outputPath", "error", "rowNum", "colNum"],
        "overwrite": ["imtype"]
    },
    "normalize": {
        "ref": True,
        "add": [],
        "required": ["pegasusid"],
        "exclude": ["pegasusid", "path", "outputPath", "error"],
        "overwrite": []
    },
    "correlation": {
        "ref": True,
        "add": [],
        "required": ["pegasusid", "id", "date"],
        "exclude": ["pegasusid", "path", "outputPath", "error", "rowNum", "colNum", "date", "imgname"],
        "overwrite": []
    },
    "threshold": {
        "ref": True,
        "add": [],
        "required": ["pegasusid"],
        "exclude": ["pegasusid", "path", "outputPath", "error"],
        "overwrite": []
    },
    "anova": {
        "ref": False,
        "add": ["factors"],
        "required": ["pegasusid", "treatment", "date", "imtype"],
        "exclude": ["pegasusid", "experiment", "id", "genotype", "date", "treatment", "imgname", "path", "outputPath", "error"],
        "overwrite": ["imtype"]
    }
}

"""
Defines allowed image extensions, png is preferred.
"""
imageExtensions = [".png", ".jpg", ".jpeg", ".gif"]

"""
Defines allowed file extensions
"""
fileExtensions = {
    "image": ".png",
    "roi": ".json",
    "binfile": ".json",
    "csv": ".csv",
}


"""
Defines valid arguments for stats and image processing
functions.
"""
valid = {
    "ih-resize": {
        "type": "imgproc",
        "inputs": ["image"],
        "outputs": ["image"],
        "arguments": {
            "--input": {
                "type": "derived",
                "key": "inputs",
                "index": 0,
                "required": "true"
            },
            "--output": {
                "type": "derived",
                "key": "outputs",
                "index": 0,
                "required": "true"
            },
            "--outputdir": {
                "type": "overwrite",
                "value": "."
            },
            "--writeblank": {
                "type": "overwrite",
                "required": "true",
                "value": ""
            },
            "--scale": {
                "type": "numeric"
            },
            "--width": {
                "type": "numeric",
                "validation": "list",
                "value": range(1, 5001)
            },
            "--height": {
                "type": "numeric",
                "validation": "list",
                "value": range(1, 5001)
            }
        }
    },
    "ih-color-filter": {
        "type": "imgproc",
        "inputs": ["image", "roi"],
        "outputs": ["image"],
        "arguments": {
            "--input": {
                "type": "derived",
                "key": "inputs",
                "index": 0,
                "required": "true"
            },
            "--output": {
                "type": "derived",
                "key": "outputs",
                "index": 0,
                "required": "true"
            },
            "--outputdir": {
                "type": "overwrite",
                "value": "."
            },
            "--writeblank": {
                "type": "overwrite",
                "required": "true",
                "value": ""
            },
            "--roi": {
                "type": "derived",
                "key": "inputs",
                "index": 1
            },
            "--logic": {
                "type": "string",
                "required": "true",
                "complex": "true"
            }
        }
    },
    "ih-edges": {
        "type": "imgproc",
        "inputs": ["image"],
        "outputs": ["image"],
        "arguments": {
            "--input": {
                "type": "derived",
                "key": "inputs",
                "index": 0,
                "required": "true"
            },
            "--output": {
                "type": "derived",
                "key": "outputs",
                "index": 0,
                "required": "true"
            },
            "--outputdir": {
                "type": "overwrite",
                "value": "."
            },
            "--writeblank": {
                "type": "overwrite",
                "required": "true",
                "value": ""
            },
            "--threshold1": {
                "type": "numeric",
                "required": "true"
            },
            "--threshold2": {
                "type": "numeric",
                "required": "true"
            },
            "--apertureSize": {
                "type": "numeric",
                "validation": "list",
                "value": range(1, 50)
            },
            "--L2gradient": {
                "type": "exist"
            }
        }
    },
    "ih-contour-chop": {
        "type": "imgproc",
        "inputs": ["image", "image"],
        "outputs": ["image", "roi"],
        "arguments": {
           "--input": {
                "type": "derived",
                "key": "inputs",
                "index": 0,
                "required": "true"
            },
            "--binary": {
                "type": "derived",
                "key": "inputs",
                "index": 1,
                "required": "true"
            },
            "--output": {
                "type": "derived",
                "key": "outputs",
                "index": 0,
                "required": "true"
            },
            "--outputdir": {
                "type": "overwrite",
                "value": "."
            },
            "--writeblank": {
                "type": "overwrite",
                "required": "true",
                "value": ""
            },
            "--basemin": {
                "type": "numeric"
            }
        }
    },
    "ih-contour-cut": {
        "type": "imgproc",
        "inputs": ["image", "image"],
        "outputs": ["image", "roi"],
        "arguments": {
           "--input": {
                "type": "derived",
                "key": "inputs",
                "index": 0,
                "required": "true"
            },
            "--binary": {
                "type": "derived",
                "key": "inputs",
                "index": 1,
                "required": "true"
            },
            "--output": {
                "type": "derived",
                "key": "outputs",
                "index": 0,
                "required": "true"
            },
            "--outputdir": {
                "type": "overwrite",
                "value": "."
            },
            "--writeblank": {
                "type": "overwrite",
                "required": "true",
                "value": ""
            },
            "--basemin": {
                "type": "numeric"
            },
            "--padminx": {
                "type": "numeric"
            },
            "--padmaxx": {
                "type": "numeric"
            },
            "--padminy": {
                "type": "numeric"
            },
            "--padmaxy": {
                "type": "numeric"
            },
            "--resize": {
                "type": "exist"
            },
            "--returnBound": {
                "type": "derived",
                "key": "outputs",
                "index": 1,
                "value": ""
            },
            "--roiwrite": {
                "type": "derived",
                "key": "outputs",
                "index": 1
            }
        }
    },
    "ih-mask": {
        "type": "imgproc",
        "inputs": ["image", "roi"],
        "outputs": ["image"],
        "arguments": {
            "--input": {
                "type": "derived",
                "key": "inputs",
                "index": 0,
                "required": "true"
            },
            "--output": {
                "type": "derived",
                "key": "outputs",
                "index": 0,
                "required": "true"
            },
            "--outputdir": {
                "type": "overwrite",
                "value": "."
            },
            "--writeblank": {
                "type": "overwrite",
                "required": "true",
                "value": ""
            }
        }
    },
    "ih-crop": {
        "type": "imgproc",
        "inputs": ["image", "roi"],
        "outputs": ["image"],
        "arguments": {
           "--input": {
                "type": "derived",
                "key": "inputs",
                "index": 0,
                "required": "true"
            },
            "--output": {
                "type": "derived",
                "key": "outputs",
                "index": 0,
                "required": "true"
            },
            "--outputdir": {
                "type": "overwrite",
                "value": "."
            },
            "--writeblank": {
                "type": "overwrite",
                "required": "true",
                "value": ""
            },
            "--roi": {
                "type": "derived",
                "key": "inputs",
                "index": 1,
                "required": "true"
            },
            "--resize": {
                "type": "exist"
            }
        }
    },
    "ih-split": {
        "type": "imgproc",
        "inputs": ["image"],
        "outputs": ["image"],
        "arguments": {
           "--input": {
                "type": "derived",
                "key": "inputs",
                "index": 0,
                "required": "true"
            },
            "--output": {
                "type": "derived",
                "key": "outputs",
                "index": 0,
                "required": "true"
            },
            "--outputdir": {
                "type": "overwrite",
                "value": "."
            },
            "--writeblank": {
                "type": "overwrite",
                "required": "true",
                "value": ""
            },
            "--channel": {
                "type": "numeric",
                "validation": "list",
                "value": [0, 1, 2],
                "required": "true"
            }
        }
    },
    "ih-equalize-hist": {
        "type": "imgproc",
        "inputs": ["image"],
        "outputs": ["image"],
        "arguments": {
           "--input": {
                "type": "derived",
                "key": "inputs",
                "index": 0,
                "required": "true"
            },
            "--output": {
                "type": "derived",
                "key": "outputs",
                "index": 0,
                "required": "true"
            },
            "--outputdir": {
                "type": "overwrite",
                "value": "."
            },
            "--writeblank": {
                "type": "overwrite",
                "required": "true",
                "value": ""
            }
        }
    },
    "ih-flood-fill": {
        "type": "imgproc",
        "inputs": ["image", "image", "image"],
        "outputs": ["image"],
        "arguments": {
           "--input": {
                "type": "derived",
                "key": "inputs",
                "index": 0,
                "required": "true"
            },
            "--mask": {
                "type": "derived",
                "key": "inputs",
                "index": 1,
                "required": "true"
            },
            "--seedMask": {
                "type": "derived",
                "key": "inputs",
                "index": 2
            },
            "--output": {
                "type": "derived",
                "key": "outputs",
                "index": 0,
                "required": "true"
            },
            "--outputdir": {
                "type": "overwrite",
                "value": "."
            },
            "--writeblank": {
                "type": "overwrite",
                "required": "true",
                "value": ""
            },
            "--low": {
                "type": "string",
                "required": "true"
            },
            "--high": {
                "type": "string",
                "required": "true"
            },
            "--writeColor": {
                "type": "string",
                "required": "true"
            },
            "--connectivity": {
                "type": "numeric",
                "validation": "list",
                "value": [4, 8]
            },
            "--fixed": {
                "type": "exist"
            },
            "--seedx": {
                "type": "numeric"
            },
            "--seedy": {
                "type": "numeric"
            },
            "--findSeed": {
                "type": "exist"
            },
            "--binary": {
                "type": "exist"
            }
        }
    },
    "ih-fill": {
        "type": "imgproc",
        "inputs": ["image", "roi"],
        "outputs": ["image"],
        "arguments": {
           "--input": {
                "type": "derived",
                "key": "inputs",
                "index": 0,
                "required": "true"
            },
            "--output": {
                "type": "derived",
                "key": "outputs",
                "index": 0,
                "required": "true"
            },
            "--outputdir": {
                "type": "overwrite",
                "value": "."
            },
            "--writeblank": {
                "type": "overwrite",
                "required": "true",
                "value": ""
            },
            "--roi": {
                "type": "derived",
                "key": "inputs",
                "index": 1,
                "required": "true"
            },
            "--r": {
                "type": "numeric",
                "validation": "list",
                "value": range(0, 256)
            },
            "--g": {
                "type": "numeric",
                "validation": "list",
                "value": range(0, 256)
            },
            "--b": {
                "type": "numeric",
                "validation": "list",
                "value": range(0, 256)
            }
        }
    },
    "ih-morphology": {
        "type": "imgproc",
        "inputs": ["image"],
        "outputs": ["image"],
        "arguments": {
            "--input": {
                "type": "derived",
                "key": "inputs",
                "index": 0,
                "required": "true"
            },
            "--output": {
                "type": "derived",
                "key": "outputs",
                "index": 0,
                "required": "true"
            },
            "--outputdir": {
                "type": "overwrite",
                "value": "."
            },
            "--writeblank": {
                "type": "overwrite",
                "required": "true",
                "value": ""
            },
            "--morphType": {
                "type": "string",
                "validation": "dictionary",
                "value": morph,
                "required": "true"
            },
            "--ktype": {
                "type": "string",
                "validation": "dictionary",
                "value": kernels,
                "required": "true"
            },
            "--kwidth": {
                "type": "numeric",
                "validation": "list",
                "value": range(1, 256, 2),
                "required": "true"
            },
            "--kheight": {
                "type": "numeric",
                "validation": "list",
                "value": range(1, 256, 2),
                "required": "true"
            },
            "--anchorx": {
                "type": "numeric",
                "validation": "list",
                "value": range(-255, 256),
            },
            "--anchory": {
                "type": "numeric",
                "validation": "list",
                "value": range(-255, 256),
            },
            "--iterations": {
                "type": "numeric",
                "validation": "list",
                "value": range(1, 100)
            },
            "--border": {
                "type": "string",
                "validation": "dictionary",
                "value": borders
            }
        }
    },
    "ih-normalize-intensity": {
        "type": "imgproc",
        "inputs": ["image"],
        "outputs": ["image"],
        "arguments": {
            "--input": {
                "type": "derived",
                "key": "inputs",
                "index": 0,
                "required": "true"
            },
            "--output": {
                "type": "derived",
                "key": "outputs",
                "index": 0,
                "required": "true"
            },
            "--outputdir": {
                "type": "overwrite",
                "value": "."
            },
            "--writeblank": {
                "type": "overwrite",
                "required": "true",
                "value": ""
            }
        }
    },
    "ih-gaussian-blur": {
        "type": "imgproc",
        "inputs": ["image"],
        "outputs": ["image"],
        "arguments": {
            "--input": {
                "type": "derived",
                "key": "inputs",
                "index": 0,
                "required": "true"
            },
            "--output": {
                "type": "derived",
                "key": "outputs",
                "index": 0,
                "required": "true"
            },
            "--outputdir": {
                "type": "overwrite",
                "value": "."
            },
            "--writeblank": {
                "type": "overwrite",
                "required": "true",
                "value": ""
            },
            "--kwidth": {
                "type": "numeric",
                "validation": "list",
                "value": range(1, 256, 2),
                "required": "true"
            },
            "--kheight": {
                "type": "numeric",
                "validation": "list",
                "value": range(1, 256, 2),
                "required": "true"
            },
            "--sigmax": {
                "type": "numeric"
            },
            "--sigmay": {
                "type": "numeric"
            },
            "--border": {
                "type": "string",
                "validation": "dictionary",
                "value": borders
            }
        }
    },
    "ih-median-blur": {
        "type": "imgproc",
        "inputs": ["image"],
        "outputs": ["image"],
        "arguments": {
            "--input": {
                "type": "derived",
                "key": "inputs",
                "index": 0,
                "required": "true"
            },
            "--output": {
                "type": "derived",
                "key": "outputs",
                "index": 0,
                "required": "true"
            },
            "--outputdir": {
                "type": "overwrite",
                "value": "."
            },
            "--writeblank": {
                "type": "overwrite",
                "required": "true",
                "value": ""
            },
            "--ksize": {
                "type": "numeric",
                "validation": "list",
                "value": range(1, 256, 2),
                "required": "true"
            }
        }
    },
    "ih-blur": {
        "type": "imgproc",
        "inputs": ["image"],
        "outputs": ["image"],
        "arguments": {
            "--input": {
                "type": "derived",
                "key": "inputs",
                "index": 0,
                "required": "true"
            },
            "--output": {
                "type": "derived",
                "key": "outputs",
                "index": 0,
                "required": "true"
            },
            "--outputdir": {
                "type": "overwrite",
                "value": "."
            },
            "--writeblank": {
                "type": "overwrite",
                "required": "true",
                "value": ""
            },
            "--kwidth": {
                "type": "numeric",
                "validation": "list",
                "value": range(1, 256, 2),
                "required": "true"
            },
            "--kheight": {
                "type": "numeric",
                "validation": "list",
                "value": range(1, 256, 2),
                "required": "true"
            },
            "--anchorx": {
                "type": "numeric",
                "validation": "list",
                "value": range(-255, 256),
            },
            "--anchory": {
                "type": "numeric",
                "validation": "list",
                "value": range(-255, 256),
            },
            "--border": {
                "type": "string",
                "validation": "dictionary",
                "value": borders
            }
        }
    },
    "ih-adaptive-threshold": {
        "type": "imgproc",
        "inputs": ["image"],
        "outputs": ["image"],
        "arguments": {
            "--input": {
                "type": "derived",
                "key": "inputs",
                "index": 0,
                "required": "true"
            },
            "--output": {
                "type": "derived",
                "key": "outputs",
                "index": 0,
                "required": "true"
            },
            "--outputdir": {
                "type": "overwrite",
                "value": "."
            },
            "--writeblank": {
                "type": "overwrite",
                "required": "true",
                "value": ""
            },
            "--value": {
                "type": "numeric",
                "validation": "list",
                "value": range(0, 256),
                "required": "true"
            },
            "--adaptiveType": {
                "type": "string",
                "validation": "dictionary",
                "value": adaptives,
                "required": "true"
            },
            "--thresholdType": {
                "type": "string",
                "validation": "dictionary",
                "value": {"binary": "", "inverse": ""},
                "required": "true"
            },
            "--blockSize": {
                "type": "numeric",
                "validation": "list",
                "value": range(1, 256, 2),
                "required": "true"
            },
            "--C": {
                "type": "numeric",
                "required": "true",
            }
        }
    },
    "ih-meanshift": {
        "type": "imgproc",
        "inputs": ["image"],
        "outputs": ["image"],
        "weight": .3,
        "arguments": {
            "--input": {
                "type": "derived",
                "key": "inputs",
                "index": 0,
                "required": "true"
            },
            "--output": {
                "type": "derived",
                "key": "outputs",
                "index": 0,
                "required": "true"
            },
            "--outputdir": {
                "type": "overwrite",
                "value": "."
            },
            "--writeblank": {
                "type": "overwrite",
                "required": "true",
                "value": ""
            },
            "--spatial_radius": {
                "type": "numeric",
                "required": "true"
            },
            "--range_radius": {
                "type": "numeric",
                "required": "true"
            },
            "--min_density": {
                "type": "numeric",
                "required": "true"
            }
        }
    },
    "ih-convert-color": {
        "type": "imgproc",
        "inputs": ["image"],
        "outputs": ["image"],
        "arguments": {
            "--input": {
                "type": "derived",
                "key": "inputs",
                "index": 0,
                "required": "true"
            },
            "--output": {
                "type": "derived",
                "key": "outputs",
                "index": 0,
                "required": "true"
            },
            "--outputdir": {
                "type": "overwrite",
                "value": "."
            },
            "--writeblank": {
                "type": "overwrite",
                "required": "true",
                "value": ""
            },
            "--intype": {
                "type": "string",
                "validation": "dictionary",
                "value": colors,
                "required": "true"
            },
            "--outtype": {
                "type": "string",
                "validation": "dictionary",
                "key": "--intype",
                "value": colors,
                "required": "true"
            }
        }
    },
    "ih-threshold": {
        "type": "imgproc",
        "inputs": ["image"],
        "outputs": ["image"],
        "arguments": {
            "--input": {
                "type": "derived",
                "key": "inputs",
                "index": 0,
                "required": "true"
            },
            "--output": {
                "type": "derived",
                "key": "outputs",
                "index": 0,
                "required": "true"
            },
            "--outputdir": {
                "type": "overwrite",
                "value": "."
            },
            "--writeblank": {
                "type": "overwrite",
                "required": "true",
                "value": ""
            },
            "--thresh": {
                "type": "numeric",
                "required": "true"
            },
            "--max": {
                "type": "numeric",
                "validation": "list",
                "value": range(0, 256)
            },
            "--type": {
                "type": "string",
                "validation": "list",
                "value": ["binary", "inverse", "trunc", "otsu", "tozero"]
            }
        }
    },
    "ih-bitwise-or": {
        "type": "imgproc",
        "inputs": ["image", "image"],
        "outputs": ["image"],
        "arguments": {
            "--input1": {
                "type": "derived",
                "key": "inputs",
                "index": 0,
                "required": "true"
            },
            "--input2": {
                "type": "derived",
                "key": "inputs",
                "index": 1,
                "required": "true"
            },
            "--output": {
                "type": "derived",
                "key": "outputs",
                "index": 0,
                "required": "true"
            },
            "--outputdir": {
                "type": "overwrite",
                "value": "."
            },
            "--writeblank": {
                "type": "overwrite",
                "required": "true",
                "value": ""
            }
        }
    },
    "ih-bitwise-xor": {
        "type": "imgproc",
        "inputs": ["image", "image"],
        "outputs": ["image"],
        "arguments": {
            "--input1": {
                "type": "derived",
                "key": "inputs",
                "index": 0,
                "required": "true"
            },
            "--input2": {
                "type": "derived",
                "key": "inputs",
                "index": 1,
                "required": "true"
            },
            "--output": {
                "type": "derived",
                "key": "outputs",
                "index": 0,
                "required": "true"
            },
            "--outputdir": {
                "type": "overwrite",
                "value": "."
            },
            "--writeblank": {
                "type": "overwrite",
                "required": "true",
                "value": ""
            }
        }
    },
    "ih-bitwise-not": {
        "type": "imgproc",
        "inputs": ["image"],
        "outputs": ["image"],
        "arguments": {
            "--input": {
                "type": "derived",
                "key": "inputs",
                "index": 0,
                "required": "true"
            },
            "--output": {
                "type": "derived",
                "key": "outputs",
                "index": 0,
                "required": "true"
            },
            "--outputdir": {
                "type": "overwrite",
                "value": "."
            },
            "--writeblank": {
                "type": "overwrite",
                "required": "true",
                "value": ""
            }
        }
    },
    "ih-add-weighted": {
        "type": "imgproc",
        "inputs": ["image", "image"],
        "outputs": ["image"],
        "arguments": {
            "--input1": {
                "type": "derived",
                "key": "inputs",
                "index": 0,
                "required": "true"
            },
            "--input2": {
                "type": "derived",
                "key": "inputs",
                "index": 1,
                "required": "true"
            },
            "--output": {
                "type": "derived",
                "key": "outputs",
                "index": 0,
                "required": "true"
            },
            "--outputdir": {
                "type": "overwrite",
                "value": "."
            },
            "--writeblank": {
                "type": "overwrite",
                "required": "true",
                "value": ""
            },
            "--weight1": {
                "required": "true",
                "type": "numeric"
            },
            "--weight2": {
                "required": "true",
                "type": "numeric"
            }
        }
    },
    "ih-bitwise-and": {
        "type": "imgproc",
        "inputs": ["image", "image"],
        "outputs": ["image"],
        "arguments": {
            "--input1": {
                "type": "derived",
                "key": "inputs",
                "index": 0,
                "required": "true"
            },
            "--input2": {
                "type": "derived",
                "key": "inputs",
                "index": 1,
                "required": "true"
            },
            "--output": {
                "type": "derived",
                "key": "outputs",
                "index": 0,
                "required": "true"
            },
            "--outputdir": {
                "type": "overwrite",
                "value": "."
            },
            "--writeblank": {
                "type": "overwrite",
                "required": "true",
                "value": ""
            },
            "--mask": {
                "type": "exist"
            }
        }
    },
    "ih-extract": {
        "type": "system",
        "inputs": ["image", "binfile"],
        "outputs": ["none"],
        "arguments": {
            "--input": {
                "type": "derived",
                "key": "inputs",
                "index": 0,
                "required": "true"
            },
            "--dimensions": {
                "type": "exist"
            },
            "--dimfromroi": {
                "type": "string"
            },
            "--pixels": {
                "type": "exist"
            },
            "--moments": {
                "type": "exist"
            },
            "--bins": {
                "type": "string"
            },
            "--channels": {
                "type": "exist"
            },
            "--hull": {
                "type": "exist"
            },
            "--circle": {
                "type": "exist"
            }
        }
    },
    "ih-error-log": {
         "type": "imgproc"
    },



    "ih-extract-all": {
        "type": "system"
    },
    "ih-extract-multi": {
        "type": "system"
    },
    "ih-sql-aggregate": {
        "type": "system"
    },
    "osg-wrapper.sh": {
        "type": "system"
    },



    "ih-stats-export": {
        "type": "statistics",
        "inputs": ["table"],
        "outputs": ["csv"],
        "arguments": {
            "--table": {
                "type": "derived",
                "key": "inputs",
                "index": 0,
                "required": "true"
            },
            "--fname": {
                "type": "derived",
                "key": "outputs",
                "index": 0,
                "required": "true"
            }
        }
    },
    "ih-stats-histogram-bin": {
        "type": "system",
        "inputs": ["table"],
        "outputs": ["table"],
        "arguments": {
            "--intable": {
                "type": "derived",
                "key": "inputs",
                "index": 0,
                "required": "true"
            },
            "--outtable": {
                "type": "derived",
                "key": "outputs",
                "index": 0,
                "required": "true"
            },
            "--channels": {
                "type": "dict",
                "required": "true"
            },
            "--group": {
                "type": "dict",
                "required": "true"
            },
            "--chunks": {
                "type": "dict",
                "required": "true"
            }
        }
    },
    "ih-stats-ttest": {
        "type": "statistics",
        "inputs": ["table"],
        "outputs": ["table"],
        "arguments": {
            "--intable": {
                "type": "derived",
                "key": "inputs",
                "index": 0,
                "required": "true"
            },
            "--outtable": {
                "type": "derived",
                "key": "outputs",
                "index": 0,
                "required": "true"
            },
            "--comp": {
                "type": "string",
                "validation": "list",
                "value": ["imtype", "imgname"],
                "required": "true"
            },
            "--overwrite": {
                "type": "overwrite",
                "value": "",
                "required": "true"
            }
        }
    },
    "ih-stats-treatment-comp": {
        "type": "statistics",
        "inputs": ["table"],
        "outputs": ["table"],
        "arguments": {
            "--intable": {
                "type": "derived",
                "key": "inputs",
                "index": 0,
                "required": "true"
            },
            "--outtable": {
                "type": "derived",
                "key": "outputs",
                "index": 0,
                "required": "true"
            },
            "--type": {
                "type": "string",
                "validation": "list",
                "value": ["ratio", "difference"],
                "required": "true"
            },
            "--direction": {
                "type": "string",
                "validation": "list",
                "value": ["Control", "Stress"],
                "required": "true"
            },
            "--comp": {
                "type": "string",
                "validation": "list",
                "value": ["imtype", "imgname"],
                "required": "true"
            },
            "--overwrite": {
                "type": "overwrite",
                "value": "",
                "required": "true"
            }
        }
    },
    "ih-stats-anova": {
        "type": "statistics",
        "inputs": ["table"],
        "outputs": ["table"],
        "arguments": {
            "--group": {
                "type": "list",
                "required": "true",
                "join": " "
            },
            "--intable": {
                "type": "derived",
                "key": "inputs",
                "index": 0,
                "required": "true"
            },
            "--outtable": {
                "type": "derived",
                "key": "outputs",
                "index": 0,
                "required": "true"
            },
            "--overwrite": {
                "type": "overwrite",
                "value": "",
                "required": "true"
            }
        }
    },
    "ih-stats-shoot-area": {
        "type": "statistics",
        "inputs": ["table"],
        "outputs": ["table"],
        "arguments": {
            "--group": {
                "type": "list",
                "required": "true",
                "join": " "
            },
            "--intable": {
                "type": "derived",
                "key": "inputs",
                "index": 0,
                "required": "true"
            },
            "--outtable": {
                "type": "derived",
                "key": "outputs",
                "index": 0,
                "required": "true"
            },
            "--overwrite": {
                "type": "overwrite",
                "value": "",
                "required": "true"
            }
        }
    },
    "ih-stats-threshold": {
        "type": "statistics",
        "inputs": ["table"],
        "outputs": ["table"],
        "arguments": {
            "--thresh": {
                "type": "numeric",
                "required": "true"
            },
            "--intable": {
                "type": "derived",
                "key": "inputs",
                "index": 0,
                "required": "true"
            },
            "--outtable": {
                "type": "derived",
                "key": "outputs",
                "index": 0,
                "required": "true"
            },
            "--overwrite": {
                "type": "overwrite",
                "value": "",
                "required": "true"
            }
        }
    },
    "ih-stats-normalize": {
        "type": "statistics",
        "inputs": ["table"],
        "outputs": ["table"],
        "arguments": {
            "--column": {
                "type": "string"
            },
            "--intable": {
                "type": "derived",
                "key": "inputs",
                "index": 0,
                "required": "true"
            },
            "--outtable": {
                "type": "derived",
                "key": "outputs",
                "index": 0,
                "required": "true"
            },
            "--overwrite": {
                "type": "overwrite",
                "value": "",
                "required": "true"
            }
        }
    },
    "ih-stats-correlate": {
        "type": "statistics",
        "inputs": ["table", "csv", "csv"],
        "outputs": ["table"],
        "arguments": {
            "--intable": {
                "type": "derived",
                "key": "inputs",
                "index": 0,
                "required": "true"
            },
            "--outtable": {
                "type": "derived",
                "key": "outputs",
                "index": 0,
                "required": "true"
            },
            "--datafile": {
                "type": "derived",
                "key": "inputs",
                "index": 1,
                "required": "true"
            },
            "--dataheaders": {
                "type": "derived",
                "key": "inputs",
                "index": 2,
                "required": "true"
            },
            "--overwrite": {
                "type": "overwrite",
                "value": "",
                "required": "true"
            }
        }
    }
}
