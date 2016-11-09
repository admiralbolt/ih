Installation
=============

It is recommended to use the latest stable version for each of the dependencies.  Package
manager software is sometimes behind, so for some dependencies you may have to download and
install a more recent version.  Many systems come with a development tools package which
should be installed. Most of the requirements below requires a c and c++ compiler, and some
require a fortran compiler.

Dependencies
------------
* `Matplotlib <http://matplotlib.org/>`_ >= 1.3.1
* `NumPy <http://www.numpy.org/>`_ >= 1.7
* `OpenCV <http://opencv.org/>`_ == 2.4.x
	* GTK2 (including headers) >= 2.24
	* blas >= 3.2.1
	* lapack >= 3.2.1
	* libav >= 0.5.3
	* cmake >= 2.8.12
	* `ffmpeg <https://www.ffmpeg.org/>`_ >= 2.0.5
* `Pandas <http://pandas.pydata.org/>`_ >= 0.13.1
	* `Cython <http://cython.org/>`_ >= 0.21.1
	* `python-dateutil <https://labix.org/python-dateutil>`_ >= 1.4.1
* `PyMeanShift <https://code.google.com/p/pymeanshift/>`_ >= 0.2.0
* `SciPy <http://www.scipy.org/>`_ >= 0.13.1
* `Pegasus <http://pegasus.isi.edu/>`_ >= 4.4.0
	* Java >= 1.8
	* Perl >= 5.10
* `HTCondor <http://research.cs.wisc.edu/htcondor/>`_ >= 8.3.0

Pegasus and HTCondor are only required if you wish to use the super computer workflow generation functionality.
Additionally, many super computing environments may already have Pegasus, HTCondor, and other
dependencies installed. There are resources available for quickly installing the `SciPy Stack <http://www.scipy.org/install.html>`_,
which includes the NumPy, SciPy, Pandas, and Matplotlib.  The installation tutorials for Mac OSX, and Windows
specifically leave out Pegasus and HTCondor, as they are expected to be machines for local testing, not for
submitting grid jobs.  Finally, Image Harvest can be installed by downloading a zip file from the repo
(`link <https://git.unl.edu/aknecht2/ih>`_), and running 'python setup.py install'.



Centos 6.5
----------
It is **highly** recommended that you use anaconda (or another python package manager such as pip) to install the python packages.  The installation
process becomes much simpler and faster.

With Anaconda
^^^^^^^^^^^^^

.. code-block:: bash

	# Update
	sudo yum -y update

	# Set up condor repo
	cd /etc/yum.repos.d
	sudo wget http://research.cs.wisc.edu/htcondor/yum/repo.d/htcondor-stable-rhel6.repo
	sudo wget http://research.cs.wisc.edu/htcondor/yum/RPM-GPG-KEY-HTCondor
	sudo rpm --import RPM-GPG-KEY-HTCondor

	# Install packages
	sudo yum -y install java-1.8.0-* perl condor.x86_64

	# Download Pegasus
	wget -O pegasus.tar.gz http://download.pegasus.isi.edu/pegasus/4.4.0/pegasus-worker-4.4.0-x86_64_rhel_6.tar.gz
	tar -zxvf pegasus.tar.gz

	# Download and install anaconda
	wget -O anaconda.sh http://09c8d0b2229f813c1b93-c95ac804525aac4b6dba79b00b39d1d3.r79.cf1.rackcdn.com/Anaconda-2.1.0-Linux-x86_64.sh
	bash anaconda.sh -b

	# Install *almost* everything in one line
	conda install numpy scipy pandas matplotlib opencv

	# Download PyMeanShift and install, assuming directory is 'pymeanshift'
	cd pymeanshift
	sudo python setup.py install

	# Install Image Harvest, assuming directory is 'ih.git'
	cd ih.git
	sudo python setup.py install

	# Make sure to move the pegasus python files into the anaconda package folder
	# Update the following command as necessary
	cp -r pegasus-4.4.0/lib64/python2.6/site-packages/Pegasus ~/anaconda/lib/python2.7/site-packages/
	# and to update your bash profile to include the pegasus commands,
	# or cp the pegasus commands to /usr/bin or /usr/local/bin
	cp pegasus-4.4.0/bin/* /usr/bin/


Ubuntu 12.04
------------

It is **highly** recommended that you use anaconda (or another python package manager such as pip) to install the python packages.  The installation
process becomes much simpler and faster.

With Anaconda
^^^^^^^^^^^^^

.. code-block:: bash

	# Update
	sudo apt-get -y update

	# Install build-essential
	sudo apt-get -y install build-essential

	# Setup condor repository
	sudo bash -c 'echo "deb http://research.cs.wisc.edu/htcondor/debian/stable/ wheezy contrib" >> /etc/apt/sources.list'
	wget -qO - http://research.cs.wisc.edu/htcondor/debian/HTCondor-Release.gpg.key | sudo apt-key add -
	sudo apt-get -y update
	sudo apt-get install condor

	# Install dependencies
	sudo apt-get -y install software-properties-common python-software-properties perl
	sudo add-apt-repository -y ppa:webupd8team/java
	sudo apt-get update
	sudo apt-get -y install oracle-java8-installer
	# A license agrement will pop up here...


	# Download pegasus
	wget http://download.pegasus.isi.edu/pegasus/4.4.0/pegasus_4.4.0-1+deb7_amd64.deb
	tar -zxvf pegasus.tar.gz

	# Download and install anaconda
	wget -O anaconda.sh http://09c8d0b2229f813c1b93-c95ac804525aac4b6dba79b00b39d1d3.r79.cf1.rackcdn.com/Anaconda-2.1.0-Linux-x86_64.sh
	bash anaconda.sh -b

	# Install *almost* everything in one line
	conda install numpy scipy pandas matplotlib opencv

	# Download PyMeanShift and install, assuming directory is 'pymeanshift'
	cd pymeanshift
	sudo python setup.py install

	# Install Image Harvest, assuming directory is 'ih.git'
	cd ih.git
	sudo python setup.py install

	# Make sure to move the pegasus python files into the anaconda package folder
	# Update the following command as necessary
	cp -r pegasus-4.4.0/lib64/python2.6/site-packages/Pegasus ~/anaconda/lib/python2.7/site-packages/
	# and to update your bash profile to include the pegasus commands,
	# or cp the pegasus commands to /usr/bin or /usr/local/bin
	cp pegasus-4.4.0/bin/* /usr/bin/

Mac OSX
--------

Installation for local testing is a breeze with `brew <http://brew.sh>`_.  Installing
brew simply requires copying a line into a terminal.  The only two packages
you need to manual download will be PyMeanShift and Image Harvest.
You will have to install `XCode <https://developer.apple.com/xcode/>`_, and the XCode Command Line Tools if you have not already. It's a free download
from the App Store.
After you have downloaded the packages and installed brew, run the following:

.. code-block:: bash

	# Install *almost* everything in one line
	brew tap homebrew/science
	brew tap homebrew/python
	brew update && brew upgrade
	brew install numpy scipy matplotlib pandaseq opencv
	# You need to make sure your PYTHONPATH
	# points to the installed packages.
	# We point to the brew installed packages first,
	# to make sure there are no conflicts with system python.
	export PYTHONPATH=`brew --prefix`/lib/python2.7/site-packages/:$PYTHONPATH

	# Download PyMeanShift and install, assuming directory is 'pymeanshift'
	cd pymeanshift
	sudo python setup.py install

	# Download Image Harvest and install, assuming directory is 'ih.git'
	cd ih.git
	sudo python setup.py install

	# That's it!

Windows
--------

Windows requires a little more work, and in fact, windows doesn't even come with python.
Installing requires adjusting some system settings as well.  You will need to manually
install several packages before `pip <https://pypi.python.org/pypi/pip>`_ can put
in work.  First, install `python2.7 <https://www.python.org/downloads/>`_.  Next,
you have to add python to your PATH environment variable.

* Windows 7: Right click on Computer > Properties > Advanced system settings > Advanced Tab > Enviornment Variables
* Windows 8: Control Panel > System > Advanced system settings > Advanced Tab > Environment Variables

You should see two boxes.  One that says "User variables for <user>", and the other that says
"System variables".  Scroll through the "System variables" box until you find the 'Path' variable.
It should look like lots of paths separated by semicolons.  Edit Path, and add two new paths,
'C:\\Python2.7\\' and 'C:\\Python2.7\\Scripts\\'.  Make sure to keep each path separated by a semicolon.
Next, you need to install a `c++ compiler <http://www.microsoft.com/en-us/download/details.aspx?id=44266>`_ --
simply download the installer and run it.
Finally, download and install `pip <https://pypi.python.org/pypi/pip>`_.  There should
simply be a giant script you copy to a local file, and execute with python.


Now, you can install all the dependent python packages by finding the correct version for your os,
and downloading them from this `link <http://www.lfd.uci.edu/~gohlke/pythonlibs/>`_.  You will need the same
list as above that is, `numpy <http://www.lfd.uci.edu/~gohlke/pythonlibs/#numpy>`_, `scipy <http://www.lfd.uci.edu/~gohlke/pythonlibs/#scipy>`_, `pandas <http://www.lfd.uci.edu/~gohlke/pythonlibs/#pandas>`_, `matplotlib <http://www.lfd.uci.edu/~gohlke/pythonlibs/#matplotlib>`_, and `opencv <http://www.lfd.uci.edu/~gohlke/pythonlibs/#opencv>`_.

.. code-block:: bash

	# For each downloaded wheel file, you will
	# need to run the following from a command prompt
	pip install name.whl
	# Then, download pymeanshift and install, run installer.
	# Then, download Image Harvest and install, assuming directory is 'ih.git'
	cd ih.git
	python setup.py install

One final note, when loading images, python expects forward slashes not back slashes,
and does not expect the C: for absolute paths.  If you have an image called "test.jpg"
in your downloads folder, the correct path for python is "/Users/username/Downloads/test.jpg".
