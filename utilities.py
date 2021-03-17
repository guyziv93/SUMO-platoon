"""
A utilities module for the project.

Consists miscellaneous function for the project 
"""


from math import sqrt, pow


class UtilitiesError(Exception):
    """
    A dedicated exception for the utilities module,
        meant for cataloging exceptions raised by the utilities module. 
    """

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


def stripper(string):
    """
    Gets a string and returns it stripped from whitespaces, newlines and tabs
    """

    return string.strip(" \n\r\t")


def distance(c1, c2):
    """
    Gets 2 coordinates tuples, each holds a left value for the x-axis and
        a right value for the y-axis.
    Returns the distance between these 2 coordinates.
    """

    x_dist = pow(c1[0] - c2[0], 2)
    y_dist = pow(c1[1] - c2[1], 2)

    return sqrt(x_dist + y_dist)

