.. raw:: html

	<style> .red {color:red} .blue {color:blue} .green {color:green} .orange {color:orange} </style>

.. role:: red

.. role:: blue

.. role:: green

.. role:: orange

Workflow Example #1
===========================
This section will detail the steps involved with creating a super-computer
workflow.  It assumes that you have the proper environment setup
already on a grid computer with Condor and Pegasus installed.
Workflow generation is designed specifically for high throughput
data sets -- this example uses a data set of ~80,000 images.  Additionally,
this tutorial serves to show how to setup and run a workflow, not
explaining the analysis choices made when designing a workflow.  This workflow
was created using experiment '0184 Uni Nebraska Rice 1' data, on
Tusker at the Holland Computing Center.

Final Templates
----------------
:download:`Image Loading <../../examples/workflows/current/crawl.json>`

:download:`Image Processing <../../examples/workflows/current/imgproc.json>`

:download:`Configuration <../../examples/workflows/current/config.json>`

:download:`Genotype Key File <../../examples/workflows/current/GenKey.csv>`

:download:`ROI files <../../examples/workflows/current/roi.tar.gz>`

Image Loading
-------------
In this workflow example, we will use data acquired from LemnaTec's
imaging system, for experiment 0184.  The input data structure has been
altered slightly from the raw LemnaTec data.  Although none of the data
changed, an extra directory was added to help break up the data set.
Here are several examples of paths to images:

| /work/walia/common/ih/rawdata/0184 Uni Nebraska Rice 1/strain3/0184 Uni Nebraska Rice 1_023542-C_2013-09-05_05-18-33_455640/RGB SV1/0_0.png
| /work/walia/common/ih/rawdata/0184 Uni Nebraska Rice 1/strain5/0184 Uni Nebraska Rice 1_023546-C_2013-08-21_05-22-52_432942/FLUO SV1/0_0.png
| /work/walia/common/ih/rawdata/0184 Uni Nebraska Rice 1/strain93/0184 Uni Nebraska Rice 1_023722-S_2013-09-09_10-56-45_462980/RGB TV/0_0.png

There are a total of 436 strain folders, 36 sub folders in each strain folder, and 12 additional image-type folders.  For
this experiment, we will be processing RGB SV1, RGB SV2, FLUO SV1, FLUO SV2, and RGB TV images for a total of 436 * 36 * 5 ~= 80,000 images.
The image loading step takes care of two key problems posed by having large data sets (assuming correctly written template files).  First,
it tracks all images, and loads them into a single database, making it very easy to find and process files in the future.  Second,
all meta-data definitions are done as a result of the crawling -- no manual definitions are required.  Consider our directory structure.
There is a lot of information about each image in the names of the directories -- id numbers, whether or not the plant was stressed, the date, and the image
type.  With this motivation in mind, lets look at the loading template, crawl.json.

.. code-block:: javascript

	{
		"path": "/work/walia/common/ih/rawdata/0184 Uni Nebraska Rice 1/%null%/%null%_%idnum%-%idchar%_%date%/%imgname%/0_0.png",
		"base": "/work/walia/common/ih/rawdata/0184 Uni Nebraska Rice 1/",
		"filetype": ".png",
		"order": ["experiment", "id", "genotype", "date", "treatment", "imgname", "imtype", "path"],
		"data": {
			"experiment": {
				"type": "value",
				"value": "0184"
			},
			"id": {
				"type": "value",
				"value": "%idnum%-%idchar%"
			},
			"genotype": {
				"type": "file",
				"value": "/Users/aknecht/git/ih/old_scripts/2014-09-03/GenKey.csv",
				"key": "%idnum%-%idchar%",
				"keyColumn": 0,
				"valueColumn": 1
			},
			"date": {
				"type": "date",
				"value": "%date%",
				"format": "Y-m-d"
			},
			"treatment": {
				"type": "value",
				"translate": "true",
				"value": "%idchar%"
			},
			"imgname": {
				"type": "value",
				"value": "%imgname%"
			},
			"imtype": {
				"type": "value",
				"translate": "true",
				"value": "%imgname%"
			}
		},
		"translations": {
			"treatment": {
				"S": "Stress",
				"s": "Stress",
				"C": "Control",
				"c": "Control"
			},
			"imtype": {
				"RGB SV1": "rgbsv",
				"RGB SV2": "rgbsv",
				"RGB TV": "rgbtv",
				"FLUO SV1": "fluosv",
				"FLUO SV2": "fluosv",
				"FLUO TV": "fluotv",
				"NIR SV1": "nirsv",
				"NIR SV2": "nirsv",
				"NIR TV": "nirtv",
				"IR SV1": "irsv",
				"IR SV2": "irsv",
				"IR TV": "irtv"
			}
		}
	}

This template is fairly complex, so we will break it down into logical subunits.  It should be noted,
that the order of these definitions is not strict, the way they are written matches the thought process
behind crawling.

.. code-block:: javascript

	"path": "/work/walia/common/ih/rawdata/0184 Uni Nebraska Rice 1/%null%/%null%_%idnum%-%idchar%_%date%/%imgname%/0_0.png",
	"base": "/work/walia/common/ih/rawdata/0184 Uni Nebraska Rice 1/",

The first two definitions map our way through the rest of the template.  Above, we noted several important
pieces of information in the name of the directories.  We are doing exactly that here, except in a way that
is more understandable to the computer.  We mark important places in the directory structure by using % signs,
along with names.  The names themselves are not strictly checked, so use names that are easy to remember.
Here we mark 4 places, with the identifiers 'idnum', 'idchar', 'date', and 'imgname'.  The 'null' name is for a
piece of information that isn't important, but still needs to be crawled.  In this case, the 'strain' directories
contain no information relevant to the images themselves.  Also note the underscores and dashes in the definition.
Path splitting to obtain information is possible by placing underscores (_), dashes (-), or spaces ( ) into your
definition.  To make it easier to see, look at our "path" definition side by side with an example path:

| "path": "/work/walia/common/ih/rawdata/0184 Uni Nebraska Rice 1/**%null%**/%null%\_\ :red:`%idnum%`-\ :blue:`%idchar%`\_\ :green:`%date%`/\ :orange:`%imgname%`/0_0.png",
| /work/walia/common/ih/rawdata/0184 Uni Nebraska Rice 1/**strain3**/0184 Uni Nebraska Rice 1\_\ :red:`023542`-\ :blue:`C`\_\ :green:`2013-09-05`\_05-18-33_455640/\ :orange:`RGB SV1`/0_0.png

It becomes very apparent how each defined identifier lines up with the path.  Creating this identifier string is
a very key part of the template definition.  It will likely take some time before you are completely comfortable
writing identifier strings, and every workflow is different.  The other workflow examples have different data paths
for input files, so it is recommended you look at those as well. The identifiers will be used in further steps.  The "base" definition
is simply where crawling should start.  It should be a subset of the "path" definition.

.. code-block:: javascript

	"filetype": ".png",
	"order": ["experiment", "id", "genotype", "date", "treatment", "imgname", "imtype", "path"],

The "filetype" definition is exactly that.  It searches for all files in the final path that end in the specified filetype.
The "order" definition is the order in which values are stored in to the database.  It serves two purposes.  Thematically,
you can organize your columns the same way you would data.  More importantly, it specifies which values are saved to the database.
You can define any value in the "order" definition, however, there are **required** definitions as well.  In addition,
although there are some optional column names, many of the statistics function expect a given format for data.
The names included above are the names that the statistics functions expect.  They relate directly to information about each image.
"experiment" is required, although we simply use it as additional information to help keep things organized.  Data that comes
from LemnaTec has id's assigned to them, in this case, "id" is the LemnaTec assigned value.  "genotype" contains the identifier for
which genotype the plant is.  "date" is the date the plant was imaged.  "treatment" is whether the plant is control or stressed.
"imgname" is which type, shot, and number the plant is.  Examples include RGB SV1, RGB SV2, RGB TV, FLUO SV1, FLUO SV2, FLUO TV e.t.c
"imtype" is just which type and shot the plant is.  Examples include rgbsv, rgbtv, fluosv, fluotv e.t.c.  "imtype" is generally
used more than it "imgname" counterpart.  "path" is a required entry, and will be filed with the input path to the image.
The final output path of the image is based on "experiment", "id", "date", "imtype", and "imgname", so defining
these is very important.
The next section we talk about is the data section.  The purpose of the data section is to convert the identifiers from
our "path" definition, to the names used in our "order" definition.  Let's look at it one name at a time:

.. code-block:: javascript

		"data": {
			"experiment": {
				"type": "value",
				"value": "0184"
			},

The first line simply shows how to start the data section.  Specifying '"data": {' shows that all further entries
are specifically related to data-mapping.  Each value specified in the data section corresponds to a specific
value in the "order" entry.  The values defined in the data section are NOT order dependent, but we include
them in the same order for ease of access.  Finally, remember that each of these values is for *every* image.
Our first example is defining a value for "experiment".  It's important
to note that "experiment" occurs in order.  The names of entries in the data section must match the value
in the "order" entry exactly.  First we define the type of "experiment".  Type's of data keys can be defined
as "value", "file", or "date".  Here, we define the type of experiment as a value.  This means that the value of
experiment will be saved as some combination of hard-coded characters, and identifiers, based on the "value" definition.
In this case, we do not use identifiers in our "value" definition.  We simply save the value for experiment for every image
as 0184.

.. code-block:: javascript

	"id": {
		"type": "value",
		"value": "%idnum%-%idchar%"
	},

Here, we define the "id" for each plant.  We also define it as type "value", but this time we use identifiers in
the value.  This will load the identifiers from the path directly into the value for id.  Looking at our path definition and test path again:

| "path": "/work/walia/common/ih/rawdata/0184 Uni Nebraska Rice 1/**%null%**/%null%\_\ :red:`%idnum%`-\ :blue:`%idchar%`\_\ :green:`%date%`/\ :orange:`%imgname%`/0_0.png",
| /work/walia/common/ih/rawdata/0184 Uni Nebraska Rice 1/**strain3**/0184 Uni Nebraska Rice 1\_\ :red:`023542`-\ :blue:`C`\_\ :green:`2013-09-05`\_05-18-33_455640/\ :orange:`RGB SV1`/0_0.png

For this example, the value of id would be loaded as "023542-C".  It may seem unnecessary to break up 'idnum' and 'idchar', since we use them together here,
however, we use 'idchar' by itself in a later step.  It's important to make sure that the identifiers you use match exactly with those used in the path.
Any value not surrounded by percent signs will be hard-coded into the output value.  So the "-" between our "idnum" and "idchar" identifiers is hard-coded
into the output value.

.. code-block:: javascript

			"genotype": {
				"type": "file",
				"value": "GenKey.csv",
				"key": "%idnum%-%idchar%",
				"keyColumn": 0,
				"valueColumn": 1
			},

Here, we define the "genotype" for each plant.  This time, the type is "file".  This type of data key searches through the rows of a file,
assuming that there is a mapping of key -> value in your row. If you look at the :download:`Genotype Key File <../../examples/workflows/current/GenKey.csv>`,
you can see that it is a csv file with two columns.  We can see that the first column contains values that look like our "id" value.  The second column
contains our genotype string -- our target value. The "file" type always assumes your input is some sort of value separated file.  It doesn't necessarily have to be
separated by commas, but that is the default functionality.  If your file is separated by something other than commas, specify the "separator" option.  There are three
other required definitions for "file" type data keys.  You need to define "key", "keyColumn", and "valueColumn".  The columns themselves are 0-indexed.  In this case, our "keyColumn" is 0, because
our key is located in the 0th column.  "valueColumn" is 1, because our key is located in the 1st column.  Finally, our "key" value is the same as our "id".  This
will sift through our file until it finds the row who's 0th column is our "key" value.  Then, it returns the value of 1st column.  Looking at our path definition and test path again:

| "path": "/work/walia/common/ih/rawdata/0184 Uni Nebraska Rice 1/**%null%**/%null%\_\ :red:`%idnum%`-\ :blue:`%idchar%`\_\ :green:`%date%`/\ :orange:`%imgname%`/0_0.png",
| /work/walia/common/ih/rawdata/0184 Uni Nebraska Rice 1/**strain3**/0184 Uni Nebraska Rice 1\_\ :red:`023542`-\ :blue:`C`\_\ :green:`2013-09-05`\_05-18-33_455640/\ :orange:`RGB SV1`/0_0.png

We will sift through our file looking for "023542-C" (which occurs in the 243rd line).  It will then return the corresponding genotype string
located in the same row, namely UNL032

.. code-block:: javascript

	"date": {
				"type": "date",
				"value": "%date%",
				"format": "Y-m-d"
			},

Here, we define the "date" for each plant.  We use our final type, "date".  The only additional argument to the date type
is "format", which specifies the input format of the date.  The date type loads in values based on a combination of identifiers and hard-coded values again,
but afterwards, it converts the date to Y-m-d format.  In this case, because the input type is defined as "Y-m-d" using a date type
isn't strictly required, we use it as an example though.  The date input string can contain "Y", "y", "M", "m", "d", "B", "b" as format characters,
and uses "-", "/", " ", and "_" as separators.

.. code-block:: javascript

    "treatment": {
	    "type": "value",
		"translate": "true",
		"value": "%idchar%"
	},
	"imgname": {
	    "type": "value",
		"value": "%imgname%"
	},
	"imtype": {
	    "type": "value",
		"translate": "true",
		"value": "%imgname%"
	}

We include the last three together, because they are all of type "value", and simply use one of the identifiers from the base path in their value.
However, it is important to note that two of these values have an additional option, namely "translate": "true".  This specifies that the input value
should be mapped to a different output value.  This functions very similar to a file mapping, except the mapping is defined inside the template.
It should be noted, that if the "translate" option exists in the data key, then it will check for a translation.  Even if you specify "translate": "false",
it will still check for a translation.  Let's look at the translation section:

.. code-block:: javascript

		"translations": {
			"treatment": {
				"S": "Stress",
				"s": "Stress",
				"C": "Control",
				"c": "Control"
			},
			"imtype": {
				"RGB SV1": "rgbsv",
				"RGB SV2": "rgbsv",
				"RGB TV": "rgbtv",
				"FLUO SV1": "fluosv",
				"FLUO SV2": "fluosv",
				"FLUO TV": "fluotv",
				"NIR SV1": "nirsv",
				"NIR SV2": "nirsv",
				"NIR TV": "nirtv",
				"IR SV1": "irsv",
				"IR SV2": "irsv",
				"IR TV": "irtv"
			}
		}

The translation keys line up exactly with the data keys that have "translate": "true" specified.  The data-mapping to perform is simply defined in-line
as key-value parings.  This is effective for small sets, but is inefficient for large translation sets, such as the genotype file mapping.
Here, the "treatment" translation takes a single character, and maps it to a word.  We simply convert the 1 character idchar into the full word
"Control" or "Stress".  Looking at our path definition and test path again:

| "path": "/work/walia/common/ih/rawdata/0184 Uni Nebraska Rice 1/**%null%**/%null%\_\ :red:`%idnum%`-\ :blue:`%idchar%`\_\ :green:`%date%`/\ :orange:`%imgname%`/0_0.png",
| /work/walia/common/ih/rawdata/0184 Uni Nebraska Rice 1/**strain3**/0184 Uni Nebraska Rice 1\_\ :red:`023542`-\ :blue:`C`\_\ :green:`2013-09-05`\_05-18-33_455640/\ :orange:`RGB SV1`/0_0.png

In this case, our idchar is 'C', this means that the "treatment" data key, will get mapped to "Control".  We also have a translation defined for "imtype".  Looking at our test path,
our imgname is "RGB SV1".  This means that the "imtype" data key will get mapped to "rgbsv".  Remember, the key difference between defining translations, and using file mapping is size.

With our template written, we can now load the images using 2 ih commands.  First,
run the ih-setup command with the name of the folder you want to create:

.. code-block:: bash

	ih-setup --dir awesome_project

This command will create a folder with the name you specify, and will create a two
deep directory structure, with a couple empty files at the bottom:

.. code-block:: bash

	awesome_project/
	  input/
	    -config.json
			-crawl.json
			-images.db
			-imgproc.json
			-stats.json

The ih commands assume by default that you are in the top level awesome_project/
directory, using the above naming conventions for your input files.  The naming
of the input files can be changed by using optional arguments.  Now that the
project folder is setup, create your crawl.json file.  The above example is
specific to our input data, so you must adjust the crawl file to match your
input data.  Once your crawl.json is created, run the ih-crawl command from the
awesome_project folder:

.. code-block:: bash

	ih-crawl

This command may take a while to run depending on how many images need to be indexed.
Once it is finished, it should populate the images.db file with an sqlite3 database.
The database will contain all of the metadata information it parsed from your path
names, as well as paths to your images.  Using the images.db file, and two additional
files, a configuration file (config.json) and an workflow definition file (imgproc.json)
we can submit jobs.

Configuration
-------------

The config file contains information that shouldn't really change from run to run.  It contains things like installation directories, environment
variables, and job clustering.  Let's take a look.

.. code-block:: javascript

	{
	        "installdir": "/work/walia/common/ih/pymodules/bin/",
	        "profile": {
	                "pegasus": {
	                        "style": "glite"
	                },
	                "condor": {
	                        "grid_resource": "pbs",
	                        "universe": "vanilla"
	                },
	                "env": {
	                        "PATH": "/work/walia/common/ih/pymodules/bin/",
													"PYTHONPATH": "/work/walia/common/ih/pymodules/lib/python2.6/site-packages
	                        "LD_LIBRARY_PATH": "/work/walia/common/ih/pymodules/opencv_lib/"
	                }
	        },
	        "cluster": 100,
	        "maxwalltime": {
	        	"images": 2,
	        	"stats": 300
	        },
	        "notify": {
	        	"email": "avi@kurtknecht.com",
	        	"pegasus_home": "/usr/share/pegasus/"
	        }
	}

Most of these definitions are fairly straightforward, but some, such as the pegasus
style and condor universe will be specific to the cluster you use.  Make sure
you use appropriate pegasus configuration for your system.

1. "installdir" - This is simply the location to the ih-commands.

2. "profile" - This definition populates the workflows sites.xml file
(`sites.xml pegasus docs <http://pegasus.isi.edu/wms/docs/latest/site.php>`).
The variables defined in here will be very specific for your system.  Make
sure you use the correct pegasus & condor environment variables.  The "env"
definition passes environment variables through to the processing scripts.
Make sure that "PATH" points to necessary executables, "PYTHONPATH" points to
necessary python modules, and "LD_LIBRARY_PATH" points to the required opencv
libraries.

3.  "cluster" - This argument sets the horizontal cluster size for job execution.
Because individual image processing steps are fast and don't require many resources,
it is advantageous to cluster them.  The number of clusters depends on how many
input images you have.

4. "maxwalltime" - This argument defines the maximum wall time for image processing
jobs, and statitistics workflows.  Cummulative wall time for a single cluster is
the size of the cluster times the value in the "images" definition.  For the
example above, this means that each cluster of 100 images will request 200 mintues
of wall time.

5. "notify" - This argument defines the information needed for email notifications
on workflow completion.  Simply provide an email address, and the path to pegasus_home,
which contains a notification directory.

Processing
----------

The image processing template contains what image processing functions to use and in what order.  Separate workflows
are defined for each image type -- as a result the template is quite long.  Here it is in full:

.. code-block:: javascript

	{
	"workflows": {
		"fluosv": [
			{
				"name": "pot_filter_1",
				"executable": "ih-color-filter",
				"inputs": ["base", "/work/walia/common/workflows/0184/input/fluosv_pot1.json"],
				"outputs": ["pot1"],
				"arguments": {
					"--logic": "(((((((r - g) < 30) and (((r + g) + b) < 110)) or ((((r + g) + b) > 110) and ((r - g) < 50))) or (((r - g) < 25) and ((g - r) < 25))) or (g > 60)) not 1)"
				}
			},
			{
				"name": "pot_filter_2",
				"executable": "ih-color-filter",
				"inputs": ["pot1", "/work/walia/common/workflows/0184/input/fluosv_pot2.json"],
				"outputs": ["pot2"],
				"arguments": {
					"--logic": "(((r + g) + b) > 120)"
				},
				"depends": ["pot_filter_1"]
			},
			{
				"name": "main_filter",
				"executable": "ih-color-filter",
				"inputs": ["pot2"],
				"outputs": ["filter"],
				"arguments": {
					"--logic": "((r - g) > 10)"
				},
				"depends": ["pot_filter_2"]
			},
			{
				"name": "crop",
				"executable": "ih-crop",
				"inputs": ["filter", "/work/walia/common/workflows/0184/input/fluosv_edge.json"],
				"outputs": ["edged"],
				"arguments": {},
				"depends": ["main_filter"]
			},
			{
				"name": "cut",
				"executable": "ih-contour-cut",
				"inputs": ["edged", "edged"],
				"outputs": ["final"],
				"arguments": {
					"--basemin": 75
				},
				"depends": ["crop"]
			}
		],
		"rgbtv": [
			{
				"name": "normalize",
				"executable": "ih-normalize-intensity",
				"inputs": ["base"],
				"outputs": ["normal"],
				"arguments": {}
			},
			{
				"name": "meanshift",
				"executable": "ih-meanshift",
				"inputs": ["normal"],
				"outputs": ["shift"],
				"arguments": {
					"--spatial_radius": 4,
					"--range_radius": 4,
					"--min_density": 40
				},
				"depends": ["normalize"]
			},
			{
				"name": "main_filter",
				"executable": "ih-color-filter",
				"inputs": ["shift"],
				"outputs": ["filter"],
				"arguments": {
					"--logic": "(((g > r) and (g > b)) and ((((b max g) max r) - ((b min g) min r)) > 20))"
				},
				"depends": ["meanshift"]
			},
			{
				"name": "closing",
				"executable": "ih-morphology",
				"inputs": ["filter"],
				"outputs": ["morphed"],
				"arguments": {
					"--ktype": "ellipse",
					"--kwidth": 5,
					"--kheight": 5,
					"--morphType": "close"
				},
				"depends": ["main_filter"]
			},
			{
				"name": "crop",
				"executable": "ih-crop",
				"inputs": ["morphed", "/work/walia/common/workflows/0184/input/rgbtv_edge.json"],
				"outputs": ["edged"],
				"arguments": {},
				"depends": ["closing"]
			},
			{
				"name": "reconstitute",
				"executable": "ih-bitwise-and",
				"inputs": ["edged", "base"],
				"outputs": ["recolor"],
				"arguments": {},
				"depends": ["crop"]
			},
			{
				"name": "cut",
				"executable": "ih-contour-cut",
				"inputs": ["recolor", "recolor"],
				"outputs": ["final"],
				"arguments": {
					"--basemin": 200
				},
				"depends": ["reconstitute"]
			}
		],
		"rgbsv": [
			{
				"name": "pot-detect",
				"executable": "ih-color-filter",
				"inputs": ["base"],
				"outputs": ["pot"],
				"arguments": {
					"--logic": "((((r + g) + b) < 100) or (((b - r) > 40) and ((b - g) > 30)))"
				}
			},
			{
				"name": "pot-crop",
				"executable": "ih-contour-cut",
				"inputs": ["pot", "pot"],
				"outputs": ["unused_1", "pot_roi"],
				"arguments": {
					"--basemin": 100,
					"--padminy": 100,
					"--padmaxy": 2000,
					"--padminx": -25,
					"--padmaxx": -25,
					"--returnBound": ""
				},
				"depends": ["pot-detect"]
			},
			{
				"name": "box-crop",
				"executable": "ih-contour-cut",
				"inputs": ["pot", "pot"],
				"outputs": ["unused_2", "box_roi"],
				"arguments": {
					"--basemin": 100,
					"--padminy": 35,
					"--padmaxy": 2000,
					"--padminx": 50,
					"--padmaxx": 50,
					"--returnBound": ""
				},
				"depends": ["pot-detect"]
			},
			{
				"name": "gray",
				"executable": "ih-convert-color",
				"inputs": ["base"],
				"outputs": ["grayscale"],
				"arguments": {
					"--intype": "bgr",
					"--outtype": "gray"
				}
			},
			{
				"name": "blur",
				"executable": "ih-gaussian-blur",
				"inputs": ["grayscale"],
				"outputs": ["blurred"],
				"arguments": {
					"--kwidth": 5,
					"--kheight": 5
				},
				"depends": ["gray"]
			},
			{
				"name": "thresh",
				"executable": "ih-adaptive-threshold",
				"inputs": ["blurred"],
				"outputs": ["thresh"],
				"arguments": {
					"--value": 255,
					"--thresholdType": "inverse",
					"--adaptiveType": "mean",
					"--blockSize": 15,
					"--C": 3
				},
				"depends": ["blur"]
			},
			{
				"name": "reconstitute1",
				"executable": "ih-bitwise-and",
				"inputs": ["thresh", "base"],
				"outputs": ["recolor1"],
				"arguments": {},
				"depends": ["thresh"]
			},
			{
				"name": "meanshift",
				"executable": "ih-meanshift",
				"inputs": ["recolor1"],
				"outputs": ["shift"],
				"arguments": {
					"--spatial_radius": 2,
					"--range_radius": 2,
					"--min_density": 50
				},
				"depends": ["reconstitute1"]
			},
			{
				"name": "pot-filter",
				"executable": "ih-color-filter",
				"inputs": ["shift", "pot_roi"],
				"outputs": ["pot_filtered"],
				"arguments": {
					"--logic": "((((((((((r > g) and (r > b)) and (((b max g) - (b min g)) < (((r + g) + b) / 20))) or ((((b max g) max r) - ((b min g) min r)) < 10)) or ((b > r) and ((b > g) or (g > r)))) or (((r + g) + b) < 220)) or ((((r + g) + b) < 350) and ((((b max g) max r) - ((b min g) min r)) < 25))) or ((b > g) and (r > g))) or (((((r - g) > 5) and ((g - b) > 5)) and ((r - g) < 25)) and ((g - b) < 25))) not 1)"
				},
				"depends": ["meanshift", "pot-crop"]
			},
			{
				"name": "box-filter",
				"executable": "ih-color-filter",
				"inputs": ["pot_filtered", "box_roi"],
				"outputs": ["box_filtered"],
				"arguments": {
					"--logic": "(((g - b) > 30) or ((r - b) > 30))"
				},
				"depends": ["pot-filter", "box-crop"]
			},
			{
				"name": "gfilter1",
				"executable": "ih-color-filter",
				"inputs": ["box_filtered", "/work/walia/common/workflows/0184/input/rgbsv_gray1.json"],
				"outputs": ["gray_filtered1"],
				"arguments": {
					"--logic": "((((b max g) max r) - ((b min g) min r)) > 50)"
				},
				"depends": ["box-filter", "box-crop"]
			},
			{
				"name": "gfilter2",
				"executable": "ih-color-filter",
				"inputs": ["gray_filtered1", "/work/walia/common/workflows/0184/input/rgbsv_gray2.json"],
				"outputs": ["gray_filtered2"],
				"arguments": {
					"--logic": "((((b max g) max r) - ((b min g) min r)) > 100)"
				},
				"depends": ["gfilter1"]
			},
			{
				"name": "crop",
				"executable": "ih-crop",
				"inputs": ["gray_filtered2", "/work/walia/common/workflows/0184/input/rgbsv_edge.json"],
				"outputs": ["edged"],
				"arguments": {},
				"depends": ["gfilter2"]
			},
			{
				"name": "reconstitute2",
				"executable": "ih-bitwise-and",
				"inputs": ["edged", "base"],
				"outputs": ["recolor2"],
				"arguments": {},
				"depends": ["crop"]
			},
			{
				"name": "cut",
				"executable": "ih-contour-cut",
				"inputs": ["recolor2", "recolor2"],
				"outputs": ["final"],
				"arguments": {
					"--basemin": 50
				},
				"depends": ["reconstitute2"]
			}
		]
	},
	"options": {

	},
	"extract": {
		"histogram-bin": {
			"--group": {"rgb": ["rgbsv", "rgbtv"], "fluo": ["fluosv"]},
			"--chunks": {"rgb": [5, 5, 5], "fluo": [0, 9, 10]},
			"--channels": {"rgb": [0, 1, 2], "fluo": [1, 2]}
		},
		"workflows": {
			"rgbsv": {
				"inputs": ["final"],
				"arguments": {
					"--dimfromroi": "pot_roi",
					"--dimensions": "",
					"--pixels": "",
					"--moments": ""
				},
				"depends": ["cut"]
			},
			"rgbtv": {
				"inputs": ["final"],
				"arguments": {
					"--dimensions": "",
					"--pixels": "",
					"--moments": ""
				},
				"depends": ["cut"]
			},
			"fluosv": {
				"inputs": ["final"],
				"arguments": {
					"--dimfromroi": "/work/walia/common/workflows/0184/input/fluosv_pot1.json",
					"--pixels": "",
					"--moments": ""
				},
				"depends": ["cut"]
			}
		}
	}
	}



Let's break it down into more manageable chunks.  We will look at a few jobs from the workflows.
First, note that all workflow definitions must be under the "workflows" key.  Secondly,
note that the names of the workflows i.e. in this case "fluosv", must match the image types
of images in your database.  Each workflow is defined as a list of jobs.  The jobs aren't
necessarily executed in the order you specify them in the list, but you should structure
your job definition such that it follows the list order as closely as possible for ease
of reading.  Each individual job has 5 required definitions, and 1 optional one.  For each
job you **must** define a name, an executable, the job inputs, the job outputs, and the job arguments.
Note that you must include "arguments" even if it is left blank.
For each job you may optionally define dependent jobs.  Let's look at the first job we define for fluosv:

.. code-block:: javascript

		{
			"name": "pot_filter_1",
			"executable": "ih-color-filter",
			"inputs": ["base", "/work/walia/common/ih/workflows/0184/input/fluosv_pot1.json"],
			"outputs": ["pot1"],
			"arguments": {
				"--logic": "(((((((r - g) < 30) and (((r + g) + b) < 110)) or ((((r + g) + b) > 110) and ((r - g) < 50))) or (((r - g) < 25) and ((g - r) < 25))) or (g > 60)) not 1)"
			}
		},

Here, we define the name as "pot_filter_1".  Names are used to apply a more meaningful label
to each job for the user, as well as used for dependencies in later processing steps.
We define the executable we want to use as "ih-color-filter" -- This executable is used for
processing user defined color logic, and will not be talked about in depth here.  We define two inputs
for our function.  The first is "base" -- which serves as a placeholder for raw images.  You can use
this input in any step and it will load in the starting image.  This is important for steps such
as reconstiuting the color of the image.  The second argument we feed is a path to a roi file.
Here are the contents of the file:

.. code-block:: javascript

	{
	    "ystart": 1110,
	    "yend": "y",
	    "xstart": 369,
	    "xend": 669
	}

The roi file simply defines the region we want to apply our color-filter to.
The roi file will automatically convert "y" to the maximum height, and "x" to the maximum
width.  Additionally it supports simply arithmetic, thus you could enter "y - 300" for
"yend".  If this input is left blank, it simply applies the color-filter to the entire image.
We define the output as "pot1".  This means that the intermediate file will be saved with
a name of "pot1".  Additionally, we can now use "pot1" as input in further steps.  Finally
we define the arguments of our processing functino -- in this case only one, our logic
string.  This job is the first job in our processing workflow, so we define no dependencies.
We now look at the second job for fluosv:

.. code-block:: javascript

			{
					"name": "pot_filter_2",
					"executable": "ih-color-filter",
					"inputs": ["pot1", "/work/walia/common/ih/workflows/0184/input/fluosv_pot2.json"],
					"outputs": ["pot2"],
					"arguments": {
						"--logic": "(((r + g) + b) > 120)"
					},
					"depends": ["pot_filter_1"]
			},

Note that the input image is now "pot1" instead of "base".  This chains the output
of the previous step into the input of this step.  To fully accomplish this, we must define
dependency.  Our first job was named "pot_filter_1", and we can see this name in our
dependency list.  A job can have multiple dependencies, you simply separate the names with
commas i.e. "depends": ["job1", "job2", "job3"].  Whenever you use the output of a previous
job, you must include it in the dependency list.  Some functions output roi files instead of,
or in addition to images.  You can similarly use these roi files as input in future steps,
provided that you include them in the proper location in your "inputs" definition.  As a
demonstration of this, we look at two jobs from the rgbsv workflow, "box-crop" and "box-filter".
"box-crop" outputs "box_roi" which we use as a roi for "box-filter".  There are two other definitions
in the processing template.  One is for "options" -- which is left blank in this case.  Currently,
the only supported option is "save-steps".  If you specify:

.. code-block:: javascript

	"options": {
		"save-step": "true"
	},

Each intermediary step (including roi files) will be saved to the final output folder.  Otherwise,
only the final processed image will be saved.  Lastly, "extract" is required, and here you specify
all the numeric information you want to extract from your final images.  Let's take a look:

.. code-block:: javascript

	"extract": {
		"histogram-bin": {
			"--group": {"rgb": ["rgbsv", "rgbtv"], "fluo": ["fluosv"]},
			"--chunks": {"rgb": [5, 5, 5], "fluo": [0, 9, 10]},
			"--channels": {"rgb": [0, 1, 2], "fluo": [1, 2]}
		},
		"workflows": {
			"rgbsv": {
				"inputs": ["final"],
				"arguments": {
					"--dimfromroi": "pot_roi",
					"--pixels": "",
					"--moments": ""
				},
				"depends": ["cut"]
			},
			"rgbtv": {
				"inputs": ["final"],
				"arguments": {
					"--dimensions": "",
					"--pixels": "",
					"--moments": ""
				},
				"depends": ["cut"]
			},
			"fluosv": {
				"inputs": ["final"],
				"arguments": {
					"--dimfromroi": "/work/walia/common/workflows/0184/input/fluosv_pot1.json",
					"--pixels": "",
					"--moments": ""
				},
				"depends": ["cut"]
			}
		}
	}

There is an optional special key you can define -- "histogram-bin" -- in the
extract section.  Specifying this key allows you to perform an experiment-wise histogram
calculation of color-channel information to generate relevant bins.  It performs the
following steps:  1. Calculate color histogram for each processed image.  2. Sum
the histograms to get a histogram for the entire data set.  3. Segment the histogram
into equal area pieces as based on the inputs. 4. Generate complete permutation
of bins based on the divided histogram. In the "histogram-bin" section we
first define "--group".  This allows us to group one or more imtypes from separate
workflows together.  In this case, we group "rgbsv" and "rgbtv" together.  This
allows us to consider color information from the RGB spectrum as a whole.
We name this group "rgb" -- group names are important for future "histogram-bin"
definitions.  Next is "--chunks".  For each group AND channel, you define how many
pieces you want the total calculated histogram to be broken up into.  Remember
that color-space is 3 dimensional, and the order is [B, G, R].  Here, we break up
rgb images into 5 chunks for each channel (for a total of 125 bins), and we break up
fluorescence images only by green and red channels.   Finally, we define what channels to
process for each group.  Channel 0 corresponds to blue, channel 1 corresponds
to green, and channel 2 corresponds to red.  In this case, we leave channel 0
out of fluorescence processing -- this is because a majority of the blue values
in the image are either 0 or 1.  Any channel left out will simply be given a range of [0, 255]
for every generated bin.

The definitions in each individual "workflow" extract information from each individual
image.  You must define "inputs" and "depends" so that the extraction script
can locate the image you want to extract data from (it does not necessarily have to be the
final image, though it generally is).  In the arguments section, you define a list of the
numeric information you want to extract.  For an example of all arguments you can specify,
look at the ih-extract script.  If you specify "histogram-bin" for a particular
imtype, the "--colors" options is added automatically.  Additionally, there are
multiple ways to extract dimensions from an image.  If you pass the "--dimensions"
argument to the image, the dimensions are simply calculated as the height and width
of the final processed images.  Alternative, you can extract dimensions with reference
to a region of interest by using the "--dimfromroi" argument.  The "--dimfromroi" argument
can either by a path to an absolute roi file (as seen in the fluorescence workflow)
or it can be an intermediate output roi from the actually processing workflow
(as seen in the rgbsv workflow).

Finally, to actually generate your workflow, use the ih-run command.  Run this
command from your top level folder that was generated by the ih-setup command.

.. code-block:: bash

	ih-run

This will combine the information in your configuration file, workflow definition file,
and image database to create the necessary files for a pegasus workflow.  Additionally,
before creating the workflow, it validates arguments and dependencies in your workflow.
Use --validate to run in validate only mode to help debug your workflow as you create it.
Depending on how many input images, it may take a while for ih-run to write the necessary submission files.

Submission
-----------
Upon sucessful completion of ih-run, a date and timestamped folder should be created
in your top level folder.  Your setup should now look like this:

.. code-block:: bash

	awesome_project/
		date-timestamp/
		  input/
		    imgproc/
			-conf.rc
			-extract.dax
			-map.rc
			-notify.sh
			-remove.sh
			-sites.xml
			-status.sh
			-submit.sh
			-workflow.dax
		    rawfiles/
		    templates/
		  output/
		    -output.db
		  work/
		input/
			-config.json
			-crawl.json
			-images.db
			-imgproc.json
			-stats.json


The work directory is where actual processing is done -- but initially starts empty.  The output
folder starts only with the output database, but contains no images to start with.  The input folder
contains a copy of your submitted templates in the templates folder, and a copy of all non-image raw-input files
in the rawfiles folder.  Finally, within the imgproc folder are the actual files required to submit
a pegasus workflow.  All you need to do to submit is execute the submit.sh script.  This will launch your
workflow, as well as creating a status.sh script for easy monitoring, and a remove.sh script if you
want to remove your workflow.  If there are other pegasus errors you may need to adjust your configuration.
