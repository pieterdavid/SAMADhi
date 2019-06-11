from __future__ import unicode_literals
"""
Object representation of the SAMADhi database tables (based on peewee)

Example:
>>> from cp3_llbb.SAMADhi.SAMADhi import * ## import models and SAMADhiDB
>>> with SAMADhiDB():
>>>     mySamples = Sample.select().where(Sample.author == "MYUSERNAME")
"""

__all__ = ["loadCredentials", "SAMADhiDB"] ## models added below
_models = [] ## list for binding a database

import warnings
warnings.filterwarnings("ignore", module="peewee", category=UserWarning, message="Unable to determine MySQL version: .*")
import os
if os.getenv("CMSSW_VERSION") is not None:
    """ Silence some warnings if inside CMSSW """
    for warnMod in ("pysqlite2.dbapi2", "peewee"):
        warnings.filterwarnings("ignore", module=warnMod, category=DeprecationWarning, message="Converters and adapters are deprecated. Please use only supported SQLite types. Any type mapping should happen in layer above this module.")

from peewee import *
import datetime

def loadCredentials(path="~/.samadhi"):
    import json, os, stat
    credentials = os.path.expanduser(path)
    if not os.path.exists(credentials):
        raise IOError('Credentials file %r not found.' % credentials)
    # Check permission
    mode = stat.S_IMODE(os.stat(credentials).st_mode)
    if mode != stat.S_IRUSR:
        raise IOError('Credentials file has wrong permission. Please execute \'chmod 400 %s\'' % credentials)

    with open(credentials, "r") as f:
        data = json.load(f)
    if data.get("test", False):
        if "database" not in data:
            raise KeyError("Credentials json file at {0} does not contain 'database'".format(credentials))
    else:
        for ky in ("login", "password", "database"):
            if ky not in data:
                raise KeyError("Credentials json file at {0} does not contain '{1}'".format(credentials, ky))
        if "hostname" not in data:
            data["hostname"] = "localhost"

    return data

database = DatabaseProxy()

# Code generated by:
# python -m pwiz -e mysql --host=cp3.irmp.ucl.ac.be --user=llbb --password --info llbb
# Peewee version: 3.9.4
class BaseModel(Model):
    class Meta:
        database = database

class Analysis(BaseModel):
    id = AutoField(column_name="analysis_id")
    cadiline = TextField(null=True)
    contact = TextField(null=True)
    description = TextField(null=True)

    class Meta:
        table_name = 'analysis'

    def __str__(self):
        return ("{0.description}\n"
                "{cadi}"
                "{contact}"
                "  Number of associated results: {nresults:d}"
                ).format(self,
                    cadi=("  CADI line: {0.cadiline}\n".format(self) if self.cadiline else ""),
                    contact=("  Contact/Promotor: {0.contact}\n".format(self) if self.contact else ""),
                    nresults=self.results.count()
                    )

class Dataset(BaseModel):
    """ Table to represent one sample from DAS on which we run the analysis

    When creating a Dataset, at least the name and datatype (mc or data) attributes must be specified.
    """
    cmssw_release = CharField(null=True)
    creation_time = DateTimeField(null=True)
    id = AutoField(column_name="dataset_id")
    datatype = CharField()
    dsize = BigIntegerField(null=True)
    energy = FloatField(null=True)
    globaltag = CharField(null=True)
    name = CharField(index=True)
    nevents = IntegerField(null=True)
    process = CharField(null=True)
    user_comment = TextField(null=True)
    xsection = FloatField(null=True)

    class Meta:
        table_name = 'dataset'

    @classmethod
    def create(cls, **kwargs):
        """Initialize a dataset by name and datatype. Other attributes may be null and should be set separately"""
        for rK in ("name", "datatype"):
            if rK not in kwargs:
                raise RuntimeError("Argument '{0}' is required to construct {1}".format(rK, self.__class__.__name__))
        if kwargs["datatype"] not in ("mc", "data"):
            raise ValueError("dataset type must be mc or data, not {0!r}".format(kwargs["datatype"]))
        return super(Dataset, cls).create(**kwargs)

    def __str__(self):
        return ("Dataset #{0.id:d}:\n"
                "  name: {0.name}\n"
                "  process: {0.process}\n"
                "  cross-section: {xsection}\n"
                "  number of events: {nevents}\n"
                "  size on disk: {dsize}\n"
                "  CMSSW release: {0.cmssw_release}\n"
                "  global tag: {0.globaltag}\n"
                "  type (data or mc): {0.datatype}\n"
                "  center-of-mass energy: {energy} TeV\n"
                "  creation time (on DAS): {0.creation_time!s}\n"
                "  comment: {0.user_comment}"
                ).format(self,
                        nevents=("{0:d}".format(self.nevents) if self.nevents is not None else "None"),
                        dsize=("{0:d}".format(self.dsize) if self.dsize is not None else "None"),
                        xsection=("{0:f}".format(self.xsection) if self.xsection is not None else "None"),
                        energy=("{0:f}".format(self.energy) if self.energy is not None else "None"),
                        )

class Sample(BaseModel):
    """ Table to represent one processed sample, typically a PATtupe, skim, RDS, CP, etc.

    When creating a Sample, at least the name, path, sampletype (any of Sample.SampleTypes)
    and nevents_processed attributes must be specified.
    """
    author = TextField(null=True)
    code_version = CharField(null=True)
    creation_time = DateTimeField(constraints=[SQL("DEFAULT CURRENT_TIMESTAMP")], default=datetime.datetime.now)
    event_weight_sum = FloatField(null=True)
    extras_event_weight_sum = TextField(null=True)
    luminosity = FloatField(null=True)
    name = CharField(index=True)
    nevents = IntegerField(null=True)
    nevents_processed = IntegerField(null=True)
    normalization = FloatField(constraints=[SQL("DEFAULT 1")], default=1.)
    path = CharField()
    processed_lumi = TextField(null=True)
    id = AutoField(column_name="sample_id")
    sampletype = CharField()
    source_dataset = ForeignKeyField(Dataset, null=True, backref="samples")
    source_sample = ForeignKeyField("self", null=True, backref="derived_samples")
    user_comment = TextField(null=True)

    class Meta:
        table_name = 'sample'

    @property
    def results(self):
        return Result.select().join(SampleResult).join(Sample).where(Sample.id == self.id)

    SampleTypes = [ "PAT", "SKIM", "RDS", "LHCO", "NTUPLES", "HISTOS", "OTHER" ]

    @classmethod
    def create(cls, **kwargs):
        for rK in ("name", "path", "sampletype", "nevents_processed"):
            if rK not in kwargs:
                raise RuntimeError("Argument '{0}' is required to construct {1}".format(rK, self.__class__.__name__))
        if kwargs["sampletype"] not in Sample.SampleTypes:
            raise ValueError("sample type {0} is unknown (need one of {1})".format(kwargs["sampletype"], ", ".join(Sample.SampleTypes)))
        return super(Sample, cls).create(**kwargs)

    def removeFiles(self):
        File.delete().where(File.sample.id == self.id)
    def getLuminosity(self):
        """Computes the sample (effective) luminosity"""
        if self.luminosity is not None:
            return self.luminosity
        else:
            if self.source_dataset is not None:
                if self.source_dataset.datatype == "MC":
                    # for MC, it can be computed as Nevt/xsection
                    if self.nevents_processed is not None and self.source_dataset.xsection is not None:
                        return self.nevents_processed / self.source_dataset.xsection
                else:
                    # for DATA, it can only be obtained from the parent sample
                    if self.source_sample is not None:
                        return self.source_sample.luminosity
        ## in cases not treated above it is impossible to compute a number, so return None

    def __str__(self):
        return ("Sample #{0.id:d} (created on {0.creation_time!s} by {0.author})\n"
                "  name: {0.name}\n"
                "  path: {0.path}\n"
                "  type: {0.sampletype}\n"
                "  number of processed events: {0.nevents_processed:d}\n"
                "  number of events: {nevents}\n"
                "  normalization: {0.normalization}\n"
                "  sum of event weights: {0.event_weight_sum}\n"
                "{sumw_extras}"
                "  (effective) luminosity: : {0.luminosity}\n"
                "  {hasproclumi} processed luminosity sections information\n"
                "  code version: {0.code_version}\n"
                "  comment: {0.user_comment}\n"
                "{source_dataset}"
                "{source_sample}"
                "  {files}"
                ).format(self,
                    nevents=("{0:d}".format(self.nevents) if self.nevents is not None else "none"),
                    sumw_extras=("  has extras sum of event weight\n" if self.extras_event_weight_sum else ""),
                    hasproclumi=("has" if self.processed_lumi else "does not have"),
                    source_dataset=("  source dataset: {0.id:d}\n".format(self.source_dataset) if self.source_dataset is not None else ""),
                    source_sample=("  source sample: {0.id:d}\n".format(self.source_sample) if self.source_sample is not None else ""),
                    files=("{0:d} files: \n    - {1}".format(self.files.count(),
                            "\n    - ".join(
                                (("{0.lfn} ({nevents} entries)".format(fl, nevents="{0:d}".format(fl.nevents) if fl.nevents is not None else "no") for fl in self.files)
                                    if self.files.count() < 6 else
                                 (["{0.lfn} ({0.nevents:d} entries)".format(fl) for fl in self.files[:3]]
                                 +["...", "{0.lfn} ({0.nevents:d} entries)".format(self.files[-1])])
                                )
                            )) if self.id else "no files"
                           )
                    )

class File(BaseModel):
    """ Table to represent a file (in a sample)

    When creating a File, at least the lfn, pfn, event_weight_sum and nevents attributes must be specified.
    """
    event_weight_sum = FloatField(null=True)
    extras_event_weight_sum = TextField(null=True)
    id = BigAutoField()
    lfn = CharField() # Local file name: /store/
    nevents = BigIntegerField(null=True)
    pfn = CharField() # Physical file name: srm:// or root://
    sample = ForeignKeyField(Sample, backref="files")

    class Meta:
        table_name = 'file'

    @classmethod
    def create(cls, **kwargs):
        for rK in ("lfn", "pfn", "event_weight_sum", "nevents"):
            if rK not in kwargs:
                raise RuntimeError("Argument '{0}' is required to construct {1}".format(rK, self.__class__.__name__))
        return super(File, cls).create(**kwargs)

    def __str__(self):
        return self.lfn

class Result(BaseModel):
    """Table to represent one physics result, combining several samples.

    When creating a Result, at least the path attribute must be specified.
    """
    analysis = ForeignKeyField(Analysis, null=True, backref="results")
    author = TextField(null=True)
    creation_time = DateTimeField(constraints=[SQL("DEFAULT CURRENT_TIMESTAMP")], default=datetime.datetime.now)
    description = TextField(null=True)
    elog = CharField(null=True)
    path = CharField(index=True)
    id = AutoField(column_name="result_id")

    class Meta:
        table_name = 'result'

    @property
    def samples(self):
        return Sample.select().join(SampleResult).join(Result).where(Result.id == self.id)

    @classmethod
    def create(cls, **kwargs):
        for rK in ("path",):
            if rK not in kwargs:
                raise RuntimeError("Argument '{0}' is required to construct {1}".format(rK, self.__class__.__name__))
        return super(Result, cls).create(**kwargs)

    def __str__(self):
        return ("Result in {0.path}\n"
                "  created on {0.creation_time!s} by {0.author}"
                "{desc}"
                "{elog}"
                ).format(self,
                    desc=("\n  part of analysis {0.analysis.description}".format(self) if self.analysis else ""),
                    elog=("\n  more details in {0.elog}".format(self) if self.elog else "")
                    )

class SampleResult(BaseModel):
    result = ForeignKeyField(Result, column_name="result_id")
    sample = ForeignKeyField(Sample, column_name="sample_id")

    class Meta:
        table_name = 'sampleresult'
        indexes = (
            (('sample', 'result'), True),
        )
        primary_key = CompositeKey('result', 'sample')

# all models, for binding in SAMADhiDB and import
_models = [Analysis, Dataset, Sample, File, Result, SampleResult]
__all__ += _models

from contextlib import contextmanager
@contextmanager
def SAMADhiDB(credentials='~/.samadhi'):
    """create a database object and returns the db store from STORM"""
    cred = loadCredentials(path=credentials)
    if cred.get("test", False):
        import os.path
        dbPath = cred["database"]
        if not os.path.isabs(dbPath):
            dbPath = os.path.join(os.path.abspath(os.path.dirname(os.path.expanduser(credentials))), dbPath)
        db = SqliteDatabase(dbPath)
    else:
        db = MySQLDatabase(cred["database"], user=cred["login"], password=cred["password"], host=cred["hostname"])
    with db.bind_ctx(_models):
        yield db
