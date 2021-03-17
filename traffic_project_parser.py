"""
Parser module for the main function and possibly other processes.

For the main function, parses the flags given by the user as command line arguments,
    and the flags given by the project's configuration file.

Gives priority to flags given by a configuration file.

Configuration file flags should be with the same names as command arguments,
    with delimited by an equal sign '=' from their values, and separated by
    new lines from other flags.
"""


import argparse
from os.path import exists
import utilities as utils


_paths = ["project.config_path", "sumo.config_path"]
_numbers = ["sumo.num_vehicles", "vehicle.speed", "vehicle.max_speed"]
_booleans = ["platoon.focal_direction"]
_strings = ["vehicle.type"]

_accepted_boolean_strings = {"true": True, "false": False}


class ParserError(Exception):
    """
    A dedicated exception for the parser module,
        meant for cataloging exceptions raised by the parser module. 
    """
    
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


def create_parser():
    """
    Initializes a simple argument parser object and returns it.
    """
    
    return argparse.ArgumentParser(argument_default=argparse.SUPPRESS)


def get_flags(parser, args=None):
    """
    Gets a parser object made by the create_parser method, and a list of arguments.
    Parses the arguments, and returns a dictionary such that the keys are the names of the arguments, and the values are the values
        given to the arguments.
    """
    
    parsed_args = parser.parse_args(args=args)
    return vars(parsed_args)


def create_main_parser():
    """
    Creates the parser object for the main module of the project
    Consists an internal function that adds '--' to the flag name
    """
    
    parser = create_parser()
    
    def add_argument(flag_name, nn=None, **kwargs):
        flag_name = ["--" + flag_name]
        if nn is not None:
            flag_name.insert(0, "-" + nn)
        parser.add_argument(*flag_name, **kwargs)
        
    add_argument("project.config_path", help="Allows to alter the path to the project's configuration file",
                default="project_conf.txt")
    add_argument("sumo.config_path", help="Allows to alter the path to SUMO's configuration file", 
                default="traffic2.sumocfg")
    add_argument("vehicle.speed", help="Allows to choose the default initial speed of a vehicle when entering the simulation", 
                default=1)
    add_argument("vehicle.max_speed", help="Allows to choose the default maximum speed of a vehicle in the simulation", 
                default=5)
    add_argument("vehicle.type", help="Configures the vehicle's type", 
                default="Car")
    add_argument("platoon.focal_direction", help="Decides if the direction of the platoon is set by the focal point or "\
                 "by the propagating vehicle", default=True)
    
    return parser


def parse_project_config(flags):
    """
    Gets the flags of the project.
    Parses the configuration file (if exists) and overwrites the flags' 
        corresponding values.
    
    NOTE: If a flag from the config does not exist in 'flags', that flag will
        be skipped
    """
    
    config_path = flags["project.config_path"]
    if not exists(config_path):
        print("WARNING! Could not load the configuration file: " + config_path)
        return
    
    with open(config_path, "r") as f:
        for line in f.readlines():
            line = utils.stripper(line)
            if line == "": # skipping empty lines
                continue
            
            flag = [utils.stripper(x) for x in line.split("=")]
            if len(flag) == 1:
                arg, val = flag[0], True
            else:
                arg, val = flag[0], flag[1]
                
            if arg not in flags:
                print("WARNING! Skipping unrecognized flag: " + arg)
                continue
            
            flags[arg] = val


def validate_flag_number(flag, value):
    """
    Gets a flag name and its value, raises exception if the value is not a number.
    """

    if type(value) not in (int, float):
        raise ParserError(f"{flag} must be a number! Got '{value}'")


def validate_flag_boolean(flag, value):
    """
    Gets a flag name and its value, raises exception if the value is not boolean.
    Accepts True / False, and the strings true, false (not case sensitive) 
    """

    if type(value) not in (bool, ) and value.lower() not in _accepted_boolean_strings:
        raise ParserError(f"{flag} must be either boolean value or one of the strings 'true' / 'false'! "\
                          f"Got '{value}'")


def validate_main_flags(flags):
    """
    Gets the flags given to the script, and validates that they all got valid values.
    NOTE: Path values are not checked in here.
    """

    for flag, value in flags.items():
        if flag in _paths:
            continue
        elif flag in _numbers:
            validate_flag_number(flag, value)
        elif flag in _booleans:
            validate_flag_boolean(flag, value)
        elif flag in _strings:
            pass
        else:
            raise ParserError(f"No validation set for flag: '{flag}'!")


def tend_booleans(flags):
    """
    Gets the flags given to the script AFTER validation.
    For every boolean value, makes sure there's a bool value in the flag.
    """

    for flag, value in flags.items():
        if flag in _booleans and type(value) is str and value.lower() in _accepted_boolean_strings:
            flags[flag] = _accepted_boolean_strings[value.lower()]


def get_main_flags():
    """
    Parses the arguments given to the script.
    Returns a dictionary such that the keys are the names of configurable attributes 
        of the script, and the values may be either default values for the attributes,
        or user defined values via flags to the script.
    """
    
    parser = create_main_parser()
    flags = get_flags(parser)
    parse_project_config(flags)
    validate_main_flags(flags)
    tend_booleans(flags)
    
    return flags