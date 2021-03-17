"""
Dedicated module for global parameters of the project
"""


import logs


LOG = logs.create_logger()
TERMINAL = logs.get_logger("sumo_log").terminal
EXCEPTION = logs.get_logger("sumo_log").exception
EXIT = False

VEHICLES = []
ID_TO_VEHICLE = {}
PLATOON = None
DEFAULT_MAX_SPEED = None
DEFAULT_SPEED = None


def toggle_exit():
    """
    Negates the current value of the EXIT global
    """
    
    global EXIT
    
    EXIT = not EXIT


def set_platoon(platoon):
    """
    Gets a platoon object and a sets the global platoon variable to it.
    NOTE: Can be given None to remove the platoon.
    """

    global PLATOON

    PLATOON = platoon

