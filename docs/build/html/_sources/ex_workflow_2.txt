.. raw:: html

	<style> .red {color:red} .blue {color:blue} .green {color:green} .orange {color:orange} </style>

.. role:: red

.. role:: blue

.. role:: green

.. role:: orange

OSG Workflows
==============
This section details the modifications necessary to submit your pegasus
workflows on the `OSG <http://www.opensciencegrid.org/>`_.  Their team has
set up an environment specifically for our software, so the only changes that
need to occur are some configuration changes, and creating a tarred version
of this library. Before you can process, you must request an account at
`osg connect <http://osgconnect.net/>`_.  Additionally, osg connect contains
additionally information for getting started, and generated sample super computing
workflows.

Final Templates
----------------

:download:`Image Loading <../../examples/workflows/osg/crawl.json>`

:download:`Image Processing <../../examples/workflows/osg/imgproc.json>`

:download:`Configuration <../../examples/workflows/osg/config.json>`

:download:`Genotype Key File <../../examples/workflows/osg/GenKey.csv>`

:download:`ROI files <../../examples/workflows/osg/roi.tar.gz>`

System Configuration
--------------------
Before beginning loading and execution of workflows, some environment variables need to
be updated in order to have access to the appropriate software.  All of this can
be taken care of by adjusting your ~/.bash_profile.  Adding the following module
load commands:

.. code-block:: bash

    #!/bin/bash
    source /cvmfs/oasis.opensciencegrid.org/osg/modules/lmod/5.6.2/init/bash

    module load python/2.7
    module load libgfortran
    module load lapack
    module load atlas
    module load hdf5/1.8.13
    module load netcdf/4.2.0
    module load gnome_libs
    module load ffmpeg/0.10.15
    module load opencv/2.4.10
    module load image_modules

.. warning:: Workflow submission only works if you use the pegasus version >=4.5.0.  The default pegasus version is currently 4.5.1, but if you have another version of pegasus loaded you will not be able to submit.  Check this by running pegasus-version.

Once you donwload ih, make sure to update your PATH, and PYTHONPATH
to point to the donwload location of ih.

Image Loading
-------------
This image loading template looks nearly identical to the template from
the previous example.  The data set we use here is a small subset of the data
from the previous example.  There are no specific adjustments that need to be
made for image crawling to work on the OSG.  The difference in this case,
is that the data is publicly available in the @RicePhenomics group folder.
Here are the first few lines of the crawl.json file:

.. code-block:: javascript

    {
        "path": "/stash/project/@RicePhenomics/public/tinySet/%null%/%null%_%idnum%-%idchar%_%date%/%imgname%/0_0.png",
        "base": "/stash/project/@RicePhenomics/public/tinySet",
        ...

The data set located in /stash/project/@RicePhenomics/public/tinySet is publicly available,
so you shouldn't need to adjust this file at all!  To setup a project directory and load images run:

.. code-block:: bash

    ih-setup --dir awesome_project
    # copy the above crawl.json file over awesome_project/input/crawl.json
    cd awesome_project
    ih-crawl

Image Processing
----------------
The image processing file imgproc.json requires no osg specific changes, but
make sure to adjust the paths to the ROI files appropriately to your project
setup.

Configuration
-------------
The configuration for osg submissions is very different, and you must additionally
generate an ih distribution, and ssh keys to transfer your files.
Here is the adjusted configuration file:

.. code-block:: javascript

	{
			"version": "1.0",
			"installdir": "/home/aknecht/stash/walia/ih/ih/build/scripts-2.7/",
			"profile": {
				"pegasus": {
					"style": "condor"
				},
				"condor": {
					"universe": "vanilla",
					"requirements": "OSGVO_OS_STRING == \"RHEL 6\" &amp;&amp; HAS_FILE_usr_lib64_libstdc___so_6 &amp;&amp; CVMFS_oasis_opensciencegrid_org_REVISION >= 3590",
					"+WantsStashCache": "True",
					"+ProjectName": "YOUR_OSG_PROJECT_NAME"
				}
			},
			"osg": {
				"tarball": "/home/aknecht/stash/walia/ih/ih/dist/ih-1.0.tar.gz",
				"ssh": "/home/aknecht/.ssh/workflow"
			},
			"cluster": 80,
			"maxwalltime": {
				"stats": 300,
				"images": 2
			},
			"notify": {
				"email": "YOUR_EMAIL",
				"pegasus_home": "/usr/share/pegasus/"
			}
	}


Most of the information is the same as the configuration file from the previous
workflow example, but there are a few differences.  First, there is a version definition,
which should match the version of your ih tarball (Currently 1.0).  Next, the condor configuration
should have the "requirements" and "+WantsStashCache" definitions, and they should
match as above.  The "+ProjectName" definition is if you have a group on the OSG,
and it should match your group name.  Finally, there is an "osg" specific key.
This requires a path to an ih tarball distribution, as well as a path to your
ssh private key.

Creating the ih Distribution
=============================
To create a tarball distribution, navigate to your ih install, and run:

.. code-block:: python

	python setup.py sdist

This will create a dist folder, as well as an ih-1.0.tar.gz file.  Pass the
full path to this file into the "tarball" definition.

.. warning:: The python setup.py sdist commnad does not correctly create hashbangs for the ih scripts.  The scripts need to point to the python2.7 we loaded from cvfms.  To fix this, run the folllowing:

.. code-block:: bash

    # first cd to the dist folder after creating it with python setup.py sdist
    cd dist
    # un-tar the archive
    tar -zxvf ih-1.0.tar.gz
    # cd to the scripts folder
    cd ih-1.0/scripts/
    # replace the '#!pytohn' hashbangs with the appropriate ones
    sed -i 's/#!python/#!\/cvmfs\/oasis.opensciencegrid.org\/osg\/modules\/virtualenv-2.7\/image_modules\/bin\/python/' *
    # cd out
    cd ../../
    # re-tar our folder
    tar -zcvf ih-1.0.tar.gz ih-1.0

Creating ssh Keys
==================
Next, for data staging and transferring files to work successfully, you need to create an ssh key pair
for your workflow.  Run the following:

.. code-block:: bash

	ssh-keygen -t rsa -b 2048

This while generate an ssh key pair.  You will be prompted for a name and a
password.  When prompted for the password, hit enter to leave the password blank.
After this finishes, there should be two files created in your ~/.ssh/ folder,
a private key file and public key file with the name that you gave.  The public
key is simply the file that ends with ".pub". Append the contents of the public
key file to your ~/.ssh/authorized_keys files.  If there is not a ~/.ssh/authorized_keys
files, then create it and append the contents of your public key to it.

.. code-block:: bash

	cat ~/.ssh/KEY_NAME.pub >> ~/.ssh/authorized_keys

Make sure you provide the full path to the PRIVATE key for the "ssh" definition.
Now you are ready to generate and submit your workflow!  Make sure you cd
to your top level folder (awesome_project) and then run:

.. code-block:: bash

    ih-run

Submission
----------
Upon successfuly completion of ih-run, a date and timestamped folder should be created in
your top level folder (awesome_project).  Your setup should now look like this:

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
          staging/
          work/
        input/
            -config.json
            -crawl.json
            -images.db
            -imgproc.json
            -stats.json

An additional staging folder is created for osg workflows -- this is where all the input and processed files are transferred through.  The work directory is where actual processing is done -- but initially starts empty.  The output
folder starts only with the output database, but contains no images to start with.  The input folder
contains a copy of your submitted templates in the templates folder, and a copy of all non-image raw-input files
in the rawfiles folder.  Finally, within the imgproc folder are the actual files required to submit
a pegasus workflow.  All you need to do to submit is execute the submit.sh script.  This will launch your
workflow, as well as creating a status.sh script for easy monitoring, and a remove.sh script if you
want to remove your workflow.  If there are other pegasus errors you may need to adjust your configuration.

.. warning:: Before executing the submit.sh script, unload the python/2.7 module.

Unfortunately, an awkward python version juggling needs to be done.  The system pegasus wants python2.6, but ih needs python2.7.  Make sure you execute:

.. code-block:: bash

    module unload python/2.7

Before you submit you workflow.
