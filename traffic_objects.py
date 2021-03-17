import traci
import utilities
import system_globals as sg
import simulation_lib as sl


class TrafficObjectsError(Exception):
    """
    A dedicated exception for the traffic_objects module,
        meant for cataloging exceptions raised by the traffic_objects module. 
    """
    
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class platoon_member:
    """
    A class for handling a vehicle in a platoon.
    """

    search_vehicles = []


    def __init__(self, v):
        """
        Constructor for the platoon_member object.
        Gets a vehicle object.
        """

        self.v = v
        self.members_in_radius = []

        self.original_max_speed = v.get_max_speed()


    def get_propagation_members(self):
        """
        Returns a list of the members of the platoon resulted from this vehile's propagation
        """

        fellow_members = []

        for m in self.members_in_radius:
            fellow_members.append(m)
            fellow_members += m.get_propagation_members()

        return fellow_members


    def get_vehicles_in_radius(self, radius):
        """
        Returns the list of vehicles in the radius given of this member.
        """

        ids = []
        gathered_vehicles = []

        for i, v in enumerate(platoon_member.search_vehicles):
            if utilities.distance(self.v.get_coordinates(), v.get_coordinates()) <= radius:
                ids.append(i)
                gathered_vehicles.append(v)

        for i in reversed(ids):
            platoon_member.search_vehicles.pop(i)

        return gathered_vehicles


    def propagate(self, radius):
        """
        Goes over the vehicles in the smulation and checks if they are in the radius
            of the current platoon member, if so, adds them to its member's list.
        Removes any member that was already acquired by another member.
        """

        self.members_in_radius = []

        vir = self.get_vehicles_in_radius(radius)
        sg.LOG(f"Vehicles in radius of {self.v.id}: {[v.id for v in vir]}")

        for v in vir:
            if v.id == self.v.id:
                continue

            platoon.increment() # debug purpose
            platoon.add_vehicle(v) # debug purpose
            v.highlight(color=(0, 255, 0, 255))
            self.members_in_radius.append(platoon_member(v))

        for m in self.members_in_radius:
            m.propagate(radius)


    def __del__(self):
        """
        Actions to take when the platoon member is dropped from the platoon.
        """

        self.v.stop_highlight()
        self.v.set_max_speed(self.original_max_speed)

        if self.v.target_speed < 1:
            self.v.set_speed(1)


class platoon:
    """
    A class to serve the purpose of a platoon - a collection of vehicles
        moving in the same direction that.
    The platoon is initiated by choosing a vehicle to be its focal point, every
        vehicle in a dynamic range of any vehicle, starting from the focal point
        is part of the platoon.
    NOTE: Every vehicle can be found only once in a platoon member's members in radius.
    """

    members = []
    size = 0

    def __init__(self, fp_vehicle, focal_direction, radius=15):
        """
        Constructor method for the class.
        Gets a list of vehicles THAT MUST ALREADY BE IN THE SIMULATION,
            and possibly the initial speed for the convoy, defaults to 0.
        Sets the inital speed of the convoy to the speed given
        """

        self.focal_point = platoon_member(fp_vehicle)
        self.focal_direction = focal_direction
        self.radius = radius
        self.increment()

    @staticmethod
    def increment():
        """
        Increments the size of the platoon.
        """

        platoon.size += 1


    @staticmethod
    def add_vehicle(v):
        """
        Gets a vehicle object that is added to the platoon, and adds it to the
            platoon's list of vehicles.
        """

        platoon.members.append(v)


    def propagate(self):
        """
        Activates the propagation algorithm of the platoon.
        """

        platoon.size = 0
        platoon.members = [self.focal_point.v]

        direction = self.focal_point.v.get_remaining_edges()
        self.focal_point.v.highlight()
        platoon_member.search_vehicles = sl.get_vehicles_in_direction(direction, 
                                                                      exclude=[self.focal_point.v])

        sg.LOG(f"Members for propagation: {[v.id for v in platoon_member.search_vehicles]}")
        self.focal_point.propagate(self.radius)
        sg.LOG(f"Platoon size: {platoon.size}")


    def get_vehicle(self, v_id):
        """
        Gets a vehicle id and returns the vehicle's object.
        If the vehicle was not found returns None
        """
        
        for v in iter(self):
            if v.id == v_id:
                return v
        else:
            raise TrafficObjectsError(f"Could not find a vehicle with id '{v_id}' in the platoon")


    def set_speed(self, speed):
        """
        Gets an number representing the requested speed of the convoy.
        Sets the speed of the vehicles in the convoy to the given speed. 
        """
        
        for v in iter(self):
            v.set_speed(speed)


    def set_target(self, edge):
        """
        Gets the id of the target edge for the convoy.
        The object sets the course for the convoy.
        """

        for v in iter(self):
            v.set_target(edge)


    def get_members(self):
        """
        Returns a list of all of the members in the platoon.
        """

        return self.focal_point.get_propagation_members()


    def __iter__(self):
        """
        Returns the vehicles in the platoon.
        """
        
        for member in [self.focal_point] + self.get_members():
            yield member.v


class vehicle:
    """
    A class for managing a single vehicle in the simulation.
    """

    latest_id = 0

    def __init__(self, initial_route=None):
        """
        Constructor function for a vehicle object.
        Gets the vehicle id. 
        """

        self.id = f"v{vehicle.latest_id}"
        self.increment_id()

        self.init_route = self.get_initial_route(initial_route)
        self.curr_edge = self.init_route
        self.target_edge = traci.route.getEdges(self.init_route)[-1]
        self.target_speed = 1

        self.ensurance_active = True


    def get_initial_route(self, initial_route):
        """
        Sets the inital route of the vehicle.
        Can get an initial route, defaults to the first route in the simulation.
        """

        routes = traci.route.getIDList()

        if initial_route is None and len(routes) == 0:
            raise TrafficObjectsError("Failed to get default route, make sure there is at least one route in the sumocfg")

        initial_route = routes[0] if initial_route is None else initial_route

        if initial_route not in routes:
            raise TrafficObjectsError(f"Failed to find route: {initial_route}")

        return initial_route


    def increment_id(self):
        """
        Increments the static value 'latest_id' by 1
        """

        vehicle.latest_id += 1


    def update_current_edge(self):
        """
        Retrieves the value of the current edge of the vehicle and updates the
            self.curr_edge attribute
        """

        updated_curr_edge = traci.vehicle.getRoadID(self.id)

        if updated_curr_edge[0] != ":" and self.curr_edge != updated_curr_edge:
            sg.LOG(f"Updating {self.id} current edge from {self.curr_edge} to {updated_curr_edge}")
            self.curr_edge = updated_curr_edge


    def set_speed(self, speed):
        """
        Sets the speed of the vehicle to a given number
        """

        max_speed = self.get_max_speed()

        if max_speed < speed:
            raise TrafficObjectsError(f"Cannot change speed of {self.id} to {speed}, max speed is {max_speed}!")

        traci.vehicle.setSpeed(self.id, speed)
        self.target_speed = speed
        sg.LOG(f"Setting {self.id} speed to {speed}")


    def get_speed(self):
        """
        Returns the current speed of the vehicle
        """

        return traci.vehicle.getSpeed(self.id)


    def set_max_speed(self, max_speed):
        """
        Sets the maximum speed the vehicle can drive.
        """

        speed = self.get_speed()

        if max_speed < speed:
            raise TrafficObjectsError(f"Cannot change maximum speed of {self.id} to {max_speed}, speed is {speed}!")

        traci.vehicle.setMaxSpeed(self.id, max_speed)
        sg.LOG(f"Setting {self.id} maximum speed to {max_speed}")


    def get_max_speed(self):
        """
        Returns the maximum speed of the vehicle
        """

        return traci.vehicle.getMaxSpeed(self.id)


    def set_target(self, edge):
        """
        Gets the id of a target edge, assumes the edge is legal.
        Sets the course of the vehicle to target edge.
        """
        
        traci.vehicle.changeTarget(self.id, edge)
        self.target_edge = edge
        sg.LOG(f"Setting {self.id} target edge to {edge}")


    def check_reached_target(self):
        """
        Checks if the vehicle reached its target edge
        """
        
        return self.target_edge == self.curr_edge


    def get_coordinates(self):
        """
        Returns the vehicle's coordinates.
        """

        return traci.vehicle.getPosition(self.id)


    def get_route(self):
        """
        Returns the route the vehicle is currently following.
        """

        return traci.vehicle.getRoute(self.id)


    def get_remaining_edges(self):
        """
        Returns a list of the edges remaining in its current route.
        """

        route = self.get_route()

        return route[route.index(self.curr_edge):]


    def toggle_ensurance(self):
        """
        Toggles the ensurance mechanism indicator.
        """

        self.ensurance_active = not self.ensurance_active


    def highlight(self, **flags):
        """
        Highlights the vehicle with a red circle.
        Can be given flags to alter the state of the circle, according to traci api
        """

        traci.vehicle.highlight(self.id, **flags)


    def stop_highlight(self):
        """
        Stop the highlight of a vehicle.
        """

        self.highlight(duration=1, alphaMax=1)


    def __str__(self):
        """
        toString function for th vehicle object
        """
        
        v_str = f"Vehicle id: {self.id}\n"
        v_str += f"Current edge: {self.curr_edge}\n"
        v_str += f"Target edge: {self.target_edge}"
        if self.ensurance_active:
            v_str += f"\nRoute: {self.get_route()}"
        
        return v_str
        
        