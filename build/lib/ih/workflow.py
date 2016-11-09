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

import os
import conf
import sys
import json
import re
import csv
import datetime
import sqlite3
import shutil
import errno
import textwrap
import copy
import ih.validator
import getpass
import xml.dom.minidom
from Pegasus.DAX3 import *


class Workflow(object):

    """
        Generic workflow creation class.
    """

    def __init__(self, jobhome, basename = None):
        """
            :param jobhome: The base directory for job submission.
            :type jobhome: str

            Creates a Workflow class based on the input directory.  Only loads and
            validates the config file by default.
        """
        self.err = ""
        self.jobhome = os.path.abspath(jobhome)
        self.jobname = os.path.basename(os.path.dirname(self.jobhome + "/"))
        self.basename = basename
        self.dax = ADAG(self.jobname)
        self.executables = {}
        self.files = {self.dax: {}}
        self.jobs = {self.dax: {}}
        self.deps = {}
        return

    def _loadInputFiles(self):
        """
            Loads the input files into the appropriate variables
            This should be overloaded.
        """
        return

    def _isFile(self, name, dax, imtype, inout):
        """
            Convenience function to check if a given file exists.
        """
        if name in self.files[dax][imtype][inout]:
            return True
        return False

    def _isJob(self, name, dax):
        """
            Convenience function to check if a given job exists.
        """
        if name in self.jobs[dax]:
            return True
        return False

    def _isExecutable(self, name):
        """
            Convenience function to check if a given executable exists.
        """
        if name in self.executables:
            return True
        return False

    def _createSetup(self):
        """
            Creates the base structure for job submission.  Everything is contained
            within a folder based on the current timestamp.
        """
        self.basepath = self.jobhome + "/" + self.basename if self.basename else self.jobhome + "/" + datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S")
        if not os.path.exists(self.basepath):
            os.makedirs(self.basepath)
        if not os.path.exists(self.basepath + "/input"):
            os.makedirs(self.basepath + "/input")
        if not os.path.exists(self.basepath + "/output"):
            os.makedirs(self.basepath + "/output")
        if not os.path.exists(self.basepath + "input/templates"):
            os.makedirs(self.basepath + "/input/templates")
        if not os.path.exists(self.basepath + "/input/rawfiles"):
            os.makedirs(self.basepath + "/input/rawfiles")
        if "osg" in self.config:
            if not os.path.exists(self.basepath + "/staging"):
                os.makedirs(self.basepath + "/staging")
        return

    def _addFile(self, name, imtype, inout, path = None, dax = None, derivedPath = None):
        """
            Adds the inputted file to the dax, as well as the internal variable self.files
        """
        dax = dax if dax else self.dax
        if not self._isFile(name, dax, imtype, inout):
            self.files[dax][imtype][inout][name] = {"file": File(name), "path": ""}
            if inout == "input":
                self.files[dax][imtype][inout][name]["path"] = path if path else name
                self.files[dax][imtype][inout][name]["file"].addPFN(PFN("file://" + path.replace(" ","%20"), "local"))
                if derivedPath:
                    self.files[dax][imtype][inout][name]["derivedPath"] = derivedPath
                dax.addFile(self.files[dax][imtype][inout][name]["file"])
        return

    def _addJob(self, jobname, executable, inputs, outputs, arguments, dependencies = None, dax = None, label = None, walltime = None):
        dax = dax if dax else self.dax
        if not self._isJob(jobname, dax):
            if "osg" in self.config:
                self.jobs[dax][jobname] = Job("osg-wrapper.sh")
            else:
                self.jobs[dax][jobname] = Job(executable)
            dax.addJob(self.jobs[dax][jobname])
            if "osg" in self.config:
                self.jobs[dax][jobname].uses("ih.tar.gz", link = Link.INPUT)
            for key in inputs:
                self.jobs[dax][jobname].uses(inputs[key]["file"], link = Link.INPUT)
            for key in outputs:
                self.jobs[dax][jobname].uses(outputs[key]["file"], link = Link.OUTPUT, transfer = outputs[key]["transfer"])
            arglist = []
            if "osg" in self.config:
                arglist.append("./ih-" + self.config["version"] + "/scripts/" + executable)
            for arg in arguments:
                arglist.append(arg)
                if str(arguments[arg]) in inputs:
                    arglist.append(inputs[str(arguments[arg])]["file"])
                elif str(arguments[arg]) in outputs:
                    arglist.append(outputs[str(arguments[arg])]["file"])
                else:
                    if "osg" in self.config:
                        arglist.append("'" + str(arguments[arg]) + "'")
                    else:
                        arglist.append(str(arguments[arg]))
            self.jobs[dax][jobname].addArguments(*arglist)
            if dependencies:
                for depend in dependencies:
                    dax.depends(child = self.jobs[dax][jobname], parent = self.jobs[dax][depend])
            if label:
                self.jobs[dax][jobname].profile(Namespace.PEGASUS, "label", label)
            if walltime:
                self.jobs[dax][jobname].profile(Namespace.GLOBUS, "maxwalltime", walltime)
        return

    def create(self):
        """
            Creates a new pegasus submission directory based on the current timestamp,
            and populates it with all required information to submit a pegasus job.
            This function should be overloaded.
        """
        return


class Statistics(Workflow):

    """
        A class specifically for statistics workflow
        validation and submission.
    """

    def __init__(self, jobhome, basename, validOnly = False):
        super(Statistics, self).__init__(jobhome, basename)
        self.configfile = jobhome + "/input/" + conf.configFile
        self.statsfile = jobhome + "/input/" + conf.statsFile
        self.dbfile = jobhome + "/" + basename + "/output/" + conf.outputdb
        self.validOnly = validOnly
        self.rawFiles = {}
        self._loadInputFiles()
        return

    def _getImageTypes(self):
        return [x[0] for x in self.db.execute("select distinct imtype from images")]


    def _loadInputFiles(self):
        self.validator = ih.validator.Statistics(self.statsfile, self.configfile, self.dbfile)
        if not self.validator.isValid() or self.validOnly:
            self.validator.printErrors()
            sys.exit()
        else:
            self.stats = self.validator.workflow.data
            self.db = self.validator.db.conn
            self.config = self.validator.config.data
            self.rawFiles = self.validator.workflow.rawFiles
        return

    def _copyFiles(self):
        """
            Copies all input files to the correct location.
        """
        if not os.path.exists(self.basepath + "/input/stats"):
            os.makedirs(self.basepath + "/input/stats")
        shutil.copyfile(self.statsfile, self.basepath + "/input/templates/" + os.path.basename(self.statsfile))
        return

    def _loadFiles(self, loc):
        """
            Loads all files (input and output) into the dax and the self.files variable
        """
        self.files[self.dax] = {}
        self.files[self.dax]["raw"] = {"input": {}, "output": {}}
        self._addFile("output.db", "raw", "input", self.basepath + "/output/output.db")
        for type in self.stats["workflows"]:
            self.files[self.dax][type] = {"input": {}, "output": {}}
            for f in self.rawFiles[type]:
                shutil.copyfile(f, self.basepath + "/input/rawfiles/" + os.path.basename(f))
                self._addFile(os.path.basename(f), type, "input", self.basepath + "/input/rawfiles/" + os.path.basename(f))
        return

    def _loadExecutables(self, os="linux", arch="x86_64"):
        """
            Loads all executables (as specified in the conf) into
            the dax, as well as the internal self.executables variable
        """
        for ex in conf.valid:
            if "osg" in self.config:
                self.executables[ex] = Executable(name=ex, os=os, arch=arch, installed=False)
            else:
                self.executables[ex] = Executable(name=ex, os=os, arch=arch)
            self.executables[ex].addPFN(PFN("file://" + self.config["installdir"] + "/" + ex, "local"))
            #if "cluster" in self.config:
            #     self.executables[ex].addProfile(Profile(Namespace.PEGASUS, "clusters.size", self.config["cluster"]))
            self.dax.addExecutable(self.executables[ex])
        return

    def _loadNotify(self):
        if "notify" in self.config:
            self.dax.invoke(When.AT_END, self.basepath + "/input/stats/notify.sh")
            with open(self.basepath + "/input/stats/notify.sh", "w") as wh:
                notify = textwrap.dedent("""\
                        #!/bin/bash
                        %s/notification/email -t %s --report=pegasus-analyzer
                """ % (self.config["notify"]["pegasus_home"], self.config["notify"]["email"]))
                wh.write(notify)
            os.chmod(self.basepath + "/input/stats/notify.sh", 0755)
        return

    def _loadJobInputs(self, job, type, basename, extension, save = False):
        inputs = {}
        for i,input in enumerate(job["inputs"]):
            ftype = conf.valid[job["executable"]]["inputs"][i]
            if input in self.rawFiles[type]:
                inputs[input] = {"file": os.path.basename(input), "transfer": save}
            else:
                ex = extension if job["name"] == self.workflow["workflows"][type][0]["name"] else conf.fileExtensions[ftype]
                inputs[input] = {"file": basename + "_" + input + ex, "transfer": save}
        return inputs

    def _loadJobInputs(self, job, type, save = False):
        inputs = {"output.db": {"file": "output.db", "transfer": True}}
        for i,input in enumerate(job["inputs"]):
            ftype = conf.valid[job["executable"]]["inputs"][i]
            if input in self.rawFiles[type]:
                inputs[input] = {"file": os.path.basename(input), "transfer": save}
        return inputs

    def _createDax(self, loc):
        """
            Loads all jobs into the dax, and then writes the dax
            to input/loc/stats.dax
        """
        serial = []
        if "maxwalltime" in self.config:
            if "stats" in self.config["maxwalltime"]:
                maxwalltime = self.config["maxwalltime"]["stats"]
            else:
                maxwalltime = None
        else:
            maxwalltime = None
        for type in self.stats["workflows"]:
            for job in self.stats["workflows"][type]:
                jobname = type + "_" + job["name"]
                job["arguments"]["--intable"] = type + "_" + job["arguments"]["--intable"] if job["arguments"]["--intable"] != "images" else job["arguments"]["--intable"]
                job["arguments"]["--outtable"] = type + "_" + job["arguments"]["--outtable"]
                job["arguments"]["--db"] = "output.db"
                inputs = self._loadJobInputs(job, type)
                outputs = {}
                depends = [type + "_" + depend for depend in job["depends"]] if "depends" in job else serial
                if self.stats["workflows"][type].index(job) == len(self.stats["workflows"][type]) - 1:
                    serial = [jobname]
                else:
                    serial = []
                self._addJob(jobname, job["executable"], inputs, outputs, job["arguments"], depends, walltime = maxwalltime)
        with open(self.basepath + "/" + loc + "/stats.dax", "w") as wh:
            self.dax.writeXML(wh)
        return

    def _createReplica(self, loc):
        """
            Creates the pegasus configuration replica catalog.  input/conf.rc
        """
        with open(self.basepath + "/" + loc + "/conf.rc", "w") as wh:
            pegasusrc = textwrap.dedent("""\
                        pegasus.catalog.site = XML
                        pegasus.catalog.site.file = %s/sites.xml

                        pegasus.condor.logs.symlink = false

                        pegasus.transfer.links = true

                        pegasus.data.configuration = %s

                        """ % (self.basepath + "/" + loc))
            wh.write(pegasusrc)
        return

    def _createSites(self, loc):
        """
            Creates the pegasus site catalog.  input/sites.xml
        """
        with open(self.basepath + "/" + loc + "/sites.xml", "w") as wh:
            if "osg" in self.config:
                sites = """\
                <sitecatalog version="3.0" xmlns="http://pegasus.isi.edu/schema/sitecatalog" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://pegasus.isi.edu/schema/sitecatalog http://pegasus.isi.edu/schema/sc-3.0.xsd">
                    <site handle="local" arch="x86_64" os="LINUX">
                            <head-fs>
                                <scratch>
                                        <shared>
                                            <file-server protocol="file" url="file://" mount-point="%s"/>
                                            <internal-mount-point mount-point="%s"/>
                                        </shared>
                                    </scratch>
                                <storage>
                                        <shared>
                                            <file-server protocol="file" url="file://" mount-point="%s"/>
                                            <internal-mount-point mount-point="%s"/>
                                        </shared>
                                    </storage>
                            </head-fs>
                    """ % (self.basepath + "/work/stats/", self.basepath + "/work/stats/", self.basepath + "/output/", self.basepath + "/output/", self.basepath)
                sites += """\
                    </site>
                    <site handle="condorpool" arch="x86_64" os="LINUX">
                            <head-fs>
                                    <scratch />
                                    <storage />
                            </head-fs>
                """
            else:
                sites = """\
                 <sitecatalog xmlns="http://pegasus.isi.edu/schema/sitecatalog" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://pegasus.isi.edu/schema/sitecatalog http://pegasus.isi.edu/schema/sc-4.0.xsd" version="4.0">

                            <site  handle="local" arch="x86_64" os="LINUX">
                                <directory type="shared-scratch" path="%s">
                                    <file-server operation="all" url="file://%s" />
                                </directory>
                                <directory type="local-storage" path="%s">
                                    <file-server operation="all" url="file://%s" />
                                </directory>
                            """ % (self.basepath + "/work/stats/", self.basepath + "/work/stats/", self.basepath + "/output/", self.basepath + "/output/")
            for namespace in self.config["profile"]:
                for key in self.config["profile"][namespace]:
                    val = ":".join(self.config["profile"][namespace][key]) if "path" in key.lower() else self.config["profile"][namespace][key]
                    sites += """\n\t<profile namespace="%s" key="%s">%s</profile> """ % (namespace, key, val)
            sites += "</site></sitecatalog>"
            sites = sites.replace("\n","")
            wh.write("\n".join([line for line in xml.dom.minidom.parseString(sites).toprettyxml().split('\n') if line.strip()]))
        return

    def _createSubmit(self, loc):
        """
            Creates the pegasus submit script.  submit.sh
        """
        with open(self.basepath + "/" + loc + "/submit.sh", "w") as wh:

            submit = textwrap.dedent("""\
                    #!/bin/bash
                    %s
                    plan=`pegasus-plan \\
                    --conf "%s" \\
                    --sites "%s" \\
                    --dir "%s" \\
                    --output-site local \\
                    --dax "%s" \\
                    --randomdir \\""" % ("module unload python/2.7" if "osg" in self.config else "", self.basepath + "/" + loc + "/conf.rc", "condorpool" if "osg" in self.config else "local", self.basepath + "/work/stats", self.basepath + "/" + loc + "/stats.dax"))
            if "cluster" in self.config:
                submit += """--cluster horizontal \\\n"""
            submit += textwrap.dedent("""\
                    --submit`

                    status=`echo "$plan" | grep pegasus-status | tr -s ' '| cut -d ' ' -f 6`
                    echo -e "#!/bin/bash
                    pegasus-status -l $status" > status.sh
                    chmod 744 status.sh

                    remove=`echo "$plan" | grep pegasus-remove | tr -s ' '| cut -d ' ' -f 5`
                    echo -e "#!/bin/bash
                    pegasus-remove $remove" > remove.sh
                    chmod 744 remove.sh

                    echo "$plan"
                    echo "Alternatively, you can use the status & remove scripts in the current directory!"

                    """)
            wh.write(submit)
            os.chmod(self.basepath + "/" + loc + "/submit.sh", 0755)
        return

    def create(self):
        """
            Creates a new pegasus submission directory based on the current timestamp,
            and populates it with all required information to submit a pegasus job.
        """
        loc = "/input/stats/"
        self._createSetup()
        self._copyFiles()
        self._loadFiles(loc)
        self._loadExecutables()
        self._loadNotify()
        self._createDax(loc)
        self._createReplica(loc)
        self._createSites(loc)
        self._createSubmit(loc)
        return





class ImageProcessor(Workflow):

    """
        A class specifically for image processing workflow
        validation and submission.
    """

    def __init__(self, jobhome, basename = None, validOnly = False):
        """
            :param jobhome: The base directory for job submission.
            :type jobhome: str

            Creates a Workflow class based on the input directory.  Loads and validates all input files,
            and quits out if something doesn't exist or is defined innapropriately.
        """
        super(ImageProcessor, self).__init__(jobhome, basename)
        self.validOnly = validOnly
        self.workfile = jobhome + "/input/" + conf.workflowFile
        self.metafile = jobhome + "/input/" + conf.dbFile
        self.configfile = jobhome + "/input/" + conf.configFile
        self._loadInputFiles()
        self.exdax = ADAG("extract-" + self.jobname)
        self.jobs[self.exdax] = {}
        self.files[self.exdax] = {}
        return

    def _loadInputFiles(self):
        """
            Loads the input files into the appropriate variables
        """
        self.validator = ih.validator.ImageProcessor(self.workfile, self.configfile, self.metafile)
        if not self.validator.isValid() or self.validOnly:
            self.validator.printErrors()
            sys.exit()
        else:
            self.workflow = self.validator.workflow.data
            self.metadata = self.validator.db.conn
            self.config = self.validator.config.data
            self.rawFiles = self.validator.workflow.rawFiles
        return

    def _getImageTypes(self):
        """
            Convenience function to get all image types from the database.
        """
        return [x[0] for x in self.metadata.execute("select distinct imtype from images")]

    def _copyFiles(self):
        """
            Copies all input files to the correct location.
        """
        if not os.path.exists(self.basepath + "/input/imgproc"):
            os.makedirs(self.basepath + "/input/imgproc")
        shutil.copyfile(self.workfile, self.basepath + "/input/templates/" + os.path.basename(self.workfile))
        shutil.copyfile(self.configfile, self.basepath + "/input/templates/" + os.path.basename(self.configfile))
        shutil.copyfile(self.metafile, self.basepath + "/output/output.db")
        for type in self.rawFiles:
            for input in self.rawFiles[type]:
                shutil.copyfile(input, self.basepath + "/input/rawfiles/" + os.path.basename(input))
        if "osg" in self.config:
            shutil.copyfile(self.config["osg"]["tarball"], self.basepath + "/input/rawfiles/" + os.path.basename(self.config["osg"]["tarball"]))
        return

    def _loadFiles(self, loc):
        """
            Loads all files (input and output) into the dax and the self.files variable
        """
        with open(self.basepath + "/input/rawfiles/extract.json", "w") as wh:
            json.dump(self.workflow["extract"], wh)
        with open(self.basepath + "/" + loc + "/map.rc", "w") as wh:
            self.exInput = {"db": "img.db", "extract.json": "extract.json"}
            self.files[self.dax] = {}
            self.files[self.exdax] = {}
            self.files[self.exdax]["all"] = {"input": {}, "output": {}}
            self.files[self.dax]["raw"] = {"input": {}, "output": {}}
            self.files[self.exdax]["raw"] = {"input": {}, "output": {}}
            if "osg" in self.config:
                self._addFile("ih.tar.gz", "raw", "input", self.basepath + "/input/rawfiles/ih-" + self.config["version"] + ".tar.gz")
                self._addFile("ih.tar.gz", "raw", "input", self.basepath + "/input/rawfiles/ih-" + self.config["version"] + ".tar.gz", dax = self.exdax)
            self._addFile("img.db", "raw", "input", self.basepath + "/output/output.db")
            self._addFile("img.db", "all", "input", self.basepath + "/output/output.db", dax = self.exdax)
            self._addFile("img2.db", "raw", "output", self.basepath + "/output/img2.db")
            self._addFile("img2.db", "raw", "output", self.basepath + "/output/img2.db", dax = self.exdax)
            self._addFile("img3.db", "raw", "output", self.basepath + "/output/img3.db")
            self._addFile("img3.db", "raw", "output", self.basepath + "/output/img3.db", dax = self.exdax)
            self._addFile("img.log", "raw", "output", self.basepath + "/output/imgproc.log")
            self._addFile("extract.json", "raw", "input", self.basepath + "/input/rawfiles/extract.json")
            self._addFile("extract.json", "all", "input", self.basepath + "/input/rawfiles/extract.json", dax = self.exdax)
            for type in self.workflow["workflows"]:
                self.files[self.dax][type] = {"input": {}, "output": {}}
                for input in self.rawFiles[type]:
                    self._addFile(os.path.basename(input), type, "input", self.basepath + "/input/rawfiles/" + os.path.basename(input))
                wh.write("img.log file://" + self.basepath + "/output/imgproc.log pool=\"local\"\n")
                wh.write("img3.db file://" + self.basepath + "/output/img3.db pool=\"local\"\n")
                inputImages = [self.workflow["workflows"][type][0]["inputs"][i] for i,x in enumerate(conf.valid[self.workflow["workflows"][type][0]["executable"]]["inputs"]) if x == "image"]
                outputImages = [self.workflow["workflows"][type][z]["outputs"][i] for z in range(0, len(self.workflow["workflows"][type])) for i,x in enumerate(conf.valid[self.workflow["workflows"][type][z]["executable"]]["outputs"]) if x == "image"]
                outputFiles = dict((self.workflow["workflows"][type][z]["outputs"][i], conf.fileExtensions[conf.valid[self.workflow["workflows"][type][z]["executable"]]["outputs"][i]]) for z in range(0, len(self.workflow["workflows"][type])) for i,x in enumerate(conf.valid[self.workflow["workflows"][type][z]["executable"]]["outputs"]) if x != "image" and x != "none" and len(self.workflow["workflows"][type][z]["outputs"]) > i)
                for row in self.metadata.execute("select pegasusid, experiment, id, date, imgname, path from images where imtype=?", (type,)):
                    realname = row["path"].split("/")[-1].split(".")[0]
                    #derivedPath = row["experiment"].replace(" ","%20") + "/" + row["id"].replace(" ","%20") + "/" + row["date"].replace(" ","%20") + "/" + type + "/" + row["imgname"].replace(" ","%20") + "/"
                    derivedPath = row["experiment"].replace(" ","") + "/" + row["id"].replace(" ","") + "/" + row["date"].replace(" ","") + "/" + type + "/" + row["imgname"].replace(" ","") + "/"
                    for input in inputImages:
                        if "osg" in self.config:
                            self._addFile(row["pegasusid"] + "_" + input + "." + row["path"].split(".")[1], type, "input", row["path"], derivedPath = derivedPath + row["pegasusid"])
                        else:
                            self._addFile(derivedPath + row["pegasusid"] + "_" + input + "." + row["path"].split(".")[1], type, "input", row["path"], derivedPath = derivedPath + row["pegasusid"])
                    for output in outputImages:
                        if output in self.workflow["extract"]["workflows"][type]["inputs"]:
                            self.exInput[derivedPath + row["pegasusid"] + "_" + output + ".png"] = derivedPath + row["pegasusid"] + "_" + output + ".png"
                            self._addFile(derivedPath + row["pegasusid"] + "_" + output + ".png", "all", "input", self.basepath + "/output/" + derivedPath + row["pegasusid"] + "_" + output + ".png", dax = self.exdax)
                        self._addFile(derivedPath + row["pegasusid"] + "_" + output + ".png", type, "output")
                        wh.write(derivedPath + row["pegasusid"] + "_" + output + ".png file://" + self.basepath + "/output/" + derivedPath + row["pegasusid"].replace(" ","%20") + "_" + output + ".png pool=\"local\"\n")
                    for output in outputFiles:
                        outname = output + outputFiles[output]
                        self._addFile(derivedPath + row["pegasusid"] + "_" + outname, type, "output")
                        wh.write(derivedPath + row["pegasusid"] + "_" + outname + " file://" + self.basepath + "/output/" + derivedPath.replace("_","%20") + outname + " pool=\"local\"\n")
        return

    def _loadNotify(self):
        if "notify" in self.config:
            self.dax.invoke(When.AT_END, self.basepath + "/input/imgproc/notify.sh")
            self.exdax.invoke(When.AT_END, self.basepath + "/input/imgproc/notify.sh")
            with open(self.basepath + "/input/imgproc/notify.sh", "w") as wh:
                notify = textwrap.dedent("""\
                        #!/bin/bash
                        %s/notification/email -t %s --report=pegasus-analyzer
                """ % (self.config["notify"]["pegasus_home"], self.config["notify"]["email"]))
                wh.write(notify)
            os.chmod(self.basepath + "/input/imgproc/notify.sh", 0755)
        return

    def _loadExecutables(self, os="linux", arch="x86_64"):
        """
            Loads all executables (as specified in the conf) into
            the dax, as well as the internal self.executables variable
        """
        for ex in conf.valid:
            if "osg" in self.config:
                self.executables[ex] = Executable(name=ex, os=os, arch=arch, installed = False)
            else:
                self.executables[ex] = Executable(name=ex, os=os, arch=arch)
            self.executables[ex].addPFN(PFN("file://" + self.config["installdir"] + "/" + ex, "local"))
            #if "cluster" in self.config:
            #    val = int(self.config["cluster"] * conf.valid[ex]["weight"]) if "weight" in conf.valid[ex] else self.config["cluster"]
            #    self.executables[ex].addProfile(Profile(Namespace.PEGASUS, "clusters.size", val))
            self.dax.addExecutable(self.executables[ex])
            self.exdax.addExecutable(self.executables[ex])
        return

    def _loadJobInputs(self, job, type, basename, extension, save = False):
        inputs = {}
        for i,input in enumerate(job["inputs"]):
            ftype = conf.valid[job["executable"]]["inputs"][i]
            if input in self.rawFiles[type]:
                inputs[input] = {"file": os.path.basename(input), "transfer": save}
            else:
                ex = extension if job["name"] == self.workflow["workflows"][type][0]["name"] else conf.fileExtensions[ftype]
                if "osg" in self.config:
                    if input == "base":
                        inputs[input] = {"file": os.path.basename(basename) + "_" + input + ex, "transfer": save}
                    else:
                        inputs[input] = {"file": basename + "_" + input + ex, "transfer": save}
                else:
                    inputs[input] = {"file": basename + "_" + input + ex, "transfer": save}
        return inputs

    def _loadJobOutputs(self, job, type, basename, save):
        outputs = {}
        for i,output in enumerate(job["outputs"]):
            if output != "none":
                outputs[output] = {"file": basename + "_" + output + conf.fileExtensions[conf.valid[job["executable"]]["outputs"][i]], "transfer": save}
        return outputs

    #def _loadJobOutputs(self, job, type, basename):
    #    return dict((output, basename + "_" + output + conf.fileExtensions[conf.valid[job["executable"]]["outputs"][i]]) for i,output in enumerate(job["outputs"]) if output != "none")

    def _createDax(self, loc):
        """
            Loads all jobs into the dax, and then writes the dax
            to input/workflow.dax
        """
        exDep = {}
        exInput = {}
        clusternum = {}
        meancluster = {}
        excluster = {}

        if "maxwalltime" in self.config:
            if "images" in self.config["maxwalltime"]:
                maxwalltime = self.config["maxwalltime"]["images"]
            else:
                maxwalltime = None
        else:
            maxwalltime = None

        save = True if "save-steps" in self.workflow["options"] else False
        for type in self.workflow["workflows"]:
            exDep[type] = [[]]
            exInput[type] = [{}]
            jobnum = -1
            skipFirst = True
            clusternum[type] = 0
            meancluster[type] = 0
            excluster[type] = 0
            exNames = self.workflow["extract"]["workflows"][type]["depends"]
            for infile in [x for x in self.files[self.dax][type]["input"] if "." + x.split(".")[1] in conf.imageExtensions]:
                if "cluster" in self.config:
                    jobnum += 1
                    if jobnum == self.config["cluster"]:
                        jobnum = 0
                        clusternum[type] += 1
                    if ((clusternum[type] * 100 + jobnum) % int(self.config["cluster"] * 0.3)) == 0:
                        meancluster[type] += 1
                    if (jobnum % 50) == 0 and not skipFirst:
                        exDep[type].append([])
                        exInput[type].append({})
                        excluster[type] += 1
                    skipFirst = False
                extension = "." + infile.split(".")[1]
                realname = self.files[self.dax][type]["input"][infile]["path"].split("/")[-1].split(".")[0]
                derivedPath = self.files[self.dax][type]["input"][infile]["derivedPath"]
                for stepnum,job in enumerate(self.workflow["workflows"][type]):
                    jobname = derivedPath + "_" + job["name"]
                    inputs = self._loadJobInputs(job, type, derivedPath, extension)
                    if job["name"] in exNames:
                        outputs = self._loadJobOutputs(job, type, derivedPath, True)
                        exDep[type][excluster[type]].append(jobname)
                        reqFile = derivedPath + "_" + self.workflow["extract"]["workflows"][type]["inputs"][0] + ".png"
                        exInput[type][excluster[type]][reqFile] = {"file": reqFile, "transfer": save}
                        if "--dimfromroi" in self.workflow["extract"]["workflows"][type]["arguments"]:
                            if os.path.isfile(self.workflow["extract"]["workflows"][type]["arguments"]["--dimfromroi"]):
                                roiFile = os.path.basename(self.workflow["extract"]["workflows"][type]["arguments"]["--dimfromroi"])
                            else:
                                roiFile = derivedPath + "_" + self.workflow["extract"]["workflows"][type]["arguments"]["--dimfromroi"] + ".json"
                            exInput[type][excluster[type]][roiFile] = {"file": roiFile, "transfer": save}
                    else:
                        outputs = self._loadJobOutputs(job, type, derivedPath, save)
                    depends = [derivedPath + "_" + depend for depend in job["depends"]] if "depends" in job else []
                    if job["executable"] == "ih-meanshift":
                        self._addJob(jobname, job["executable"], inputs, outputs, job["arguments"], depends, label = type + "_step" + str(stepnum) + "_cluster" + str(meancluster[type]) if "cluster" in self.config else None, walltime = maxwalltime)
                    else:
                        self._addJob(jobname, job["executable"], inputs, outputs, job["arguments"], depends, label = type + "_step" + str(stepnum) + "_cluster" + str(clusternum[type]) if "cluster" in self.config else None, walltime = maxwalltime)


        maprc = open(self.basepath + "/" + loc + "/map.rc", "a")
        binDep = []
        aggIn = {}
        aggIn2 = {}
        for type in self.workflow["workflows"]:
            for q in range(0, excluster[type] + 1):
                arguments = self.workflow["extract"]["workflows"][type]["arguments"]
                if "--input" in arguments:
                    del arguments["--input"]
                if "--dimfromroi" in arguments:
                    del arguments["--dimfromroi"]
                    arguments["--dimfromroi"] = " ".join([x for x in exInput[type][q].keys() if ".json" in x])
                if "histogram-bin" in self.workflow["extract"]:
                    if type in [imtype for key in self.workflow["extract"]["histogram-bin"]["--group"] for imtype in self.workflow["extract"]["histogram-bin"]["--group"][key]]:
                        arguments["--colors"] = ""
                arguments["--db"] = "db"
                arguments["--createdb"] = ""
                arguments["--inputs"] = " ".join([x for x in exInput[type][q].keys() if ".png" in x])
                self._addFile(type + str(q) + ".db", type, "output")
                self._addFile(type + str(q) + "_2.db", type, "output")
                self._addJob(type + "_extract" + str(q), "ih-extract-multi", exInput[type][q], {"db": {"file": type + str(q) + ".db", "transfer": False}}, arguments, exDep[type][q], walltime = 180)
                self._addJob(type + "_extract" + str(q), "ih-extract-multi", exInput[type][q], {"db": {"file": type + str(q) + ".db", "transfer": False}}, arguments, [], dax = self.exdax, walltime = 180)
                maprc.write(type + str(q) + ".db" + " file://" + self.basepath + "/output/" + type + str(q) + ".db" + " pool=\"local\"\n")
                binDep.append(type + "_extract" + str(q))
                aggIn[type + str(q) + ".db"] = {"file": type + str(q) + ".db", "transfer": False}
                aggIn2[type + str(q) + "_2.db"] = {"file": type + str(q) + "_2.db", "transfer": False}
        aggIn["db"] = {"file": "img.db", "transfer": False}
        self._addJob("sql_aggregate1", "ih-sql-aggregate", aggIn, {"img2.db": {"file": "img2.db", "transfer": False if "histogram-bin" in self.workflow["extract"] else True}}, {"--db": "db", "--output": "img2.db", "--inputs": " ".join([aggIn[x]["file"] for x in aggIn if x != "db"])}, binDep, walltime = 180)
        self._addJob("sql_aggregate1", "ih-sql-aggregate", aggIn, {"img2.db": {"file": "img2.db", "transfer": False if "histogram-bin" in self.workflow["extract"] else True}}, {"--db": "db", "--output": "img2.db", "--inputs": " ".join([aggIn[x]["file"] for x in aggIn if x != "db"])}, binDep, dax = self.exdax, walltime = 180)

        if "histogram-bin" in self.workflow["extract"]:
            outputs = {}
            for name in self.workflow["extract"]["histogram-bin"]["--group"]:
                self._addFile(name + "_hist_bins.json", "raw", "output")
                maprc.write(name + "_hist_bins.json" + " file://" + self.basepath + "/output/" + name + "_hist_bins.json" + " pool=\"local\"\n")
                outputs[name + "_hist_bins.json"] = {"file": name + "_hist_bins.json", "transfer": True}
            self._addJob("bin_creation", "ih-stats-histogram-bin", {"db": {"file": "img2.db", "transfer": True}, "extract.json": {"file": "extract.json", "transfer": False}}, outputs, {"--db": "db", "--options": "extract.json", "--intable": "images", "--outtable": "histogramBins", "--jsonwrite": "", "--overwrite": ""}, ["sql_aggregate1"])
            self._addJob("bin_creation", "ih-stats-histogram-bin", {"db": {"file": "img2.db", "transfer": True}, "extract.json": {"file": "extract.json", "transfer": False}}, outputs, {"--db": "db", "--options": "extract.json", "--intable": "images", "--outtable": "histogramBins", "--jsonwrite": "", "--overwrite": ""}, ["sql_aggregate1"], dax = self.exdax)

            binDep = []
            map = {}

            for group in self.workflow["extract"]["histogram-bin"]["--group"]:
                for type in self.workflow["extract"]["histogram-bin"]["--group"][group]:
                    map[type] = group

            for type in self.workflow["workflows"]:
                for q in range(0, excluster[type] + 1):
                    arguments = {}
                    arguments["--db"] = "db"
                    arguments["--copydb"] = "copydb"
                    arguments["--inputs"] = " ".join(exInput[type][q].keys())
                    exInput[type][q]["db"] = {"file": type + str(q) + ".db", "transfer": False}
                    exInput[type][q]["binfile"] = {"file": map[type] + "_hist_bins.json", "transfer": False}
                    arguments["--bins"] = "binfile"
                    self._addJob(type + "_extractBins" + str(q), "ih-extract-multi", exInput[type][q], {"copydb": {"file": type + str(q) + "_2.db", "transfer": False}}, arguments, ["bin_creation"], walltime = 300)
                    self._addJob(type + "_extractBins" + str(q), "ih-extract-multi", exInput[type][q], {"copydb": {"file": type + str(q) + "_2.db", "transfer": False}}, arguments, ["bin_creation"], dax = self.exdax, walltime = 300)
                    binDep.append(type + "_extractBins" + str(q))
            aggIn2["db"] = {"file": "img2.db", "transfer": False}
            self._addJob("sql_aggregate2", "ih-sql-aggregate", aggIn2, {"img3.db": {"file": "img3.db", "transfer": True}}, {"--db": "db", "--output": "img3.db", "--inputs": " ".join([aggIn2[x]["file"] for x in aggIn2 if x != "db"])}, binDep, walltime = 180)
            self._addJob("sql_aggregate2", "ih-sql-aggregate", aggIn2, {"img3.db": {"file": "img3.db", "transfer": True}}, {"--db": "db", "--output": "img3.db", "--inputs": " ".join([aggIn2[x]["file"] for x in aggIn2 if x != "db"])}, binDep, dax = self.exdax, walltime = 180)

        z = 2 if "histogram-bin" in self.workflow["extract"] else 1
        indb = "img3.db" if "histogram-bin" in self.workflow["extract"] else "img.db"
        self._addJob("error-log", "ih-error-log", {"db": {"file": indb, "transfer": True}}, {"output": {"file": "img.log", "transfer": True}}, {"--db": "db", "--output": "output"}, ["sql_aggregate" + str(z)])
        with open(self.basepath + "/" + loc + "/workflow.dax", "w") as wh:
            self.dax.writeXML(wh)
        return

    def _createExtract(self, loc):
        """
            Creates the extraction step only dax!
        """
        #self._addJob("extractOnly", "ih-extract-all", self.exInput, {}, {"--db": "db", "--options": "extract.json"}, dax = self.exdax)
        with open(self.basepath + "/" + loc + "/extract.dax", "w") as wh:
            self.exdax.writeXML(wh)
        return

    def _createReplica(self, loc):
        """
            Creates the pegasus configuration replica catalog.  input/conf.rc
        """
        with open(self.basepath + "/" + loc + "/conf.rc", "w") as wh:
            pegasusrc = textwrap.dedent("""\
                        pegasus.catalog.site = XML
                        pegasus.catalog.site.file = %s/sites.xml

                        pegasus.condor.logs.symlink = false

                        pegasus.transfer.links = true

                        pegasus.data.configuration = %s

                        pegasus.dir.storage.mapper = Replica
                        pegasus.dir.storage.mapper.replica = File
                        pegasus.dir.storage.mapper.replica.file = %s/map.rc
                        """ % (self.basepath + "/" + loc, "nonsharedfs" if "osg" in self.config else "sharedfs", self.basepath + "/" + loc))
            if "osg" in self.config:
                pegasusrc += textwrap.dedent("""\
                    pegasus.stagein.clusters = 4
                    pegasus.stageout.clusters = 4
                    pegasus.transfer.threads = 4
                    pegasus.transfer.lite.threads = 4

                    dagman.maxjobs = 200
                """)
            wh.write(pegasusrc)
        return

    def _createSites(self, loc):
        """
            Creates the pegasus site catalog.  input/sites.xml
        """
        with open(self.basepath + "/" + loc + "/sites.xml", "w") as wh:
            if "osg" in self.config:
                userName = getpass.getuser()
                sites = """\
                <sitecatalog version="4.0" xmlns="http://pegasus.isi.edu/schema/sitecatalog" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://pegasus.isi.edu/schema/sitecatalog http://pegasus.isi.edu/schema/sc-4.0.xsd">
                    <site handle="local" arch="x86_64" os="LINUX">
                        <directory type="shared-scratch" path="%s">
                            <file-server operation="all" url="file://%s" />
                        </directory>
                        <directory type="local-storage" path="%s">
                            <file-server operation="all" url="file://%s" />
                        </directory>
                        <profile namespace="pegasus" key="SSH_PRIVATE_KEY">%s</profile>
                    </site>
                    <site handle="stash" arch="x86_64" os="LINUX">
                        <directory type="shared-scratch" path="%s">
                            <!-- <file-server operation="get" url="stash://%s"/> -->
                            <file-server operation="all" url="scp://%s@login02.osgconnect.net/%s"/>
                        </directory>
                    </site>
                    <site handle="isi_workflow" arch="x86_64" os="LINUX">
                        <directory type="shared-scratch" path="/nfs/ccg4/scratch-purge-no-backups/workflow.isi.edu/scratch2/%s/scratch">
                            <file-server operation="get" url="http://workflow.isi.edu/scratch2/%s/scratch"/>
                            <file-server operation="put" url="scp://%s@workflow.isi.edu/nfs/ccg4/scratch-purge-no-backups/workflow.isi.edu/scratch2/%s/scratch"/>
                        </directory>
                    </site>
                    <site handle="condorpool" arch="x86_64" os="LINUX">



                    """ % (self.basepath + "/work/imgproc/", self.basepath + "/work/imgproc/", self.basepath + "/output/", self.basepath + "/output/", self.config["osg"]["ssh"], self.basepath + "/staging/", "/".join((self.basepath + "/staging/").split("/")[2:]), userName, self.basepath + "/staging/", userName, userName, userName, userName)
            else:
                sites = """\
                 <sitecatalog xmlns="http://pegasus.isi.edu/schema/sitecatalog" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://pegasus.isi.edu/schema/sitecatalog http://pegasus.isi.edu/schema/sc-4.0.xsd" version="4.0">

                            <site  handle="local" arch="x86_64" os="LINUX">
                                <directory type="shared-scratch" path="%s">
                                    <file-server operation="all" url="file://%s" />
                                </directory>
                                <directory type="local-storage" path="%s">
                                    <file-server operation="all" url="file://%s" />
                                </directory>
                            """ % (self.basepath + "/work/imgproc/", self.basepath + "/work/imgproc/", self.basepath + "/output/", self.basepath + "/output/")
            for namespace in self.config["profile"]:
                for key in self.config["profile"][namespace]:
                    val = ":".join(self.config["profile"][namespace][key]) if "path" in key.lower() else self.config["profile"][namespace][key]
                    sites += """\n\t<profile namespace="%s" key="%s">%s</profile> """ % (namespace, key, val)
            sites += "</site></sitecatalog>"
            sites = sites.replace("\n","")
            wh.write("\n".join([line for line in xml.dom.minidom.parseString(sites).toprettyxml().split('\n') if line.strip()]))
        return

    def _createSubmit(self, loc):
        """
            Creates the pegasus submit script.  submit.sh
        """
        with open(self.basepath + "/" + loc + "/submit.sh", "w") as wh:
            submit = textwrap.dedent("""\
                    #!/bin/bash
                    if [ "$1" = "--extract-only" ] || [ "$1" = "--extract" ] || [ "$1" = "-e" ]; then
                        DAX="%s"
                    else
                        DAX="%s"
                    fi
                    plan=`pegasus-plan \\
                    --conf "%s" \\
                    --sites "%s" \\
                    --dir "%s" \\
                    --output-site local \\
                    --dax "$DAX" \\
                    --randomdir \\
                    """ % (self.basepath + "/" + loc + "/extract.dax", self.basepath + "/" + loc + "/workflow.dax", self.basepath + "/" + loc + "/conf.rc", "condorpool" if "osg" in self.config else "local", self.basepath + "/work/imgproc"))
            if "cluster" in self.config:
                submit += """--cluster label \\\n"""
            if "osg" in self.config:
                submit += """--staging-site stash \\\n"""
                submit += """--staging isi_workflow \\\n"""
                submit += """--cleanup leaf \\\n"""
            submit += textwrap.dedent("""\
                    --submit`

                    status=`echo "$plan" | grep pegasus-status | tr -s ' '| cut -d ' ' -f 6`
                    echo -e "#!/bin/bash
                    pegasus-status -l $status" > status.sh
                    chmod 744 status.sh

                    remove=`echo "$plan" | grep pegasus-remove | tr -s ' '| cut -d ' ' -f 5`
                    echo -e "#!/bin/bash
                    pegasus-remove $remove" > remove.sh
                    chmod 744 remove.sh

                    echo "$plan"
                    echo "Alternatively, you can use the status & remove scripts in the current directory!"

                    """)
            wh.write(submit)
            os.chmod(self.basepath + "/" + loc + "/submit.sh", 0755)
        return

    def create(self):
        """
            Creates a new pegasus submission directory based on the current timestamp,
            and populates it with all required information to submit a pegasus job.
        """
        print "Generating workflow.  Please wait."
        loc = "/input/imgproc/"
        self._createSetup()
        self._copyFiles()
        self._loadFiles(loc)
        self._loadExecutables()
        self._loadNotify()
        self._createDax(loc)
        self._createExtract(loc)
        self._createReplica(loc)
        self._createSites(loc)
        self._createSubmit(loc)
        return


class ImageLoader:
    """
        This should handle all meta-data definitions
    """

    def __init__(self, template, output, validOnly = False, overwrite = False):
        """
            :param template: Path to input template file, should be valid json.
            :type template: str
        """
        self.templatePath = os.path.abspath(template)
        self.err = ""
        self.output = output + "/input/"
        try:
            open(self.output + "/images.db")
        except IOError:
            self.err += "Path Error: Cannot open output db file. \n"
        try:
            self.log = open(self.output + "/crawl.log", "w")
        except IOError:
            self.err += "Path Error: Cannot open log file. \n"
        self.validator = ih.validator.ImageLoader(self.templatePath)
        if not self.validator.isValid() or validOnly:
            self.validator.printErrors()
            sys.exit()
        self.overwrite = overwrite
        self.template = self.validator.data
        self.template["order"].insert(0, "pegasusid")

        self.count = {}
        self.depth = len(self.template["path"].split("/")) - 1
        self.structure = self._dictTemplate()
        self.data = []
        return

    def _success(self):
        if self.overwrite:
            print "Data crawled!"
            print "Use ih-run to submit your jobs."
        else:
            print "Directory setup successful!"
            print "Define the required templates in " + self.output + "."
            print "Then use ih-run to submit your jobs."
        return

    def _dictTemplate(self):
        """
            Creates the first of two intermediary dictionaries for crawling.  This relates
            identifiers in the path, to a specified depth, as well as operators to split
            the value at that depth.
        """
        m = [x for x in re.findall(r"%(\w+)%", self.template["path"]) if x != "null"]
        sp = self.template["path"].split("/")
        d = {}
        for key in m:
            d[key] = {}
            d[key]["depth"] = [n for n,x in enumerate(sp) if key in x][0]
            d[key]["split"] = []
            val = sp[d[key]["depth"]]
            for operator in [" ", "_", "-", "."]:
                if operator in val:
                    b = val.split(operator)
                    x = [n for n,x in enumerate(b) if key in x][0]
                    d[key]["split"].append({"operator": operator, "index": x})
                    val = b[x]
        return d

    def _loadStructure(self, splitPath):
        """
            Creates the second of two intermediary dictionaries for crawling.
            This utilizes the template created in _dictTemplate, and creates
            a dictionary with actual values instead of structure.
        """
        d ={}
        for key in self.structure:
            val = splitPath[self.structure[key]["depth"]]
            for operator in self.structure[key]["split"]:
                val = val.split(operator["operator"])[operator["index"]]
            d[key] = val
        return d

    def _loadDataFile(self, dict, structure, key):
        """
            Loads data from a data file.  If the specified key isn't in the file,
            write 'UNKNOWN' instead.
        """
        keyVal = self._convertReferences(structure, self.template["data"][key]["key"])
        if keyVal in self.filedata[self.template["data"][key]["value"]]:
            dict[key] = self.filedata[self.template["data"][key]["value"]][keyVal]
        else:
            dict[key] = "UNKNOWN"
        return

    def _loadDataValue(self, dict, structure, key):
        """
            Loads a data value.
        """
        val = self._convertReferences(structure, self.template["data"][key]["value"])
        if "case" in self.template["data"][key]:
            if self.template["data"][key]["case"] == "lower":
                val = val.lower()
            elif self.template["data"][key]["case"] == "upper":
                val = val.upper()

        if "translate" in self.template["data"][key]:
            if val in self.template["translations"][key]:
                val = self.template["translations"][key][val]
        dict[key] = val

        return

    def _loadDataDate(self, dict, structure, key):
        """
            Loads a date.
        """
        val = self._convertReferences(structure, self.template["data"][key]["value"])
        format = "".join([x.replace(x, "%" + x) if x in conf.dateFormat else x for x in self.template["data"][key]["format"]])
        val = datetime.datetime.strptime(val, format).strftime("%Y-%m-%d")
        dict[key] = val
        return

    def _convertReferences(self, structure, val):
        """
            Replaces all references ('%%') to actual values.
        """
        idList = [x for x in re.findall(r"%(\w+)%", val) if x != "null"]
        for identifier in idList:
            if identifier in structure:
                val = val.replace("%" + identifier + "%", structure[identifier])
        return val

    def _loadData(self, path):
        """
            Loads all data for a particular path.
        """
        temp = {}
        final = {}
        splitPath = path.split("/")
        structure = self._loadStructure(splitPath)
        for key in self.template["data"]:
            d = {
                "value": self._loadDataValue,
                "file": self._loadDataFile,
                "date": self._loadDataDate
            }[self.template["data"][key]["type"]](final, structure, key)
        final["path"] = path
        if final["imtype"] not in self.count:
            self.count[final["imtype"]] = 1
        else:
            self.count[final["imtype"]] += 1
        final["pegasusid"] = final["imtype"] + str(self.count[final["imtype"]])
        return final

    def _loadFiles(self):
        """
            Reads all data from all specified files.
        """
        self.filedata = {}
        for key in self.template["data"]:
            if self.template["data"][key]["type"] == "file":
                if self.template["data"][key]["value"] not in self.filedata:
                    self.filedata[self.template["data"][key]["value"]] = {}
                    with open(self.template["data"][key]["value"], "r") as rh:
                        for line in rh.readlines():
                            info = line.strip().split(",")
                            self.filedata[self.template["data"][key]["value"]][info[self.template["data"][key]["keyColumn"]]] = info[self.template["data"][key]["valueColumn"]]
        return

    def crawl(self):
        """
            Recursively walks through directories in base, and loads
            the appropriate data.
        """
        self._loadFiles()
        for root, dirs, files in os.walk(self.template["base"]):
            arr = root.split("/")
            depth = len(arr)
            if (depth == self.depth):
                for f in files:
                    if f[-len(self.template["filetype"]):] == self.template["filetype"] and f[0] != ".":
                        try:
                            d = self._loadData(root + "/" + f)
                            self.data.append(d)
                        except Exception as e:
                            self.log.write("Could not load file from path: '%s/%s'\n" % (root, f))
        return

    def write(self):
        """
            Writes the data loaded from crawl into csv format based on 'order'
        """
        if self.data:
            conn = sqlite3.connect(self.output + "/images.db")
            tablestr = "(pegasusid PRIMARY KEY"
            for x in self.template["order"]:
                if x != "pegasusid":
                    tablestr += "," + str(x)
            tablestr += ")"
            if self.overwrite:
                conn.execute("DROP TABLE IF EXISTS images")
                conn.commit()
            conn.execute("CREATE TABLE images " + tablestr)
            writedata = []
            for row in self.data:
                writedata.append(tuple([str(row[x]) for x in self.template["order"]]))
            query = "insert into images " + str(tuple([str(x) for x in self.template["order"]])) + " values (" + ("?," * len(self.template["order"]))[:-1] + ")"
            conn.executemany(query, writedata)
            conn.commit()
            if not self.overwrite:
                shutil.copyfile(self.templatePath, self.output + "/crawl.json")
        else:
            print "Call crawl first!"
        return

class DirectorySetup:

    def __init__(self, jobhome):
        """
            :param jobhome: The base directory to setup a job.
            :type jobhome: str
        """
        if not os.path.isdir(os.path.dirname(os.path.dirname(os.path.abspath(jobhome) + "/"))):
            print "Can't create job folder, path doesn't exist!"
            sys.exit()
        self.jobhome = jobhome
        return

    def _makeDir(self, dirpath):
        """
            Makes a directory if it doesn't exist.  Catches and
            prints out common errors.
        """
        try:
            os.makedirs(dirpath)
        except OSError as e:
            raise Exception({
                errno.EEXIST: "Directory " + dirpath + " already exists!",
                errno.EACCES: "You don't have permission to create directory "  + dirpath + ".",
            }.get(e.errno, "Error for directory " + dirpath + " error:" + str(e)))
        return

    def _makeFile(self, filepath):
        """
            Opens a file to create it, uses append mode
            so it doesn't overwrite any existing files.
        """
        try:
            open(filepath, "a")
        except OSError as e:
            raise Exception({

            }.get(e, "Unsepcified error for file " + filepath))
        return

    def setup(self):
        """
            Creates the directory structure needed to submit jobs,
            and creates empty template files needed for job submission.
        """
        self._makeDir(self.jobhome)
        self._makeDir(self.jobhome + "/input/")
        for fname in conf.jobFiles:
            self._makeFile(self.jobhome + "/input/" + fname)
        return
