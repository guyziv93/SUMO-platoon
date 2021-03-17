import traci
import cmd
import sys
import traceback
import colors
import traffic_objects as to
import system_globals as sg
import simulation_lib as sl


class ClientError(Exception):
    """
    A dedicated exception for the client module,
        meant for cataloging exceptions raised by the client module. 
    """
    
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class traffic_client(cmd.Cmd):
    """
    Interactive client for giving commands to the traffic_objects,
    also might affect the simulation in additional ways.
    """
    
    def __init__(self, flags, action_event, step_event):
        """
        Constructor method for the class.
        Gets the commands queue from which it will transfer the commands to the simulation.
        """
        super().__init__()
        
        self.prompt = "traffic_client> "
        self.prints = {"notification": True, "error": True, "warning": True}
        self.block = action_event
        self.blocker = step_event
        self.pause = False
        
        self.edges = sl.get_edges()
        self.block.set() # unblocking simulation steps

        self.vehicle_type = flags["vehicle.type"]
        self.last_line = None
        self.default_max_speed = flags["vehicle.max_speed"]
        self.default_speed = flags["vehicle.speed"]
        self.focal_direction = flags["platoon.focal_direction"]

    
    def precmd(self, line):
        """
        Overrides the original function.
        Gets the line of arguments from the user and returns the list of arguments
        """
        
        return " ".join(filter(lambda x: x is not "", line.split(" ")))
    
    
    def onecmd(self, line):
        """
        Overwrites ancestor oncecmd 
        """
        
        self.last_line = line
        
        try:
            if not self.pause:
                self.block.clear()
            self.blocker.wait()
                
            super().onecmd(line) # this is in order to keep the original behavior.
            
            if not self.pause:
                self.block.set()
        except ClientError as e:
            if sys.exc_info()[1] == "0": # indicates to close the client
                raise e
            return self.print_exception()
        except:
            return self.print_exception(unmapped=True)
    
    
    def print_notification(self, msg):
        """
        Prints a notification to the user from the system
        """
        
        if self.prints["notification"]:
            sg.TERMINAL(colors.wrap_message_in_bold_blue(msg))
    
    
    def print_error(self, msg):
        """
        Prints the error message given colored in red
        """
        
        if self.prints["error"]:
            msg = "ERROR: " + msg
            sg.TERMINAL(colors.wrap_message_in_red(msg))
    
    
    def print_warning(self, msg):
        """
        Prints the message given in bold
        """
        if self.prints["warning"]:
            msg = "WARNING: " + msg
            sg.TERMINAL(colors.wrap_message_in_bold(msg))
            

    def print_exception(self, unmapped=False):
        """
        Prints the error given by the exception colored in red
        """
        
        preprint = "GOT EXCEPTION" if not unmapped else "GOT AN UNMAPPED EXCEPTION"
        preprint = colors.wrap_message_in_bold_red(preprint)
        sg.EXCEPTION(preprint)
        print(preprint)

        err = str(sys.exc_info()[1]).strip("' ")
        save_status = self.prints["error"]
        self.prints["error"] = True

        print("######   TRACEBACK   ######\n")
        traceback.print_tb(sys.exc_info()[2])
        self.print_error(err)
        print("\n######   TRACEBACK   ######")

        self.prints["error"] = save_status


    def get_args(self, mandatory=0):
        """
        Returns the arguments given to the command, according the the number of args
            expected.
        Can be given the the number of mandatory arguments expected.
        If mandatory is 0, assumes all arguments are optional.
        """

        args = self.last_line.split(" ")
        sg.LOG(f"Got command: {args}")

        if mandatory > 0 and len(args) - 1 < mandatory:
            raise ClientError(f"Not enough arguments provided! Expected at least {mandatory}, got {len(args) - 1}")

        if len(args) == 1:
            return []
        else:
            return args[1:]


    def get_vehicles(self, vehicle_ids):
        """
        Gets a list of vehicle ids, returns a list of their respective vehicle objects, if
            existent.
        """

        vehicles = []

        for v_id in vehicle_ids:
            try:
                vehicles.append(sl.get_vehicle(v_id))
            except sl.SimulationLibError as e:
                sg.EXCEPTION(f"Failed to get vehicle {v_id}")
                raise e

        return vehicles


    def do_speed(self, _):
        """
        Gets 2 arguments:
        1. A number
        *. Vehicle ids
        Sets the speed given to the vehicle ids given.
        If none were given, sets the speed given to all vehicles in
            the simulation.
        """

        mandatory = 1
        args = self.get_args(mandatory=mandatory)
        try:
            speed = float(args[0])
        except ValueError:
            raise ClientError(f"Cannot change speed to '{args[0]}', it's not a number!")

        vehicles = sg.VEHICLES if len(args) == mandatory else self.get_vehicles(args[mandatory:])

        for v in vehicles:
            v.set_speed(speed)
        sg.LOG(f"Updated speed to {speed} to {[v.id for v in vehicles]}")


    def do_max_speed(self, _):
        """
        Gets 2 arguments:
        1. A number
        *. Vehicle ids
        Sets the maximum speed given to the vehicle ids given.
        If none were given, sets the maximum speed given to all vehicles in
            the simulation.
        """

        mandatory = 1
        args = self.get_args(mandatory=mandatory)
        try:
            speed = float(args[0])
        except ValueError:
            raise ClientError(f"Cannot change maximum speed to '{args[0]}', it's not a number!")

        vehicles = sg.VEHICLES if len(args) == mandatory else self.get_vehicles(args[mandatory:])

        for v in vehicles:
            v.set_max_speed(speed)
        sg.LOG(f"Updated maximum speed to {speed} to {[v.id for v in vehicles]}")


    def do_pe(self, _):
        """
        Prints the edges of the simulation.
        Can be given a prefix of an edge id, and only the edges with that prefix will
            be printed.
        """
        
        args = self.get_args()
        
        if len(args) == 0:
            for e in self.edges:
                sg.TERMINAL(e)
        else:
            prefix_len = len(args[0])
            for e in self.edges:
                if e[:prefix_len] == args[0]:
                    sg.TERMINAL(e)
        
        
    def do_pv(self, _):
        """
        Prints the vehicles in the convoy by order.
        Can be given a vehicle id as an argument, which prints only that vehicles data.
        """
        
        args = self.get_args()
        
        if len(args) == 0:
            for v in sg.VEHICLES:
                sg.TERMINAL(v)
                sg.TERMINAL("--------------------------")
        else:
            v_id = args[0]
            v = sl.get_vehicle(v_id)
            sg.TERMINAL(v)


    def do_pp(self, _):
        """
        Prints the members of the platoon.
        """

        for v in iter(sg.PLATOON):
            sg.TERMINAL(v)


    def do_target(self, _):
        """
        Gets 2 arguments:
        1. Vehicle id
        2. Target edge
        Sets the target of the vehicle to the given edge id
        """
        
        args = self.get_args(2)
        vehicle_id = args[0]
        target_edge = args[1]

        if not sl.is_vehicle(vehicle_id):
            raise ClientError(f"Vehicle {vehicle_id} is not in the simulation!")

        if target_edge not in self.edges:
            raise ClientError(f"Edge {target_edge} is not in the simulation!")
        
        v = sl.get_vehicle(vehicle_id)
        v.set_target(target_edge)


    def do_pause(self, _):
        """
        Stops the simulation until the user allows to continue
        """
        
        self.block.clear()
        self.pause = True
        sg.LOG("Paused")
    
    
    def do_resume(self, _):
        """
        Resumes the simulation if it was paused
        """
        
        self.block.set()
        self.pause = False
        sg.LOG("Resumed")


    def do_step(self, _):
        """
        Makes a simulation step.
        Can be used only if the simulation is paused.
        Can be given an positive integer as the number of steps to make.
        """

        args = self.get_args()
        num_steps = 1

        if len(args) > 0:
            try:
                num_steps = int(args[0])
                if num_steps <= 0:
                    raise ClientError(f"Number of steps must be a positive integer!")
            except ValueError:
                raise ClientError(f"Cannot make '{args[0]}' steps! Must be a positive integer")

        if not self.pause:
            raise ClientError("Simulation steps are possible on when simulation is paused!")

        for _ in range(num_steps):
            traci.simulationStep()


    def do_addv(self, _):
        """
        Adds a vehicle to the simulation.
        Can get a integer argument for the number of vehicles to add.
        """

        if self.pause:
            raise ClientError("Cannot add vehicle while simulation is paused!")

        args = self.get_args()
        num_vehicles = 1

        if len(args) > 0:
            try:
                num_vehicles = int(args[0])
            except:
                raise ClientError(f"Number of vehicles must be an integer! Got '{args[0]}'")

        for _ in range(num_vehicles):
            v = to.vehicle()
            sl.add_vehicle(v.id, v.init_route)
            sl.wait_for_vehicle(v.id)
    
            v.set_max_speed(self.default_max_speed)
            v.set_speed(self.default_speed)
            sg.VEHICLES.append(v)
            sg.ID_TO_VEHICLE[v.id] = v


    def do_rmv(self, _):
        """
        Removes all vehicles from the simulation by shutting down their ensuranse mechanism.
        Can get infinite arguments of vehicle ids, in that case will remove only the given vehicle ids.
        """

        args = self.get_args()
        vehicles = sg.VEHICLES if len(args) == 0 else self.get_vehicles(args)

        for v in vehicles:
            v.toggle_ensurance()


    def do_setp(self, _):
        """
        Gets a single argument to be the a vehicle id.
        Creates a platoon object and sets the vehicle id given as the focal point.
        """

        args = self.get_args(mandatory=1)
        vehicle_id = args[0]

        v = sl.get_vehicle(vehicle_id)
        sg.set_platoon(to.platoon(v, self.focal_direction))
        sg.LOG(f"Set platoon on vehicle {v.id}")


    def do_rmp(self, _):
        """
        Removes the platoon from th simulation.
        """

        sg.set_platoon(None)
        sg.LOG("Platoon removed")


    def do_radius(self, _):
        """
        Let's the user change the radius of the platoon, must be a number.
        """

        args = self.get_args(mandatory=1)
        try:
            radius = float(args[0])
        except ValueError:
            raise ClientError(f"Radius must be a number! Got {args[0]}")

        if sg.PLATOON is None:
            raise ClientError("Cannot set radius before setting a platoon!")

        sg.PLATOON.radius = radius


    def do_hl(self, _):
        """
        Highlights a vehicle with a blue circle, if none were given, highlights all
            vehicles except for the platoon vehicles.
        NOTE: Pointless to use on vehicles that are part of the platoon.
        """

        args = self.get_args()
        vehicles = sg.VEHICLES if len(args) == 0 else self.get_vehicles(args)

        for v in vehicles:
            v.highlight(color=(0, 0, 255, 255))


    def do_shl(self, _):
        """
        Stops the highlight of a vehicle, if none were given, stops the highlights
            of all vehicles.
        NOTE: Pointless to use on vehicles that are part of the platoon.
        """

        args = self.get_args()
        vehicles = sg.VEHICLES if len(args) == 0 else self.get_vehicles(args)

        for v in vehicles:
            v.stop_highlight()


    def do_vr(self, _):
        """
        Gets a vehicle id as an argument, prints the current route of that vehicle.
        """

        mandatory = 1
        args = self.get_args(mandatory=mandatory)

        v = self.get_vehicles([args[0]])[0]

        sg.TERMINAL(f"Route of vehicle {v.id}: {v.get_route()}")


    def do_speedp(self, _):
        """
        Gets a number, sets the speed of the platoon to that number.
        """

        args = self.get_args(mandatory=1)
        try:
            speed = float(args[0])
        except ValueError:
            raise ClientError(f"Cannot change platoon speed to '{args[0]}', it's not a number!")

        sg.PLATOON.set_speed(speed)


    def do_targetp(self, _):
        """
        Gets an edge id, sets the target edge of the vehicles in the platoon to be the edge given.
        """

        args = self.get_args(mandatory=1)
        target_edge = args[0]

        if target_edge not in self.edges:
            raise ClientError(f"Edge {target_edge} is not in the simulation!")

        sg.PLATOON.set_target(target_edge)


    def do_exit(self, _):
        """
        Enbales the user to exit the simulation.
        """
        
        self.do_EOF(_)
    
    
    def do_EOF(self, _):
        """
        Builtin function to treat EOF.
        """
        
        raise ClientError("0")
    
    
    def do_debug(self, _):
        """
        For experiments. 
        """
        
        args = self.get_args(mandatory=1)
        cmd = args[0]
        print(eval(cmd))