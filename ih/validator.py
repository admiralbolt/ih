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
import textwrap
import shutil
import errno
import copy
import traceback
from Pegasus.DAX3 import *

class Validator(object):
    """
    A very, very generic validator.
    """
    def __init__(self, f, type):
        self.err = ""
        if not os.path.isfile(f):
            self.err += "Path Error: Input '%s' doesn't exist.\n" % (f,)
        if not self.err:
            if type == "file":
                with open(f, "r") as rh:
                    try:
                        self.data = json.load(rh)
                    except Exception as e:
                        self.err += "Json Error: File '%s', %s\n" % (f, str(e))
            elif type == "db":
                self.conn = sqlite3.connect(f)
                self.conn.row_factory = sqlite3.Row
                try:
                    result = self.conn.execute("select * from images")
                    if not result.fetchone():
                        self.err += "Database Error: No information in images table\n"
                except Exception as e:
                    self.err += "Database Error: %s\n" % (str(e), )
            else:
                self.err += "Validator Error: Invalid type, must be either 'file' or 'db'\n"
            self.rawFiles = {}
            self.type = type
            self.validate()
        return

    def printErrors(self):
        """
            Prints out errors from validation and then exits.
        """
        if self.err:
            print self.err.strip()
        else:
            print "No Validation Errors."
        return

    def isValid(self):
        """
            A convenience function.  If validation ran successfully,
            return True, else return False.
        """
        if not self.err:
            return True
        else:
            return False

    def validate(self):
        """
            This function should be overloaded
        """
        return

class Workflow(object):

    def __init__(self, template, config, database):
        self.workflow = Validator(template, "file")
        self.config = Validator(config, "file")
        self.db = Validator(database, "db")
        self.err = ""
        if self.workflow.isValid() and self.db.isValid() and self.config.isValid():
            self.validate()
        else:
            self.err += "Workflow components did not validate individually. \n"
            self.err += self.workflow.err
            self.err += self.config.err
            self.err += self.db.err
        return

    def isValid(self):
        """
        A convenience function.
        """
        if not self.err:
            return True
        else:
            return False

    def printErrors(self):
        if self.err:
            print self.err.strip()
        else:
            print "No Validation Errors"
        return

    def _loadOverwriteArgument(self, job, arg):
        job["arguments"][arg] = conf.valid[job["executable"]]["arguments"][arg]["value"]
        return

    def _loadDerivedArgument(self, job, arg, jtype):
        key = conf.valid[job["executable"]]["arguments"][arg]["key"]
        index = conf.valid[job["executable"]]["arguments"][arg]["index"]
        if key in job:
            if isinstance(job[key], list):
                if index <= len(job[key]) - 1:
                    if "value" in conf.valid[job["executable"]]["arguments"][arg]:
                        job["arguments"][arg] = conf.valid[job["executable"]]["arguments"][arg]["value"]
                    else:
                        job["arguments"][arg] = job[key][index]
                else:
                    if "required" in conf.valid[job["executable"]]["arguments"][arg]:
                        self.err += "Workflow, Argument Error: Type '%s' job '%s', derived argument '%s' requires index '%s' for definition '%s', no such index. \n" % (jtype, job["name"], arg, index, key)
            else:
                if "required" in conf.valid[job["executable"]]["arguments"][arg]:
                    self.err += "Workflow, Argument Error: Type '%s' job '%s', derived argument '%s' requires definition for '%s' to be of type list, definition is of type '%s'. \n" % (jtype, job["name"], arg, key, type(job[key]).__name__)
        else:
            if "required" in conf.valid[job["executable"]]["arguments"][arg]:
                self.err += "Workflow, Argument Error: Type '%s' job '%s', derived argument '%s' requires job definition for '%s', no such definition. \n" % (jtype, job["name"], arg, key)
        return

    def _validateArgumentType(self, job, arg, type):
        if arg in job["arguments"]:
            if not isinstance(job["arguments"][arg], {
                "list": list,
                "string": (str, unicode),
                "dict": dict,
                "numeric": (int, long, float),
                "exist": object,
                "derived": object
            }[conf.valid[job["executable"]]["arguments"][arg]["type"]]):
                self.err += "Workflow, Argument Error: Type '%s' job '%s', argument '%s' given value '%s', should be of type '%s'. \n" % (type, job["name"], arg, job["arguments"][arg], conf.valid[job["executable"]]["arguments"][arg]["type"])
            else:
                if isinstance(job["arguments"][arg], list) and "join" in conf.valid[job["executable"]]["arguments"][arg]:
                    job["arguments"][arg] = conf.valid[job["executable"]]["arguments"][arg]["join"].join(job["arguments"][arg])
                elif (isinstance(job["arguments"][arg], dict) or isinstance(job["arguments"][arg], list)):
                    job["arguments"][arg] = str(job["arguments"][arg])
                elif (isinstance(job["arguments"][arg], (str, unicode)) and conf.valid[job["executable"]]["arguments"][arg]["type"] and "complex" in conf.valid[job["executable"]]["arguments"][arg]):
                    job["arguments"][arg] = '"' + job["arguments"][arg] + '"'
        return

    def _validateArgumentRequired(self, job, arg, type):
        if "required" in conf.valid[job["executable"]]["arguments"][arg]:
            if arg in job["arguments"]:
                if job["arguments"][arg] == "":
                    self.err += "Workflow, Argument Error: Type '%s' job '%s', has empty required argument '%s' \n" % (type, job["name"], arg)
            else:
                self.err += "Workflow, Argument Error: Type '%s' job '%s', requires argument '%s', no such argument found. \n" % (type, job["name"], arg)
        return

    def _validateArgumentDictionary(self, job, arg, type):
        arglist = job["arguments"][arg] if isinstance(job["arguments"][arg], list) else [job["arguments"][arg]]
        if conf.valid[job["executable"]]["arguments"][arg]["validation"] == "dictionary":
            d = conf.valid[job["executable"]]["arguments"][arg]["value"] if "key" not in conf.valid[job["executable"]]["arguments"][arg] else conf.valid[job["executable"]]["arguments"][arg]["value"].get(job["arguments"][conf.valid[job["executable"]]["arguments"][arg]["key"]])
            for val in arglist:
                if val not in d:
                    self.err += "Workflow, Argument Error: Type '%s' job '%s', has invalid value '%s' for argument '%s'. \n" % (type, job["name"], val, arg)
        return

    def _validateArgumentList(self, job, arg, type):
        arglist = job["arguments"][arg] if isinstance(job["arguments"][arg], list) else [job["arguments"][arg]]
        l = conf.valid[job["executable"]]["arguments"][arg]["value"]
        for val in arglist:
            if val not in l:
                self.err += "Workflow, Argument Error: Type '%s' job '%s', has invalid value '%s' for argument '%s'. \n" % (type, job["name"], val, arg)
        return

    def _validateArguments(self, job, type):
        if not job["arguments"]:
            job["arguments"] = {}
        for arg in conf.valid[job["executable"]]["arguments"]:
            if conf.valid[job["executable"]]["arguments"][arg]["type"] == "derived":
                self._loadDerivedArgument(job, arg, type)
            if "required" in conf.valid[job["executable"]]["arguments"][arg] or arg in job["arguments"]:
                if conf.valid[job["executable"]]["arguments"][arg]["type"] == "overwrite":
                    self._loadOverwriteArgument(job, arg)
                else:
                    self._validateArgumentRequired(job, arg, type)
                    self._validateArgumentType(job, arg, type)

                if "validation" in conf.valid[job["executable"]]["arguments"][arg]:
                    if arg in job["arguments"]:
                        validate = {
                            "dictionary": self._validateArgumentDictionary,
                            "list": self._validateArgumentList
                        }[conf.valid[job["executable"]]["arguments"][arg]["validation"]](job, arg, type)

        for arg in job["arguments"]:
            if arg not in conf.valid[job["executable"]]["arguments"]:
                self.err += "Workflow, Argument Error: Type '%s' job '%s', has invalid argument '%s'. \n" % (type, job["name"], arg)
        return

    def _validateDependencies(self, job, type):
        try:
            names = [x["name"] for x in self.workflow.data["workflows"][type]]
            unres = copy.deepcopy(job["inputs"])
            for input in job["inputs"]:
                if os.path.isfile(input):
                    unres.remove(input)
                    self.workflow.rawFiles[type].append(input)
                elif input in self.workflow.data["workflows"][type][0]["inputs"]:
                    unres.remove(input)
            if "depends" in job:
                for dependency in job["depends"]:
                    if dependency in names:
                        i = names.index(dependency)
                        for output in self.workflow.data["workflows"][type][i]["outputs"]:
                            if output in unres:
                                unres = [x for x in unres if x != output]
                    else:
                        self.err += "Workflow, Dependency Error: Type '%s' job '%s' depends on job '%s', no such job exists. \n" % (type, job["name"], dependency)
            for val in set(unres):
                self.err += "Workflow, Input Error: Type '%s' job '%s' depends on input '%s'.  Cannot find matching output, or raw file. \n" % (type, job["name"], val)
            for x,input in enumerate(job["inputs"]):
                if "depends" in job:
                    for dependency in job["depends"]:
                        if dependency in names:
                            i = names.index(dependency)
                            if input in self.workflow.data["workflows"][type][i]["outputs"]:
                                j = self.workflow.data["workflows"][type][i]["outputs"].index(input)
                                if conf.valid[job["executable"]]["inputs"][x] != conf.valid[self.workflow.data["workflows"][type][i]["executable"]]["outputs"][j]:
                                    self.err += "Workflow, Dependency Error: Type '%s' job '%s' input '%s' in position '%s' should be of type '%s', however, output '%s' in position '%s' of job '%s' is of type '%s'. \n" %  (type, job["name"], input, x, conf.valid[job["executable"]]["inputs"][x], self.workflow.data["workflows"][type][i]["outputs"][j], j, self.workflow.data["workflows"][type][i]["name"], conf.valid[self.workflow.data["workflows"][type][i]["executable"]]["outputs"][j])
        except:
            self.printErrors()
            print "Validation halted at type '%s' job '%s'.  Fix errors before re-running. \n" % (type, job)
            sys.exit()
        return

    def _validateDB(self):
        """
        Valides the input database file.
        DIFFERENT FOR WORKFLOWS
        OVERLOAD THIS
        """

        return

    def _validateConfig(self):
        """
        Validates the input configuration template.
        SAME FOR BOTH TYPES OF WORKFLOWS
        """
        if self.config.data:
            if set(conf.templateKeys["config"]["required"]) < set(self.config.data.keys()):
                if not os.path.isdir(self.config.data["installdir"]):
                    self.err += "Config, Path Error: Path '%s' specified for 'installdir' does not exist. \n" % (self.config.data["installdir"],)
                for key in self.config.data:
                    if key not in conf.templateKeys["config"]["required"] and key not in conf.templateKeys["config"]["optional"]:
                        self.err += "Config, Key Error: Invalid key '%s' specified.  Allowed keys are '%s'. \n" % (key, conf.templateKeys["config"]["required"] + conf.templateKeys["config"]["optional"])
                if "maxwalltime" in self.config.data:
                    for key in self.config.data["maxwalltime"]:
                        if key not in conf.templateKeys["config"]["maxwalltime"]["optional"]:
                            self.err += "Config, Key Error: Invalid key '%s' specified for 'maxwalltime'.  Allowed keys are '%s'. \n" % (key, conf.templateKeys["config"]["maxwalltime"]["optional"])
                if "notify" in self.config.data:
                    for key in conf.templateKeys["config"]["notify"]["required"]:
                        if key not in self.config.data["notify"]:
                            self.err += "Config, Key Error: Required key '%s' not specified for 'notify'.  \n" % (key,)
                        elif key == "pegasus_home":
                            if not os.path.isfile(self.config.data["notify"]["pegasus_home"] + "/notification/email"):
                                self.err += "Config, Path Error: Required key '%s' has invalid value.  Path '%s' does not exist." % (key, self.config.data["notify"]["pegasus_home"] + "/notification/email")
                for namespace in self.config.data["profile"]:
                    for key in self.config.data["profile"][namespace]:
                        if "path" in key.lower():
                            if not isinstance(self.config.data["profile"][namespace][key], list):
                                self.config.data["profile"][namespace][key] = [self.config.data["profile"][namespace][key]]
                            if "osg" in self.config.data and namespace == "env":
                                # We ignore osg enviornment variables
                                pass
                            else:
                                for path in self.config.data["profile"][namespace][key]:
                                    if not os.path.isdir(path):
                                        self.err += "Config, Path Error: Path '%s' specified for namespace '%s', key '%s' does not exist. \n" % (path, namespace, key)
                if "osg" in self.config.data:
                    if "profile" not in self.config.data:
                        self.config.data["profile"] = {}
                    if "env" not in self.config.data["profile"]:
                        self.config.data["profile"]["env"] = {}
                    for key in conf.templateKeys["config"]["osg"]["required"]:
                        if key not in self.config.data["osg"]:
                            self.err += "Config, OSG Key Error: Specifying 'osg' requires the key '%s' to be defined." % (key,)
                        elif not os.path.isfile(self.config.data["osg"][key]):
                            self.err += "Config, OSG Path Error: Path '%s' specified for key '%s' does not exist. \n" % (self.config.data["osg"][key], key)
            else:
                self.err += "Config, Template Error: Config file does not have all the required keys:" + str(conf.templateKeys["config"]["required"]) + " \n"
        else:
            self.err += "Config, Load Error: Could not load configuration info. \n"
        return

    def _getImageTypes(self):
        return [x["imtype"] for x in self.db.conn.execute("select distinct imtype from images")]

    def validate(self):
        """
        This should be overloaded again.
        """
        return


class ImageProcessor(Workflow):

    def __init__(self, template, config, database):
        super(ImageProcessor, self).__init__(template, config, database)
        return

    def validate(self):
        """
            Validates all inputted files.  Because the workflow is
            dependenet on the config and metadata, workflow validation
            is only done if config and metadata validate successfully.
        """
        if not self.err:
            self._validateConfig()
            self._validateDB()
            if not self.err:
                self._validateWorkflow()
        return

    def _validateWorkflowJobs(self):
        types = self._getImageTypes()
        for type in self.workflow.data["workflows"]:
            if type not in types:
                self.err += "Imgproc, Type Error: Workflow definition exists for type '%s', no images have been loaded for that type. \n" % (type,)
            self.workflow.rawFiles[type] = []
            names = [x["name"] for x in self.workflow.data["workflows"][type]]
            if len(names) == len(set(names)):
                for job in self.workflow.data["workflows"][type]:
                    if set(conf.templateKeys["imgproc"]["job"]["required"]) <= set(job.keys()):
                        for key in job.keys():
                            if key not in conf.templateKeys["imgproc"]["job"]["required"] and key not in conf.templateKeys["imgproc"]["job"]["optional"]:
                                self.err += "Imgproc, Key Error: Job '%s' has invalid key '%s' specified.  Allowed keys are '%s'. \n" % (job["name"], key, conf.templateKeys["imgproc"]["job"]["required"] + conf.templateKeys["imgproc"]["job"]["optional"])
                        if job["executable"] in conf.valid:
                            if not os.path.isfile(self.config.data["installdir"] + "/" + job["executable"]):
                                self.err += "Imgproc, Path Error: Job '%s' executable '%s' does not exist. \n" % (job["name"], self.config.data["installdir"] + "/" + job["executable"])
                            if conf.valid[job["executable"]]["type"] == "imgproc":
                                self._validateArguments(job, type)
                                self._validateDependencies(job, type)
                            else:
                                self.err += "Imgproc, Executable Error: Job '%s' has invalid executable '%s' specified.  Only image processing scripts are allowed. \n" % (job["name"], job["executable"])
                        else:
                            self.err += "Imgproc, Executable Error: Job '%s' has non-existant executable '%s' specified. \n" % (job["name"], job["executable"])
                    else:
                        self.err += "Imgproc, Key Error: Job '%s' doesn't have all required keys: '%s'.  \n" % (job["name"], conf.templateKeys["imgproc"]["job"]["required"])
            else:
                self.err += "Imgproc, Name Error: Cannot parse ambiguous workflow.  Workflow defined for type '%s' contains multiple jobs with the same name. \n" % (type,)
        return

    def _validateWorkflowOptions(self):
        if set(conf.templateKeys["imgproc"]["options"]["required"]) <= set(self.workflow.data["options"].keys()):
            for key in self.workflow.data["options"]:
                if key not in conf.templateKeys["imgproc"]["options"]["required"] and key not in conf.templateKeys["imgproc"]["options"]["optional"]:
                    self.err += "Imgproc, Option Error: Invalid option '%s' specified. \n " % (key,)
        else:
            self.err += "Imgproc, Option Error: Option specification doesn't have all required keys: '%s'. \n " % (conf.templateKeys["imgproc"]["options"]["required"],)
        return

    def _validateWorkflowExtract(self):
        if set(conf.templateKeys["imgproc"]["extract"]["required"]) <= set(self.workflow.data["extract"].keys()):
            for key in self.workflow.data["extract"]:
                if key not in conf.templateKeys["imgproc"]["extract"]["required"] and key not in conf.templateKeys["imgproc"]["extract"]["optional"]:
                    self.err += "Imgproc, Extract Error: Invalid option '%s' specified. \n " % (key,)

            ## Manual hist-bin validation ##
            if "histogram-bin" in self.workflow.data["extract"]:
                hist = {}
                hist["executable"] = "ih-stats-histogram-bin"
                hist["inputs"] = ["images"]
                hist["outputs"] = ["none"]
                hist["name"] = "histogramBin"
                hist["arguments"] = self.workflow.data["extract"]["histogram-bin"].copy()
                self._validateArguments(hist, "extract")
                if not self.err:
                    if set(self.workflow.data["extract"]["histogram-bin"]["--group"].keys()) != set(self.workflow.data["extract"]["histogram-bin"]["--channels"].keys()):
                        self.err += "Imgproc, Extract Error: Histogram bin group names don't match between '--group' and '--channels'. \n"
                else:
                    pass

            if not self.err:
                for type in self.workflow.data["extract"]["workflows"]:
                    if type in self.workflow.data["workflows"]:
                        if "--dimfromroi" in self.workflow.data["extract"]["workflows"][type]["arguments"]:
                            fpath = self.workflow.data["extract"]["workflows"][type]["arguments"]["--dimfromroi"]
                            if os.path.isfile(fpath):
                                self.workflow.rawFiles[type].append(fpath)
                        job = self.workflow.data["extract"]["workflows"][type]
                        job["executable"] = "ih-extract"
                        job["outputs"] = ["none"]
                        job["name"] = type + "_extract"
                        self._validateArguments(job, type)
                        self._validateDependencies(job, type)
                    else:
                        self.err += "Imgproc, Extract Error: Extraction specified for type '%s'.  No processing workflow defined for that type." % (type,)
            else:
                pass
        else:
            self.err += "Imgproc, Extract Error: Extract specification doesn't have all required keys: '%s'. \n" % (conf.templateKeys["imgproc"]["extract"]["required"],)
        return


    def _validateWorkflow(self):
        """
            Validates the input workflow template, making sure all required
            keys are inputted, and all names resolve
        """
        if set(conf.templateKeys["imgproc"]["required"]) <= set(self.workflow.data.keys()):
            for key in self.workflow.data.keys():
                if key not in conf.templateKeys["imgproc"]["required"] and key not in conf.templateKeys["imgproc"]["optional"]:
                    self.err += "Imgproc, Key error: Invalid key '%s' specified.  Allowed keys are '%s'. \n" % (key, conf.templateKeys["imgproc"]["required"] + conf.templateKeys["imgproc"]["optional"])
            try:
                self._validateWorkflowJobs()
                self._validateWorkflowOptions()
                self._validateWorkflowExtract()
            except Exception as e:
                print traceback.format_exc()
                self.err += "Validation halted.  Fix current issues before re-running. \n"
                self.printErrors()
        else:
            self.err += "Imgproc, Template Error: Workflow file does not have all the required keys: '%s'. \n" % (conf.templateKeys["imgproc"]["required"],)
        return

    def _validateDB(self):
        """
            Validates the inputted metadata db, ensuring the appropriate
            column names are in the database.
        """
        if self.db:
            cols = [row[1] for row in self.db.conn.execute("PRAGMA table_info(images)")]
            if set(conf.outHeaders) <= set(cols):
                testpath = self.db.conn.execute("select path from images limit 0,1").next()[0]
                if not os.path.isfile(testpath):
                    self.err += "DB, Path Error: Test file: '%s' could not be found. \n" % (testpath,)
            else:
                 self.err += "DB, Key Error: Meta-data file does not have all the required headers: %s \n" % (str(conf.outHeaders),)
        else:
            self.err += "DB, Load Error: Could not connect to meta-data db. \n"
        return



class Statistics(Workflow):

    def __init__(self, template, config, database):
        super(Statistics, self).__init__(template, config, database)

        return

    def validate(self):
        """
            Validates all inputted files.  Because the workflow is
            dependenet on the config and metadata, workflow validation
            is only done if config and metadata validate successfully.
        """
        if not self.err:
            self._validateConfig()
            self._validateDB()
            if not self.err:
                self._validateWorkflow()
        return

    def _validateDB(self):
        try:
            result = self.db.conn.execute("select * from images")
            cols = [row[1] for row in self.db.conn.execute("PRAGMA table_info(images)")]
            if not set(cols) > set(conf.outHeaders):
                self.err += "Stats, Database Error: Database specified does not contain any numeric columns, process images first. \n"
            if not set(conf.outHeaders) <= set(cols):
                self.err += "Stats, Database Error: Database specified does not contain all the required column names: '%s'. \n " % (conf.outHeaders,)
            if not result.fetchone():
                self.err += "Stats, Database Error: Database specified does not contain an image table with any entries. \n"
        except sqlite3.DatabaseError:
            self.err += "Stats, Database Error: File specified is not a valid database file. \n"
        return

    def _validateWorkflow(self):
        if self.workflow.data:
            for key in self.workflow.data.keys():
                if key not in conf.templateKeys["stats"]["required"] and key not in conf.templateKeys["stats"]["optional"]:
                    self.err += "Stats, Key error: Invalid key '%s' specified.  Allowed keys are '%s'. \n" % (key, conf.templateKeys["stats"]["required"] + conf.templateKeys["stats"]["optional"])
            for type in self.workflow.data["workflows"]:
                self.workflow.rawFiles[type] = []
                names = [x["name"] for x in self.workflow.data["workflows"][type]]
                if len(names) == len(set(names)):
                    for job in self.workflow.data["workflows"][type]:
                        if set(conf.templateKeys["stats"]["job"]["required"]) <= set(job.keys()):
                            for key in job.keys():
                                if key not in conf.templateKeys["stats"]["job"]["required"] and key not in conf.templateKeys["stats"]["job"]["optional"]:
                                    self.err += "Stats, Key Error: Job '%s' has invalid key '%s' specified.  Allowed keys are '%s'. \n" % (job["name"], key, conf.templateKeys["stats"]["job"]["required"] + conf.templateKeys["stats"]["job"]["optional"])
                            if job["executable"] in conf.valid:
                                if conf.valid[job["executable"]]["type"] == "statistics":
                                    if os.path.isfile(self.config.data["installdir"] + "/" + job["executable"]):
                                        self._validateArguments(job, type)
                                        self._validateDependencies(job, type)
                                    else:
                                        self.err += "Stats, Path Error: Job '%s' executable '%s' does not exist. \n" % (job["name"], self.config["installdir"] + "/" + job["executable"])
                                else:
                                    self.err += "Stats, Executable Error: Job '%s' has invalid executable '%s' specified.  Only statistics scripts are allowed. \n" % (job["name"], job["executable"])
                            else:
                                self.err += "Stats, Executable Error: Job '%s' executable '%s' is not a valid executable. \n" % (job["name"], job["executable"])
                        else:
                            self.err += "Stats, Key Error: Job '%s' doesn't have all required keys: '%s'. \n" % (job["name"], conf.templateKeys["stats"]["job"]["required"])
                else:
                    self.err += "Stats, Name Error: Cannot parse ambiguous workflow.  Workflow defined for type '%s' contains multiple jobs with the same name. \n" % (type,)
        else:
            self.err += "Stats, Load Error: Could not load stats file. \n"
        return

class ImageLoader(Validator):

    def __init__(self, f):
        super(ImageLoader, self).__init__(f, "file")
        return

    def validate(self):
        """
            Validates the given template.
        """
        if self.isValid():
            if set(conf.templateKeys["loading"]["required"]) <= set(self.data.keys()):
                for key in self.data:
                    if key not in conf.templateKeys["loading"]["required"] and key not in conf.templateKeys["loading"]["optional"]:
                        self.err += "Loader, Key Error: Invalid key '%s' specified. \\n" % (key,)

                if not self.err:
                    for key in self.data:
                        d = {
                            "path": self._validatePath,
                            "base": self._validateBase,
                            "data": self._validateData,
                            "translations": self._validateTranslations,
                            "order": self._validateOrder,
                            "filetype": self._validateFtype,
                        }[key]()
            else:
                self.err += "Loader, Key Error: Not all required keys specified: '%s' \n" % (conf.templateKeys["loading"]["required"])
        return

    def _validateFtype(self):
        if self.data["filetype"]:
            if self.data["filetype"] not in conf.imageExtensions:
                self.err += "Loader, File Error: Value '%s' specified for 'filetype' is invalid.  Must be on of '%s'. \n" % (self.data["filetype"], conf.imageExtensions)
        else:
            self.err += "Loader, File Error: No value specified for 'filetype'. \n"

    def _validatePath(self):
        """
            Validates the path.  Because the path contains potential references, path existence
            cannot be checked at this stage.
        """
        if not self.data["path"]:
            self.err += "Loader, Path Error: No value specified for 'path'.\n"
        return

    def _validateBase(self):
        """
            Validates the base walk path.  Checks existence of a value, if the value
            is a subset of path, and if the path exists.
        """
        if self.data["base"]:
            if self.data["base"] in self.data["path"]:
                if not os.path.exists(self.data["base"]):
                    self.err += "Loader, Base Error: Value for 'base' is not a valid path. \n"
            else:
                self.err += "Loader, Base Error: Value for 'base' is not a subset of 'path'. \n"
        else:
            self.err += "Loader, Base Error: No value specified for 'base'.\n"
        pass

    def _validateData(self):
        """
            Validates the data!  Uses a seperate function for each data type.
        """
        if self.data["data"]:
            for key in self.data["data"]:
                if "type" in self.data["data"][key]:
                    if self.data["data"][key]["type"] in conf.templateKeys["loading"]["data"]["type"]:
                        if key in self.data["order"]:
                            d = {
                                "value": self._validateDataValue,
                                "file": self._validateDataFile,
                                "date": self._validateDataDate
                            }[self.data["data"][key]["type"]](key)
                        else:
                            self.err += "Loader, Data Error: Definition for data key '%s', no corresponding definition in 'order'. \n" % (key,)
                    else:
                        self.err += "Loader, Data Error: Invalid type '%s' specified for data key '%s', must be one of '%s'. \n" % (self.data["data"][key]["type"], key, conf.templateKeys["loading"]["data"]["type"])
                else:
                    self.err += "Loader, Data Error: No value specified for 'type' of data key '%s'. \n" % (key,)
        else:
            self.err += "Loader, Value Error: No value specified for 'data'. \n"
        pass

    def _validateDataValue(self, key):
        """
            Validates type 'value'.  Values can be combinations of hard-coded text
            as well as references to path identifiers  Checks existence of a value,
            if all the references are valid, and if translation is specified, that
            translations exist.
        """
        if self.data["data"][key]["value"]:
            if set(conf.templateKeys["loading"]["data"]["value"]["required"]) <= set(self.data["data"][key].keys()):

                for subkey in self.data["data"][key]:
                    if subkey not in conf.templateKeys["loading"]["data"]["value"]["required"] and subkey not in conf.templateKeys["loading"]["data"]["value"]["optional"]:
                        self.err += "Loader, Data Value Error: Invalid key '%s' specified for data key '%s'. \n" % (subkey,key)

                m = re.findall(r"%(\w+)%", self.data["data"][key]["value"])
                for val in m:
                    if "%" + val + "%" not in self.data["path"]:
                        self.err += "Loader, Data Value Reference Error: Could not reference identifier '%s' for data key '%s'. \n" % (val, key)
                if "translate" in self.data["data"][key]:
                    if key not in self.data["translations"]:
                        self.err += "Loader, Data Value Translation Error: Can't translate data key '%s', no translation specified. \n" % (key,)
                if "case" in self.data["data"][key]:
                    if self.data["data"][key]["case"] not in ["lower", "upper"]:
                        self.err += "Loader, Data Value Error: Case for key '%s' is defined as '%s', should be either 'lower' or 'upper'. \n" % (key, self.data["data"][key]["case"])
            else:
                print set(conf.templateKeys["loading"]["data"]["value"]["required"])
                print set(self.data["data"][key].keys())
                self.err += "Loader, Data Value Error: Data key '%s' does not have all required keys '%s'. \n" % (key, conf.templateKeys["loading"]["data"]["value"]["required"])
        else:
            self.err += "Loader, Data Value Error: No value specified for data key '%s'. \n " % (key,)
        return

    def _validateDataFile(self, key):
        """
            Validates type 'file'.  Checks to ensure that a file is specified,
            that file exists, and that a value is specified for key, keyColumn,
            and valueColumn.  Assumes the file is of csv format.
        """
        if set(conf.templateKeys["loading"]["data"]["file"]["required"]) <= set(self.data["data"][key].keys()):

            for subkey in self.data["data"][key]:
                if subkey not in conf.templateKeys["loading"]["data"]["file"]["required"] and subkey not in conf.templateKeys["loading"]["data"]["file"]["optional"]:
                    self.err += "Loader, Data File Error: Invalid key '%s' specified for data key '%s'. \n" % (subkey, key)

            if os.path.exists(self.data["data"][key]["value"]):
                with open(self.data["data"][key]["value"], "r") as rh:
                    firstline = rh.readline()
                    sep = self.data["data"][key]["separator"] if "separator" in self.data["data"][key] else ","
                    maxlength = len(firstline.split(sep))
                    if maxlength <= self.data["data"][key]["keyColumn"]:
                        self.err += "Loader, Data File Error: Key column for data key '%s' out of range. \n" % (key,)
                    if maxlength <= self.data["data"][key]["valueColumn"]:
                        self.err += "Loader, Data File Error: Value column for data key '%s' out of range. \n" % (key,)
            else:
                self.err += "Loader, Data Filer Error: File '%s' specified for data key '%s' does not exist. \n" % (self.data["data"][key]["value"], key)

            m = re.findall(r"%(\w+)%", self.data["data"][key]["key"])
            for val in m:
                if "%" + val + "%" not in self.data["path"]:
                    self.err += "Loader, Data Value Reference Error: Could not reference identifier '%s' for data key '%s'. \n" % (val, key)
        else:
            self.err += "Loader, Data File Error: Data key '%s' does not have all required keys '%s'. \n" % (key, conf.templateKeys["loading"]["data"]["file"]["required"])
        return

    def _validateDataDate(self, key):
        """
            Validates type 'date'.  Checks to ensure that a value exists, a format
            exists, and that the format is semi-valid.  True validity of format is
            checked when values are given in the crawling step.
        """
        if set(conf.templateKeys["loading"]["data"]["date"]["required"]) <= set(self.data["data"][key].keys()):

            for subkey in self.data["data"][key]:
                if subkey not in conf.templateKeys["loading"]["data"]["date"]["required"] and subkey not in conf.templateKeys["loading"]["data"]["date"]["optional"]:
                    self.err += "Loader, Data Date Error: Invalid key '%s' specified for data key '%s'. \n" % (subkey, key)

            if not set(self.data["data"][key]["format"]) <= set(conf.dateFormat + conf.dateSep):
                self.err += "Loader, Data Date Error: Invalid values in data key '%s', format only supports '%s'. \n" % (key, conf.dateFormat + conf.dateSep)

            m = re.findall(r"%(\w+)%", self.data["data"][key]["value"])
            for val in m:
                if "%" + val + "%" not in self.data["path"]:
                    self.err += "Loader, Data Value Reference Error: Could not reference identifier '%s' for data key '%s'. \n" % (val, key)
        else:
            self.err += "Loader, Data Date Error: Data key '%s' does not have all required keys '%s'. \n" % (key, conf.templateKeys["loading"]["data"]["date"]["required"])
        return

    def _validateTranslations(self):
        """
            Nothing to see here, move along.
        """
        for key in self.data["translations"]:
            if key not in self.data["data"]:
                self.err += "Loader, Translation Error: Translation defined for '%s', however, no such data value exists. \n" % (key,)
        return

    def _validateOrder(self):
        """
            Validates the order -- the order you want to write values to the csv.
            Checks existence of a value, as well as ensuring all values specified
            have corresponding data values.
        """
        if self.data["order"]:
            if not set(self.data["order"]) == set(self.data["data"].keys() + ["path"]):
                self.err += "Loader, Order Error: Order must contain ALL data keys AND 'path'. \n"
        else:
            self.err += "Loader, Order Error: No value specified for order. \n"
        return
