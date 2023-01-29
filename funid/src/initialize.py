import os, sys, shutil
import json
import pandas as pd
from Bio import SeqIO
from funid.src.logics import isnan
import zipfile
import numpy as np
import re


from funid.src.tool import (
    initialize_path,
    get_genus_species,
    mkdir,
)
from funid.src.logger import Mes
from funid.src.validate_option import initialize_option

INF = 99999999

# Setup
# Make logics.py and move these unnecessary things to logics.py
# make directory if directory does not exists


"""
def gettype(string):
    if string == "str":
        return str
    elif string == "int":
        return int
    elif string == "float":
        return float
    elif string == "list":
        return list
    elif string == "bool":
        return bool
    else:
        print(string)
        raise TypeError
"""


# checking input option
# value should be list of small letter cases (for developmentors)
def check(
    obj,
    type_,
    criterion,
    value=np.NaN,
    min_=np.NaN,
    max_=np.NaN,
    default=np.NaN,
    solve=False,
):

    # obj : option things that should be checked
    # type_ : type of the object that should be
    # criterion : name of the option to be written on message
    # min_ : minimum value accepted (int, float)
    # max_ : maximum value accepted (int, float)
    # default : default value if the option is not available
    # solve : if True, if input is string, change to list form (list)

    # Error messages for each of the type
    # Change these things to logger if available
    def err_msg(type__):
        if type__ is bool:
            return "true or false, in small letters and without quotations"
        elif type__ is str:
            return "string with quotations"
        elif type__ is list:
            return "list with square brackets, and items with quotations"
        elif type__ is int:
            return "integer number"
        elif type__ is float:
            return "floating point number"
        else:
            print(
                "[ERROR] DEVELOPMENTAL ERROR. Please issue to wan101010@snu.ac.kr with logs and datasets"
            )
            raise ValueError

    # Flexible solve to int and float
    if (type(obj)) is int and type_ is float:
        obj = float(obj)
    elif (type(obj)) is float and type_ is int:
        obj = int(obj)

    # if type is right
    if (type(obj)) is type_:

        # if value is not in right range (for int and float)
        if not (isnan(min_)) and not (isnan(max_)):
            if type_ is int or type_ is float:
                if obj < min_ or obj > max_:
                    print(
                        f"[ERROR] {criterion} should be between {min_} and {max_}. Your input is {obj}"
                    )
                    raise ValueError

            else:
                print(type_)
                print(obj)
                print(
                    f"[ERROR] DEVELOPMENTAL ERROR on {criterion}. Please issue to wan101010@snu.ac.kr with logs and datasets"
                )
                raise Exception

        # if value is not in possible value (for str)
        if type(value) is list:
            if type_ is str:
                if not (obj.lower() in value):
                    print(
                        f"[ERROR] {criterion} should be one of {value}. Your input is {obj}"
                    )
                    raise ValueError
            else:
                print(
                    "[ERROR] DEVELOPMENTAL ERROR. Please issue to wan101010@snu.ac.kr with logs and datasets"
                )
                raise Exception

        return obj

    # if solving single string to list is available
    if solve is True:
        if type_ is list and type(obj) is str:
            obj = [obj]
        elif type(obj) is not (list):
            print(
                f"[ERROR] FAILED to solve {criterion} to list. It should be {err_msg(str)} or {err_msg(list)}. Your input is {obj}"
            )
            raise TypeError

    # if type is wrong
    else:
        # if default value exists
        if not (isnan(default)):
            print(
                f"[WARNING] {criterion} should be {err_msg(type_)}. Your input is {obj}. Setting to default value {default}"
            )
            return default

        # if default value does not exists and option.config should be corrected by user
        else:
            print(
                f"[ERROR] {criterion} is mandatory and should be {err_msg(type_)}. Your input is {obj}"
            )
            raise TypeError

    return obj


# Change it to FunIDPath
# Class with all path
class Path:
    def __init__(self, root):

        # For universal data used in every run
        self.sys_path = os.path.abspath(f"{os.path.dirname(__file__)}/../")

        # Option manager file location
        self.option_attributes = f"{self.sys_path}/data/Option_manager.xlsx"

        # initializing MAFFT for windows
        # MAFFT is occuring error when distributed in already used form
        # Therefore, distribute in zipped format
        if sys.platform == "win32":
            if not os.path.exists(f"{self.sys_path}/external/MAFFT_Windows"):
                with zipfile.ZipFile(
                    f"{self.sys_path}/external/MAFFT_Windows.zip",
                    "r",
                ) as zip_ref:
                    zip_ref.extractall(f"{self.sys_path}/external/MAFFT_Windows")

        # Location for list of genus file
        self.genusdb = f"{self.sys_path}/data/genus_line.txt"

        # Make blast / mmseqs db caching directory
        self.in_db = f"{self.sys_path}/db"
        mkdir(self.in_db)
        mkdir(f"{self.in_db}/mmseqs")
        mkdir(f"{self.in_db}/blast")

    def init_workspace(self, root, opt):

        # Workspace directory
        # root will be current run folder in "Result"
        if opt.outdir is None:
            self.root = root
        # if output directory designated, use it
        else:
            self.root = f"{opt.outdir}/{opt.runname}"
            mkdir(self.root)

        # Logging directory
        self.log = f"{self.root}/log.txt"
        self.extlog = f"{self.root}/log"  # for saving external program logs
        mkdir(self.extlog)

        # main workspace
        self.data = f"{self.root}"

        # saving directory
        self.save = f"{self.root}/save.shelve"

        # GenMine downloader points
        self.GenMine = f"{self.root}/GenMine"
        mkdir(self.GenMine)
        self.GenMine_tmp = f"{self.root}/GenMine/tmp"
        mkdir(self.GenMine_tmp)

        # DB input save point. Edited from io function
        self.out_db = f"{self.root}/DB"
        mkdir(self.out_db)

        # Query sequence save point
        self.out_query = f"{self.root}/Query"
        mkdir(self.out_query)

        # BLAST or mmseqss result saving point
        self.out_matrix = f"{self.root}/Search"
        mkdir(self.out_matrix)

        # Outgroup adjusted before aligned sequence file
        self.out_adjusted = f"{self.root}/Outgroup_Adjusted"
        mkdir(self.out_adjusted)

        # Alignment file directory (non-trimmed, trimmed and concatenated)
        self.out_alignment = f"{self.root}/Alignment"
        mkdir(self.out_alignment)

        # modeltest result directory
        self.out_modeltest = f"{self.root}/Modeltest"
        mkdir(self.out_modeltest)

        # Tree directory
        self.out_tree = f"{self.root}/Tree"
        mkdir(self.out_tree)

        # tmpfile directory
        self.tmp = f"{self.root}/tmp"
        mkdir(self.tmp)


## Main run in initialize.py ##
def initialize(path_run, parser):

    # Path expression for Linux system
    # Use pathlib for better expression
    if sys.platform != "win32":
        path_run = path_run.replace("\\", "/")

    # Move option loading as independent class or function
    # Generate path class
    print(f"Output location: {path_run}")
    path = Path(path_run)

    # Parsing options
    opt, list_info, list_warning, list_error = initialize_option(parser, path_run)

    # Make Run path
    path_root = f"{path_run}/{opt.runname}"

    # Setup path
    path.init_workspace(path_root, opt)

    # Clean up temporary files before start
    for file in os.listdir(path.root):
        if any(
            file.endswith(x) for x in [".fasta", ".png", ".nwk", "nhr", "nin", "nsq"]
        ):
            os.remove(f"{path.root}/{file}")

    # make log file
    log = open(path.log, "a")

    return opt, path, list_info, list_warning, list_error


# Initialize available genus list
def get_genus_list(V, opt, path):

    # put this to option in further development
    # if opt.use_default_genus_list is True:
    if 1:
        with open(path.genusdb, "r") as f:
            genus_set = set(f.read().splitlines())
    # else:
    #    genus_set = set()

    for FI in V.list_FI:
        if not (FI.genus == ""):
            genus_set.add(FI.genus)

    if len(genus_set) == 0:
        print("[Warning] No genus list found!")

    V.tup_genus = tuple(genus_set)
    return V
