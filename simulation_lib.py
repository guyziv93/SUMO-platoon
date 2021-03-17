"""
General library for simulation actions
"""


import traci
import system_globals as sg
from random import choice


class SimulationLibError(Exception):
    """
    A dedicated exception for the parser module,
        meant for cataloging exceptions raised by the parser module. 
    """
    
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


def get_edges():
    """
    Returns the list of edges in the simulation, removing
        unexplainable ids that start with ':'
    """

    edges = traci.edge.getIDList()
    return list(filter(lambda x: x[0] != ":", edges))


def get_random_edge(exclude=[]):
    """
    Returns the id of random edge in the simulation.
    Can be given a list of edge ids to exclude.
    """
    
    edges = list(filter(lambda x: x not in exclude, get_edges()))
    return choice(edges)


def ensure_vehicle(vehicle, target_edge=None):
    """
    Gets a vehicle object and checks if it reached its target edge.
    If it did, reroutes it to a random edge, unless given a target.
    """

    if sg.EXIT or not vehicle.check_reached_target():
        return

    target = get_random_edge(exclude=[vehicle.curr_edge]) \
            if target_edge is None else target_edge

    vehicle.set_target(target)


def has_past_subroute(direction, v):
    """
    Gets a direction and a vehicle object.
    Checks if that vehicle is following a route that begins with the direction given,
        and at some point 
    """

    v_route = v.get_route()
    start_e = direction[0]

    if start_e not in v_route:
        return False

    for e in v_route[v_route.index(start_e):]:
        if e == v.curr_edge:
            return True

    return False


def get_vehicles_in_direction(direction, exclude=[]):
    """
    Gets a list of edges that form a valid route in the simulation.
    Returns a list of vehicles that have the first edge in the list as one of their
        remaining edges, or having a subroute in the current route, that begines with the firsr
        edge in the direction and ends in the current edge of the vehicle.
    Can get a list of vehicles to exclude from the returned list.
    """

    return_vehicles = []

    for v in sg.VEHICLES:
        if v.id in exclude:
            continue

        if direction[0] in v.get_remaining_edges() or has_past_subroute(direction, v):
            return_vehicles.append(v)
            
    return return_vehicles


def add_vehicle(vehicle_id, init_route_id):
    """
    Gets a vehicle id and a route id.
    Enters a new vehicle to the simulation in the route given.
    """

    traci.vehicle.add(vehicle_id, init_route_id)


def is_vehicle(vehicle_id):
    """
    Gets a vehicle id and checks if the vehicle is in the simulation.
    """

    return vehicle_id in traci.vehicle.getIDList()


def get_vehicle(vehicle_id):
    """
    Gets a vehicle id and returns its vehicle object.
    """

    if vehicle_id not in sg.ID_TO_VEHICLE:
        raise SimulationLibError(f"Could not find a vehicle with id: {vehicle_id}")

    return sg.ID_TO_VEHICLE[vehicle_id]


class freeze_vehicles:
    """
    A decorator class for freezing all of the vehicles in the simulation.
    """

    def __init__(self, vehicles=None):
        """
        Can get a list of vehicle objects, if sets a list of all the vehicles in
            the simulation.
        """

        self.vehicles = sg.VEHICLES.copy() if vehicles is None else vehicles
        self.vehicle_to_speed = {}

    def __enter__(self):
        """
        Sets the speed of all vehicles in the simulation to 0 and keeps the
            original speed.
        """

        for v in self.vehicles:
            self.vehicle_to_speed[v.id] = v.target_speed
            v.set_speed(1)

    def __exit__(self, *_):
        """
        Sets the speed of all of the vehicles in the object back to the original speed.
        """

        for v in self.vehicles:
            original_speed = self.vehicle_to_speed[v.id]
            v.set_speed(original_speed)


def wait_for_vehicle(vehicle_id):
    """
    Gets a vehicle id.
    Freezes all of the vehicles in the simulation and advances step after
        step until the given vehicle has entered the simulation.
    """

    with freeze_vehicles():
        while not is_vehicle(vehicle_id):
            traci.simulationStep()


def remove_vehicles():
    """
    Goes over every registered vehicle, removes vehicles that left the simulation
    """

    left_vehicle_ids = []

    for i, v in enumerate(sg.VEHICLES):
        if not is_vehicle(v.id):
            left_vehicle_ids.append(i)

    for i in reversed(left_vehicle_ids):
        sg.LOG(f"Removing vehicle: {sg.VEHICLES[i]}")
        sg.ID_TO_VEHICLE.pop(sg.VEHICLES[i].id)
        sg.VEHICLES.pop(i)


def highlight_vehicle(vehicle_id, color=None):
    """
    Gets a vehicle id and highlights the vehicle with a red circle.
    Can be given the color of the circle as a tuple of RGBA.
    """

    flags = {}

    if color is not None:
        flags["color"] = color

    traci.vehicle.highlight(vehicle_id, **flags)


def stop_highlights():
    """
    Cancels the highlights of all vehicles.
    """

    for v in sg.VEHICLES:
        v.stop_highlight()

