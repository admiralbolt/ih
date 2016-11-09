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
import math
import os
import sqlite3
import conf
import datetime
import numpy as np
import pandas
import ih.imgproc
import cv2
import json
import traceback
import shutil
import subprocess
import itertools
from scipy import stats

class Stats:

    def __init__(self, db):
        self.db = db
        self.conn = self._openConnection()
        return

    def _openConnection(self, db = None):
        db = self.db if not db else db
        if os.path.isfile(db):
            conn = sqlite3.connect(db, check_same_thread = False)
            conn.row_factory = sqlite3.Row
            result = conn.execute("select pegasusid from images limit 0,1")
            if not result.fetchone():
                raise Exception("Database '%s' has no entries!" % (db,))
            # Have to enable foreign keys EVERY time.
            conn.execute("PRAGMA foreign_keys = ON")
            conn.commit()
        else:
            raise Exception("Database file '%s' does not exist." % (db,))
        return conn

    def _closeConnection(self, conn = None):
        conn = self.conn if not conn else conn
        conn.close()
        return

    def _tableExists(self, tablename, conn = None):
        conn = self.conn if not conn else conn
        result = conn.execute("select name from sqlite_master where type='table' and name=?", (tablename,))
        if not result.fetchone():
            return False
        else:
            return True

    def _validate(self, funcname, intable, outtable, overwrite, conn = None):
        conn = self.conn if not conn else conn
        if funcname in conf.statsColumns:
            if self._tableExists(intable):
                cols = [x[1] for x in conn.execute("PRAGMA table_info('" + intable + "')")]
                if set(conf.statsColumns[funcname]["required"]) <= set(cols):
                    if self._tableExists(outtable, conn) and not overwrite:
                        raise Exception("Output table '" + outtable + "' already exists.")
                else:
                    raise Exception("Table '" + intable + "' doesn't have all the required columns: '" + str(conf.statsColumns[funcname]["required"]) + "'.")
            else:
                raise Exception("Table '" + intable + "' doesn't exist.")
        else:
            raise Exception("Function '" + funcname + "' doesn't exist.")
        return

    def _massage(self, table, headers, imtypes = None, conn = None):
        conn = self.conn if not conn else conn
        if not imtypes:
            imtypes = self._getImageTypes(table, conn)
        elif not isinstance(imtypes, list):
            imtypes = [imtypes]

        for header in headers:
            self.conn.execute("update " + table + " set " + header + "=? where " + header + " is null and (" + "or".join(["imtype=?" for x in imtypes]) + ")", (0,) + tuple(imtypes))
        self.conn.commit()
        return

    def _columnExists(self, column, tablename, conn = None):
        conn = self.conn if not conn else conn
        if column in [row["name"] for row in self.conn.execute("PRAGMA table_info('" + tablename + "')")]:
            return True
        else:
            return False

    def _addColumn(self, column, tablename = "images", conn = None):
        conn = self.conn if not conn else conn
        if not self._columnExists(column, tablename, conn):
            conn.execute("alter table '" + tablename + "' add column " + column + ";")
            conn.commit()
        return

    def _addKeyColumn(self, parent, parentCol, child, childCol, conn = None):
        conn = self.conn if not conn else conn
        if parentCol not in [row["name"] for row in conn.execute("PRAGMA table_info('" + parent + "');")] and childCol in [row["name"] for row in conn.execute("PRAGMA table_info('" + child + "');")]:
            conn.execute("alter table '" + parent + "' add column '" + parentCol + "' REFERENCES '" + child + "'('" + childCol + "');")
            conn.commit()
        return

    def _createTable(self, funcname, intable, outtable, overwrite, conn = None):
        conn = self.conn if not conn else conn
        tablestr = "(pegasusid INTEGER PRIMARY KEY"
        cols = [x[1] for x in conn.execute("pragma table_info('" + intable + "')")]
        if "all" not in conf.statsColumns[funcname]["exclude"]:
            for col in cols:
                if col not in conf.statsColumns[funcname]["exclude"] and col[:3] != "ref":
                    tablestr += "," + str(col)
        for col in conf.statsColumns[funcname]["add"]:
            tablestr += "," + str(col)
        tablestr += ")"
        if overwrite:
            if conf.statsColumns[funcname]["ref"]:
                if self._columnExists("ref_" + outtable, intable, conn):
                    conn.execute("update " + intable + " set ref_" + outtable + "=? where ref_" + outtable + " is not null", (None,))
                    conn.commit()
            conn.execute("DROP TABLE IF EXISTS " + outtable)
            conn.commit()
        conn.execute("CREATE TABLE " + outtable + " " + tablestr)
        conn.commit()
        if conf.statsColumns[funcname]["ref"]:
            self._addKeyColumn(intable, "ref_" + outtable, outtable, "pegasusid", conn)
        return

    def _getHeaders(self, table, conn = None):
        conn = self.conn if not conn else conn
        return [str(x[1]) for x in conn.execute("pragma table_info(" + table + ")") if x[1] != "pegasusid"]

    def _getIds(self, table, conn = None):
        conn = self.conn if not conn else conn
        return [str(x[0]) for x in conn.execute("select distinct id from " + table)]

    def _getImageTypes(self, table, conn = None):
        conn = self.conn if not conn else conn
        return [str(x[0]) for x in conn.execute("select distinct imtype from " + table)]

    def _getDates(self, table, conn = None):
        conn = self.conn if not conn else conn
        return [str(x[0]) for x in conn.execute("select distinct date from " + table)]

    def _checkNull(self, value):
        return True if value is None or str(value).lower() == "none" else False

    def _listToSql(self, l):
        return str(l).replace("[", "(").replace("]", ")")

    def _loadLemnaData(self, dataFile, dataHeaders):
        """
        :param dataFile: The input dataFile
        :type dataFile: str
        :param dataHeaders: The input data headers
        :type dataHeaders: dict

        dataHeaders should be:
        {
            "id": "Snapshot ID Tag",
            "date": "Snapshot Time Stamp",
            "dateFormat": "%m/%d/%y",
            "metric": "Projected Shoot Area [pixels]"
        }
        """
        if os.path.isfile(dataFile):
            if all(key in dataHeaders for key in ["id", "date", "dateFormat", "metric"]):
                with open(dataFile) as rh:
                    lines = rh.readlines()
                    firstline = lines[0].strip().split(",")
                    if dataHeaders["id"] in firstline:
                        if dataHeaders["date"] in firstline:
                            if dataHeaders["metric"] in firstline:
                                idIndex = firstline.index(dataHeaders["id"])
                                dateIndex = firstline.index(dataHeaders["date"])
                                metricIndex = firstline.index(dataHeaders["metric"])
                                lemnaData = {}
                                for line in lines[1:]:
                                    info = line.strip().split(",")
                                    if (info[metricIndex] != "NA"):
                                        id = info[idIndex][-8:]
                                        date = datetime.datetime.strptime(info[dateIndex].split()[0], dataHeaders["dateFormat"]).strftime("%Y-%m-%d")
                                        try:
                                            metric = float(info[metricIndex])
                                            if id not in lemnaData:
                                                lemnaData[id] = {}
                                            if date not in lemnaData[id]:
                                                lemnaData[id][date] = {}
                                            lemnaData[id][date]["metric"] = metric
                                        except:
                                            pass
                                return lemnaData
                            else:
                                raise Exception("Metric Column: ",dataHeaders["metric"]," does not exist.")
                        else:
                            raise Exception("Date Column: ",dataHeaders["date"]," does not exist.")
                    else:
                        raise Exception("Id Column: ",dataHeaders["id"]," does not exist.")
            else:
                raise Exception("Data Dictionary does not have all required keys ['id', 'date', 'dateFormat', 'metric']")
        else:
            raise Exception("Data File: " + dataFile + " does not exist!")
        return

    def loadSql(self, dblist):
        for i,f in enumerate(dblist):
            if os.path.isfile(f):
                conn = self._openConnection(f)
                headers = self._getHeaders("images", conn)
                for cols in (headers[pos:pos + 500] for pos in xrange(0, len(headers), 500)):
                    for col in cols:
                        self._addColumn(col, "images")
                    result = conn.execute("select pegasusid," + ",".join(cols) + " from images")
                    query = "update images set " + ",".join([col + "=?" for col in cols]) + " where pegasusid=?"
                    values = [tuple([row[col] for col in cols] + [row["pegasusid"]]) for row in result]
                    self.conn.executemany(query, values)
                    self.conn.commit()
                self._closeConnection(conn)
            else:
                print "DB File: '%s' does not exist." % (f,)
        return

    def logErrors(self, logfile, table = "images"):
        """
        :param logfile: The logfile to write errors to
        :type logfile: str
        :param table: The table to load errors from
        :type table: str

        This function writes all errors from a given table to a log file,
        usually used at the end of image processing to write all images that
        did not process correctly.
        """
        with open(logfile, "w") as wh:
            wh.write("Image processing error log\n")
            wh.write("==========================\n")
            result = self.conn.execute("select pegasusid,path,error from '" + table + "' where error is not null")
            firstrow = result.fetchone()
            if firstrow:
                wh.write("Image with id '%s' loaded from input path '%s' was not processed successfully.\n" % (firstrow["pegasusid"], firstrow["path"]))
                for row in result:
                    wh.write("Image with id '%s' loaded from input path '%s' was not processed successfully.\n" % (row["pegasusid"], row["path"]))
            else:
                wh.write("All images processed successfully!  Nice job!\n")
        return

    def makePublic(self, targetFolder, process = False):
        imtypes = ["rgbsv", "rgbtv", "fluosv"]
        query = "select path from images where imtype in " + self._listToSql(imtypes)
        print query
        result = self.conn.execute(query)
        for row in result:
            target = "/iplant/home/shared/walia_rice_salt/" + targetFolder + "/" + "/".join(row["path"].split("/")[5:-1]) + "/0_0.png"
            print target
            if process:
                for utype in ["anonymous", "public"]:
                    subprocess.call(["ichmod","read", utype, target])
        return

    def dataToPlantcv(self, folder, ids = None, imtypes = None, dates = None):
        if not os.path.isdir(folder):
            ids = ids if ids else self._getIds("images")
            imtypes = imtypes if imtypes else self._getImageTypes("images")
            dates = dates if dates else self._getDates("images")
            query = "select id,date,imgname,imtype,path from images where id in " + self._listToSql(ids) + " and imtype in " + self._listToSql(imtypes) + " and date in " + self._listToSql(dates)
            print query
            result = self.conn.execute(query)
            os.makedirs(folder)
            for row in result:
                id = row["id"].split("-")[0] if "-" in row["id"] else row["id"]
                date_time = row["date"] + " 000"
                imtype = {
                    "rgbsv": "vis_sv_z700",
                    "rgbtv": "vis_tv_z300"
                }[row["imtype"]]
                fname = "%s-%s-%s-%s.png" % (id, date_time, row["imgname"], imtype)
                shutil.copyfile(row["path"], folder + "/" + fname)
        else:
            print "Folder already exists."
        return

    def dataToIAP(self, folder, ids = None, imtypes = None, dates = None):
        if not os.path.isdir(folder):
            ids = ids if ids else self._getIds("images")
            imtypes = imtypes if imtypes else self._getImageTypes("images")
            dates = dates if dates else self._getDates("images")
            query = "select id,date,imgname,imtype,path from images where id in " + self._listToSql(ids) + " and imtype in " + self._listToSql(imtypes) + " and date in " + self._listToSql(dates)
            print query
            result = self.conn.execute(query)
            os.makedirs(folder)
            for row in result:
                if not os.path.isdir(folder + "/" + row["imtype"][:-2]):
                    os.makedirs(folder + "/" + row["imtype"][:-2])
                writeim = "side" if "sv" in row["imtype"] else "top"
                dirname = folder + "/" + row["imtype"][:-2] + "/" + writeim
                if not os.path.isdir(dirname):
                    os.makedirs(dirname)
                fname = "%s_%s_%s_%s.png" % (row["imgname"], writeim, row["id"], row["date"])
                shutil.copyfile(row["path"], dirname + "/" + fname)
        else:
            print "Folder already exists."
        return

    def shootArea(self, intable, outtable, grouping, overwrite = False):
        """
        :param intable: The input table to load information from
        :type intable: str
        :param outtable: The output table to write information to.
        :type outtable: str
        :param grouping: Which imtypes to group
        :type grouping: list

        This function adds the numeric values of multiple image types together.
        In general, it is used to combine side view + top view images of the same spectrum.
        If you plan on correlating your data to lemnaTec's data, lemnaTec uses SV1 + SV2 + TV,
        so you should aggregate your data likewise.
        """
        self._validate("shootArea", intable, outtable, overwrite)
        self._createTable("shootArea", intable, outtable, overwrite)
        headers = self._getHeaders(outtable)
        dataHeaders = [header for header in headers if header not in conf.allHeaders and "ref" not in header]
        start = len(headers) - len(dataHeaders)
        """
        map = {
            "genotype": {
                "date": {
                    "treatment": {
                        "writeback": [],
                        "values": ()
                    }
                }
            }
        }
        """
        dataMap = {}
        result = self.conn.execute("select pegasusid," + ",".join(headers) + " from " + intable + " where " + " or ".join(["imtype=?" for x in grouping]), tuple([x for x in grouping]))
        for row in result:
            if row["genotype"] not in dataMap:
                dataMap[row["genotype"]] = {}
            if row["date"] not in dataMap[row["genotype"]]:
                dataMap[row["genotype"]][row["date"]] = {}
            if row["treatment"] not in dataMap[row["genotype"]][row["date"]]:
                dataMap[row["genotype"]][row["date"]][row["treatment"]] = {"writeback": [row["pegasusid"]], "values": tuple([row[x] for x in headers])}
            else:
                dataMap[row["genotype"]][row["date"]][row["treatment"]]["writeback"].append(row["pegasusid"])
                values = []
                for i,(x,y) in enumerate(zip(dataMap[row["genotype"]][row["date"]][row["treatment"]]["values"], tuple([row[x] for x in headers]))):
                    if i < start:
                        values.append(x)
                    else:
                        try:
                            values.append(x + y)
                        except:
                            values.append(None)
                dataMap[row["genotype"]][row["date"]][row["treatment"]]["values"] = tuple(values)

        #Loop through dataMap, insert values and writeback accordingly
        for genotype in dataMap:
            for date in dataMap[genotype]:
                for treatment in dataMap[genotype][date]:
                    lastid = self.conn.execute("insert into " + outtable + " (" + ",".join(headers) + ") values (" + ",".join(["?"] * len(headers)) + ")", dataMap[genotype][date][treatment]["values"]).lastrowid
                    self.conn.executemany("update " + intable + " set ref_" + outtable + "=? where pegasusid=?", tuple([(lastid, x) for x in dataMap[row["genotype"]][row["date"]][row["treatment"]]["writeback"]]))
        self.conn.commit()
        return

    def normalize(self, intable, outtable, column = "pixels", overwrite = False):
        """
        :param intable: The input table to load information from
        :type intable: str
        :param outtable: The output table to write information to.
        :type outtable: str
        :param column: The column to normalize information to
        :type column: str

        Normalizes all numerical information to the specific column.  This
        function is usually used with 'pixels' as the specified column, which
        expresses all numeric information as a percentage of the total pixels
        in the image.
        """
        self._validate("normalize", intable, outtable, overwrite)
        if self._columnExists(column, intable):
            conf.statsColumns["normalize"]["exclude"] += [column]
            self._createTable("normalize", intable, outtable, overwrite)
            headers = self._getHeaders(outtable)
            dataHeaders = [header for header in headers if header not in conf.allHeaders and "ref" not in header]
            result = self.conn.execute("select pegasusid," + column + "," + ",".join(headers) + " from " + intable)
            vals = ()
            for row in result:
                vals = []
                for x in headers:
                    if x in conf.allHeaders:
                        vals.append(row[x])
                    else:
                        if not self._checkNull(row[x]):
                            if not self._checkNull(row[column]) and row[column]:
                                vals.append(float(row[x]) / float(row[column]))
                            else:
                                vals.append(None)
                        else:
                            vals.append(None)
                lastid = self.conn.execute("insert into " + outtable + " (" + ",".join(headers) + ") values (" + ",".join(["?"] * len(headers)) + ")", tuple(vals)).lastrowid
                self.conn.execute("update " + intable + " set ref_" + outtable + "=? where pegasusid=?", (lastid, row["pegasusid"]))
            self.conn.commit()
        return

    def extractAll(self, options):
        basepath = os.path.dirname(os.path.dirname(os.path.abspath(self.db) + "/"))
        if "workflows" in options:
            for type in options["workflows"]:
                self._openConnection()
                tmp = self.conn.execute("select pegasusid,experiment,id,date,imtype,imgname from images where imtype=?", (type,))
                result = tmp.fetchall()
                for row in result:
                    finalpath = row["experiment"].replace(" ","") + "/" + row["id"].replace(" ","") + "/" + row["date"].replace(" ","") + "/" + row["imtype"].replace(" ","") + "/" + row["imgname"].replace(" ","") + "/" + row["pegasusid"] + "_" + options["workflows"][type]["inputs"][0] + ".png"
                    #finalpath = row["pegasusid"] + "_" + options["workflows"][type]["inputs"][0] + ".png"
                    self._closeConnection()
                    if os.path.isfile(finalpath):
                        try:
                            plant = ih.imgproc.Image(finalpath, db = self.db, dbid = row["pegasusid"])
                            plant.extractFinalPath()
                            if "--dimensions" in options["workflows"][type]["arguments"]:
                                plant.extractDimensions()
                            if "--pixels" in options["workflows"][type]["arguments"]:
                                plant.extractPixels()
                            if "--moments" in options["workflows"][type]["arguments"]:
                                plant.extractMoments()
                            if "--colors" in options["workflows"][type]["arguments"]:
                                plant.extractColorData()
                            if "--channels" in options["workflows"][type]["arguments"]:
                                plant.extractColorChannels()
                            if "--bins" in options["workflows"][type]["arguments"]:
                                plant.extractBins(options["workflows"][type]["arguments"]["--bins"])
                        except Exception as e:
                            print traceback.format_exc()
                    else:
                        print "PATH DOES NOT EXIST: %s." % (finalpath,)
        if "histogram-bin" in options:
            self._openConnection()
            self.histogramBinning("images", "histogramBins", dict((type,options["workflows"][type]["inputs"][0]) for type in options["workflows"]), options["histogram-bin"]["--group"], options["histogram-bin"]["--chunks"], options["histogram-bin"]["--channels"], True)
        return

    def histogramBinning(self, intable, outtable, grouping, chunks, channels, jsonwrite = False, overwrite = False):
        color_vector = {}
        for name in grouping:
            self._validate("histogramBins", intable, name + "_" + outtable, overwrite)
        for name in grouping:
            self._createTable("histogramBins", intable, name + "_" + outtable, overwrite)
            color_vector[name] = [0, 0, 0]
        map = dict((type, name) for name in grouping for type in grouping[name])
        basequery = "select "
        for x,c in enumerate(["bhist", "ghist", "rhist"]):
            for i in range(0, 256):
                if i == 0 and x == 0:
                    basequery += "SUM(" + c + str(i) + ")"
                else:
                    basequery += ",SUM(" + c + str(i) + ")"
        basequery += " from images where "
        for name in grouping:
            query = basequery + " or ".join(["imtype=?" for x in grouping[name]])
            result = self.conn.execute(query, tuple(grouping[name]))
            data = list(result.fetchone())
            for i in range(0, 3):
                color_vector[name][i] = data[i*256:(i + 1)*256]
        bins = {}
        for name in grouping:
            bins[name] = self._generateBins(self._splitHist(color_vector[name], chunks[name], channels[name]), name)
            self.conn.executemany("insert into " + name + "_" + outtable + " (name, minr, ming, minb, maxr, maxg, maxb) values (?, ?, ?, ?, ?, ?, ?)", [(bin["name"], int(bin["min"][2]), int(bin["min"][1]), int(bin["min"][0]), int(bin["max"][2]), int(bin["max"][1]), int(bin["max"][0])) for bin in bins[name]])
#             for bin in bins[name]:
#                 self.conn.execute("insert into " + name + "_" + outtable + " (name, minr, ming, minb, maxr, maxg, maxb) values (?, ?, ?, ?, ?, ?, ?)", (name + bin["name"], int(bin["min"][2]), int(bin["min"][1]), int(bin["min"][0]), int(bin["max"][2]), int(bin["max"][1]), int(bin["max"][0])))
#                 self.conn.commit()
            self.conn.commit()
        if jsonwrite:
            for name in grouping:
                with open(name + "_hist_bins.json", "w") as wh:
                    json.dump(bins[name], wh)
        return


    def _splitHist(self, hist, chunks, channels):
        returnlist = [ [1], [1], [1] ]
        s = [sum(x) for x in hist]
        #s = [int(x) for x in np.sum(hist, axis = 1)]
        for i in channels:
            tmp = 0
            integral = s[i] / chunks[i]
            for j,item in enumerate(hist[i]):
                tmp += item
                if (tmp > integral):
                    returnlist[i].append(j)
                    tmp = 0
        returnlist[0].append(255)
        returnlist[1].append(255)
        returnlist[2].append(255)
        return returnlist

    def _generateBins(self, vector, type):
        bins = []
        num = 1
        for i in range (0, len(vector[0]) - 1):
            for j in range(0, len(vector[1]) - 1):
                for k in range(0, len(vector[2]) - 1):
                    bins.append({
                        "name": type + "_bin" + str(num),
                        "min": np.array([vector[0][i],vector[1][j],vector[2][k]], dtype=np.uint8).tolist(),
                        "max": np.array([vector[0][i+1],vector[1][j+1],vector[2][k+1]], dtype=np.uint8).tolist()
                    })
                    num += 1
        return bins


    def correlation(self, intable, outtable, dataFile, dataHeaders, overwrite = False):
        """
        :param intable: The input table to load information from
        :type intable: str
        :param outtable: The output table to write information to.
        :type outtable: str
        :param dataFile: The csv data file to load
        :type dataFile: str
        :param dataHeaders: Column names for relevant table headers.
        :type dataHeaders: str

        This function correlates all numeric values with values in the given file.
        The input data file is assumed to be in csv format.  In dataHeaders, you must
        specify four keys, 'id', 'date', 'dateFormat', and 'metric'.  Each of these should
        be column names.  Id corresponds to the lemnaTec style identifier ex: '023535-S'.
        All dates are converted into Y-m-d form, you must provide a valid format in 'dateFormat',
        that way the dates can be converted correctly.  The 'metric' column is the actual value you
        want to correlate to.
        """
        self._validate("correlation", intable, outtable, overwrite)
        lemnaData = self._loadLemnaData(dataFile, dataHeaders)
        self._createTable("correlation", intable, outtable, overwrite)
        headers = self._getHeaders(outtable)
        numeric = [h for h in headers if h not in conf.allHeaders]
        for id in lemnaData:
            for imtype in self._getImageTypes(intable):
                x = {}
                y = []
                corr = {}
                result = self.conn.execute("select pegasusid," + ",".join(headers + ["date"]) + " from " + intable + " where id=? and imtype=? order by date", (id,imtype))
                if result.fetchone():
                    for row in result:
                        if row["date"] in lemnaData[id]:
                            y.append(lemnaData[id][row["date"]]["metric"])
                            for header in numeric:
                                if header not in x:
                                    x[header] = []
                                try:
                                    x[header].append(float(row[header]))
                                except:
                                    pass
                    if any([x[header] for header in numeric]):
                        for header in numeric:
                            if len(x[header]) == len(y):
                                corr[header] = np.corrcoef(x[header], y)[0][1]
                            else:
                                corr[header] = None
                        lastid = self.conn.execute("insert into " + outtable + " (" + ",".join(headers) + ") values (" + ",".join(["?"] * len(headers)) + ")", tuple([row[header] if header in conf.allHeaders else corr[header] for header in headers])).lastrowid
                        self.conn.execute("update " + intable + " set ref_" + outtable + "=? where id=? and imtype=?", (lastid, id, imtype))
        self.conn.commit()
        return

    def anova(self, intable, outtable, grouping, overwrite = False):
        """
        :param intable: The input table to load information from
        :type intable: str
        :param outtable: The output table to write information to.
        :type outtable: str
        :param grouping: The list of image types to group by.
        :type grouping: list

        Computes the analysis of variation of all numeric information based on 3 factors,
        treatment, date, and the interaction between the two.  Analysis of variation is
        different than the rest of the stats functions, in that a lot of information is
        lost after running it.  The results themselves correspond to columns (pixels, rmed, binx...)
        instead of actual images.
        """
        self._validate("anova", intable, outtable, overwrite)
        headers = self._getHeaders(intable)
        numeric = [h for h in headers if h not in conf.allHeaders]
        self._createTable("anova", intable, outtable, overwrite)
        outHeaders = self._getHeaders(outtable)
        result = self.conn.execute("select * from images")
        rowdata = []
        for row in result:
            rowdata.append(dict(row))
        data = pandas.DataFrame(rowdata).dropna()
        anova = {}
        for col in numeric:
            anova[col] = {}
            dateT = []
            treatmentT = []
            date_treatmentT = []
            for date in self._getDates(intable):
                dateT.append(data[data["date"] == date][col])
                for treatment in ["Control", "Stress"]:
                    treatmentT.append(data[data["treatment"] == treatment][col])
                    date_treatmentT.append(data[np.where(np.logical_and(data["treatment"] == treatment,data["date"] == date), True, False)][col])
            f_val, d_pval = stats.f_oneway(*dateT)
            f_val, t_pval = stats.f_oneway(*treatmentT)
            f_val, dt_pval = stats.f_oneway(*date_treatmentT)
            anova[col]["date"] = d_pval
            anova[col]["treatment"] = t_pval
            anova[col]["date_treatment"] = dt_pval
        for type in ["date", "treatment", "date_treatment"]:
            vals = [group] + [anova[x][type] for x in numeric] + [type]
            self.conn.execute("insert into " + outtable + " (" + ",".join(outHeaders) + ") values (" + ",".join(["?"] * len(outHeaders)) + ")", tuple(vals))
        self.conn.commit()
        return

    def tTest(self, intable, outtable, comp = "imtype", overwrite = False):
        """
        :param intable: The input table to perform the T test on.
        :type intable: str
        :param outtable: The output table to write the results to.
        :type outtable: str
        :param comp: Whether to compare image types or image names.
        :type comp: str
        :param overwrite: Whether or not to overwrite the output database
        :type overwrite: bool

        This function computes a ttest of the input table for all numeric headers.
        The comparison is either done based on image types or image names.  Default
        functionality is a comparison between image types, specify comp = 'imgname'
        to compare image names.
        """

        self._validate("ttest", intable, outtable, overwrite)
        self._createTable("ttest", intable, outtable, overwrite)
        comp = "imtype" if comp == "imtype" else "imgname"
        headers = self._getHeaders(outtable)
        numeric = [h for h in headers if h not in conf.allHeaders]
        meta = [h for h in headers if h not in numeric]
        data = {}
        result = self.conn.execute("select pegasusid,treatment," + ",".join(headers) + " from " + intable)
        for row in result:
            if row[comp] not in data:
                data[row[comp]] = {}
            if row["date"] not in data[row[comp]]:
                data[row[comp]][row["date"]] = {"meta": dict(row), "id": [], "values": {}}
            data[row[comp]][row["date"]]["id"].append(row["pegasusid"])
            if row["treatment"] not in data[row[comp]][row["date"]]["values"]:
                data[row[comp]][row["date"]]["values"][row["treatment"]] = [[row[h]] for h in numeric]
            else:
                for i,h in enumerate(numeric):
                    data[row[comp]][row["date"]]["values"][row["treatment"]][i].append(row[h])
        for comp in data:
            for date in data[comp]:
                vals = [data[comp][date]["meta"][x] for x in meta]
                for a,b in zip(data[comp][date]["values"]["Control"], data[comp][date]["values"]["Stress"]):
                    try:
                        res = stats.ttest_ind(a, b)[1]
                    except:
                        res = None
                    vals += [res]
                lastid = self.conn.execute("insert into " + outtable + " (" + ",".join(headers) + ") values (" + ",".join(["?"] * len(headers)) + ")", vals).lastrowid
                updateVals = (lastid,) + tuple(data[comp][date]["id"])
                self.conn.execute("update " + intable + " set ref_" + outtable + "=? where id in (" + ",".join(["?"] * len(data[comp][date]["id"])) + ")", updateVals)
        self.conn.commit()
        return

    def treatmentComp(self, intable, outtable, type = "ratio", direction = "Control", comp = "imtype", overwrite = False):
        """
        :param intable: The input table to load information from
        :type intable: str
        :param outtable: The output table to write information to.
        :type outtable: str
        :param type: The type of calculation to do between treatments.  Should be ratio or difference.
        :type type: str
        :param direction: Whether to compute C ~ S, or S ~ C, default is Control first.
        :type direction: str
        :param comp: Whether to compare by imtype or imgname
        :type comp: str

        This function compares information between treatments -- It finds plants that are identical
        except for treatment, and computes either a ratio or difference between them.  Direction
        is specified as the column you want first, so direction = "Control" will compute C ~ S, and
        direction = "Stress" will compute S ~ C.  If you have already normalized your table, difference
        will provide better information than ratio.
        """
        t1 = "Stress" if direction == "Stress" else "Control"
        t2 = "Stress" if direction == "Control" else "Control"
        if type == "ratio":
            op = lambda left, right: (left / right)
        else:
            op = lambda left, right: (left - right)
        comp = "imtype" if comp == "imtype" else "imgname"
        self._validate("treatmentComp", intable, outtable, overwrite)
        self._createTable("treatmentComp", intable, outtable, overwrite)
        headers = self._getHeaders(outtable)
        numeric = [h for h in headers if h not in conf.allHeaders]
        meta = [h for h in headers if h not in numeric]
        data = {}
        result = self.conn.execute("select pegasusid," + ",".join(headers) + " from " + intable)
        for row in result:
            if row["genotype"] not in data:
                data[row["genotype"]] = {"id": [], "values": {}, "meta": {}}
            data[row["genotype"]]["meta"][row[comp]] = dict(row)
            data[row["genotype"]]["id"].append(row["pegasusid"])
            if row[comp] not in data[row["genotype"]]["values"]:
                data[row["genotype"]]["values"][row[comp]] = {}
            if row["date"] not in data[row["genotype"]]["values"][row[comp]]:
                data[row["genotype"]]["values"][row[comp]][row["date"]] = {}
            if row["treatment"] not in data[row["genotype"]]["values"][row[comp]][row["date"]]:
                data[row["genotype"]]["values"][row[comp]][row["date"]][row["treatment"]] = [row[h] for h in numeric]
        for genotype in data:
            for comp in data[genotype]["values"]:
                for date in data[genotype]["values"][comp]:
                    vals = [data[genotype]["meta"][comp][x] for x in meta]
                    for a,b in zip(data[genotype]["values"][comp][date][t1], data[genotype]["values"][comp][date][t2]):
                        try:
                            res = op(float(a), float(b))
                        except:
                            res = None
                        vals.append(res)
                    lastid = self.conn.execute("insert into " + outtable + " (" + ",".join(headers) + ") values (" + ",".join(["?"] * len(headers)) + ")", vals).lastrowid
                    updateVals = (lastid,) + tuple(data[genotype]["id"])
                    self.conn.execute("update " + intable + " set ref_" + outtable + "=? where id in (" + ",".join(["?"] * len(data[genotype]["id"])) + ")", updateVals)
        self.conn.commit()
        return

    def threshold(self, intable, outtable, thresh = 0.01, overwrite = False):
        """
        :param intable: The input table to load information from
        :type intable: str
        :param outtable: The output table to write information to.
        :type outtable: str
        :param thresh: The threshold value.
        :type thresh: float

        This function thresholds the table based on the given value.  All values
        that fall below the threhsold are 'updated' in place with 'null'.  Normalize
        is often called before thresholding.
        """
        self._validate("threshold", intable, outtable, overwrite)
        self._createTable("threshold", intable, outtable, overwrite)
        headers = self._getHeaders(outtable)
        numeric = [h for h in headers if h not in conf.allHeaders]
        result = self.conn.execute("select pegasusid," + ",".join(headers) + " from " + intable)
        for row in result:
            vals = []
            for x in headers:
                if x in conf.allHeaders:
                    vals.append(row[x])
                else:
                    if not self._checkNull(row[x]):
                        if float(row[x]) > thresh:
                            vals.append(row[x])
                        else:
                            vals.append(None)
                    else:
                        vals.append(None)
            lastid = self.conn.execute("insert into " + outtable + " (" + ",".join(headers) + ") values (" + ",".join(["?"] * len(headers)) + ")", tuple(vals)).lastrowid
            self.conn.execute("update " + intable + " set ref_" + outtable + "=? where pegasusid=?", (lastid, row["pegasusid"]))
        self.conn.commit()
        return

    def export(self, table, processed = True, group = None, fname = None):
        """
        :param table: The table to write to csv
        :type table: str
        :param processed: Whether or not to extract processed data
        :type processed: bool
        :param group: Which image types to extract from the database.
        :type group: list
        :param fname: The file name to write to.
        :type fname: str

        This function simply extracts data from a database and writes it to csv format.
        Default functionality is to extract only data that has been processed.  This is
        checked by finding if an outputPath has been set.  Additionally,
        you can specify a list of image types to extract, if not, the default list contains
        all rgb and fluo images.  Finally, if no file name is specified, the name
        of the table is used as the filename.
        """
        group = group if isinstance(group, list) else self._getImageTypes(table)
        fname = fname if fname else table + ".csv"
        query = "select * from " + table
        values = tuple()
        if processed:
            query += " where outputPath is not null"
            if group:
                query += " and (" + " or ".join(["imtype=?" for x in group]) + ")"
                values = tuple([x for x in group])
        elif group:
            query += " where " + " or ".join(["imtype=?" for x in group])
            values = tuple([x for x in group])
        table = pandas.io.sql.read_sql(sql = query, params = values, con = self.conn)
        table.to_csv(fname)
        return
