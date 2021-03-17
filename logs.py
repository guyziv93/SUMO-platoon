from os.path import join
import logging
import sys


DEBUG = logging.DEBUG
TERMINAL = 100
NTERMINAL = 99
logging.addLevelName(TERMINAL, "TERMINAL") # adds the TERMINAL log type
logging.addLevelName(NTERMINAL, "TERMINAL") # adds the NTERMINAL log type

_loggers = {}

_logfile_format= "{}_sumo_traffic.log"

def log(log_name, msg, level=DEBUG):
    """Logs the msg given to the log with the level given, defaults to DEBUG
    If no log has is set, does nothing"""
    
    if log_name is None:
        return
    
    logger = get_logger(log_name)
    logger.log(level, msg)


def add_log(logger, ignore_repeat=False):
    """Adds the logger given to the _loggers dictionary, when ignore_repeat is set on True it will allow duplicate log name
    should be used if we want a new log object under the same log name (queues_manager/executive/reconstructor etc)"""

    if logger.name in _loggers and not ignore_repeat:
            raise Exception("Cannot add logger! Logger '{}' already exists".format(logger.name))
    _loggers[logger.name] = logger


def get_logger(log_name):
    """Gets a log name and retrieves the logger object bound to that name.
    Raises exception if the logger does not exist"""

    logger = _loggers.get(log_name)

    if logger is None:
        raise Exception("Logger with the name {} does not exist!".format(log_name))

    return logger


def logger_exists(log_name):
    """Returns True if the logger exists, False if not"""

    return log_name in _loggers


class Logger(logging.Logger):
    """An alternative class for logging.Logger that initiates the logs with our specifications,
    and inherits the attributes of logging.Logger.

    Will be holding a dictionary of the handlers given to the logger for better assignments
    and removal of handlers.

    The interface will overwrite some of the native functions of logging.Logger but
    at the end will initiate them."""

    def __init__(self, logger_dir, ignore_repeat=False):
        super().__init__("sumo_log")
        self.inheritor_handlers = {} # self.handlers already exists in logging.Logger
        self.inheritor_formatter = None
        self.logger_dir = logger_dir
        add_log(self, ignore_repeat)


    def handler_exists(self, handler_name):
        """Checks if there's already a handler assigned to this logger associated with the name given"""

        return handler_name in self.inheritor_handlers


    def addHandler(self, handler_name, handler, formatter):
        """Gets a handler name and a handler object, and adds the handler to the logger
        Overwrites the native addHandler function.
        If a formatter is assigned to this logger, it will automatically assign it to the given handler"""

        if self.handler_exists(handler_name):
            raise Exception("Cannot add handler {}! A handler with that name already exists!".format(handler_name))

        if formatter is not None:
            handler.setFormatter(formatter)

        self.inheritor_handlers[handler_name] = handler
        super().addHandler(handler)


    def removeHandler(self, handler_name):
        """Gets a handler name and removes the handler given from the """

        if not self.handler_exists(handler_name):
            raise Exception("Cannot remove handler {}! No handler with that name found!".format(handler_name))

        super().removeHandler(self.handlers[handler_name])
        self.inheritor_handlers.pop(handler_name)


    def setFormatter(self, formatter, handler_name=None):
        """Gets a formatter object and assigns it to all of the handlers in the logger.
        Any future handler assigned to this logger will be configured with that formatter.
        Can be specified with a handler name in which it will configure only the specified handler with that formatter

        NOTE: Reusing this function without specifying a specific handler will result in replacing the formatters
        for all of the handlers currently assigned to this logger"""

        if handler_name is not None and not self.handler_exists(handler_name):
            raise Exception("Cannot set formatter! Handler {} does not exist in the logger!".format(handler_name))

        if handler_name is None:
            for handler in self.inheritor_handlers.values():
                handler.setFormatter(formatter)
        else:
            self.inheritor_handlers[handler_name].setFormatter(formatter)

        self.inheritor_formatter = formatter


    def _addFileHandler(self, log_name, logfile_mode, level):
        """Gets the name for a log file, the log file mode and a log level.
        Create a handler for the log and adds it to the logger"""

        handler = logging.FileHandler(join(self.logger_dir, log_name), mode=logfile_mode)
        handler.setLevel(level)

        formatter = None if self.inheritor_formatter is None else self.inheritor_formatter

        self._addHandler(log_name, handler, formatter)


    def add_debug_handler(self, log_name, logfile_mode="w"):
        """Adds a debug handler to the logger.
        Can be specified a file mode, defaults to 'w'
        Sets the log_name given to be the handler name of the handler in the logger"""

        self._addFileHandler(log_name, logfile_mode, DEBUG)


    def terminal(self, msg, skip_stdout=False, *args, **kwargs):
        """An additional logging function to the interface, should be used when logging to the stdout
        If skip_stdout is set to 'True' skips writing to stdout and only writing to the logs (TERMINAL level writes to all levels),
        this feature is meant for logging terminal prints that have a seperator that is not a newline"""

        if skip_stdout:
            self.log(NTERMINAL, msg, *args, **kwargs)
        else:
            self.log(TERMINAL, msg, *args, **kwargs)


    def add_terminal_handler(self):
        """Adds a stream hanlder to the logger that writes to the stdout (e.g. terminal)"""

        self._addStreamHandler(TERMINAL, sys.stdout)


    def _addStreamHandler(self, level, stream):
        """Creates a stream handler for the given stream, defaults to stdout, binds it to the level given"""

        terminal = logging.StreamHandler(stream=stream)
        terminal.setLevel(level)

        self._addHandler("{}_stdout_log".format(level), terminal, None)


    def _addHandler(self, log_name, handler, formatter):
        """Adds a handler to the logger"""

        try:
            self.addHandler(log_name, handler, formatter)
        except Exception as e: # Always close the handler created in case it failed adding it to the logger
            handler.close()
            raise e


    def __str__(self):

        print_string = ""

        print_string += "Number of handlers: {}\n".format(len(self.inheritor_handlers))
        print_string += "Handlers: {}".format(list(self.inheritor_handlers.keys()))

        return print_string


def prepare_logger(ignore_repeat=False):
    """Returns a logger object and sets its formatter"""

    logs_root_dir = ""

    logger = Logger(logs_root_dir, ignore_repeat)
    formatter = logging.Formatter("%(asctime)s | %(levelname)s\t | %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    logger.setFormatter(formatter)
    
    return logger


def create_logger(ignore_repeat=False, logfile_format=None):
    """Returns a logger object that can be used for logging information during runtime
    Gets the log's name and the log's root directory"""
    
    logger = prepare_logger(ignore_repeat)
    
    logger.add_debug_handler(_logfile_format.format("debug_log") if not logfile_format else logfile_format.format("debug_log"))
    logger.add_terminal_handler()

    return lambda x: logger.log(DEBUG, x)

