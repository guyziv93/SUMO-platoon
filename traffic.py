import traci
import system_globals as sg
import os
import traffic_project_parser as tpp
import simulation_lib as sl
import client
from threading import Thread, Event


log = sg.LOG


class MainError(Exception):
    """
    A dedicated exception for the main module,
        meant for cataloging exceptions raised by the main module. 
    """
    
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


def prepare_sumo_args(config_path):
    """
    Gets the config path for the sumo simulator.
    Prepares the shell command for activating the SUMO gui.
    Returns the command as a list while each element in the list represents
        shell format argument.
    Raises MainError exception in case preparing the command fails.
    """
    
    if "SUMO_HOME" not in os.environ:
        raise MainError("SUMO path could not be found in PYTHONPATH!")
    
    sumo_bin = os.path.join(os.environ["SUMO_HOME"], "bin", "sumo-gui")
    if os.name == "nt": # nt marks windows operating systems while posix is for linux
        sumo_bin += ".exe" # adding .exe for windows
        
    if not os.path.exists(sumo_bin):
        raise MainError("Could not find binary! " + sumo_bin)
    
    if not os.path.exists(config_path):
        raise MainError("Could not find sumocfg! " + config_path)
    
    return [sumo_bin, "-c", config_path]


def run_client(flags, action_event, step_event):
    """
    Gets the commands queue, from which the commands to the simulation are passed and an event.
    Starts the client that gets commands from the user via the given queue.
    """

    c = client.traffic_client(flags, action_event, step_event)
    
    while True:
        try:
            c.cmdloop()
        except client.ClientError: # indicates the client was ordered to stop
            sg.toggle_exit()
            break
        except KeyboardInterrupt:
            print("^C")
        except Exception as e:
            raise e


class post_step_actions(traci.StepListener):
    """
    Part of the traci interface, allows adding action post simulationStep.
    """

    def __init__(self):
        """
        """

        pass

    def step(self, _):
        """
        Ensures convoy vehicles and next step values
        """

        sl.remove_vehicles()

        for v in sg.VEHICLES:
            v.update_current_edge()
            if v.ensurance_active:
                sl.ensure_vehicle(v)

        if sg.PLATOON is not None:
            sg.LOG("---------------- Beginning propagation ----------------")
            sg.PLATOON.propagate()
            sg.LOG("------------------ Propagation ended ------------------")

        return not sg.EXIT


def run_simulation(sim_args, flags):
    """
    Execute an interactive simulation of a traffic_objects in the roads.
    """

    traci.start(sim_args, label="main")
    main_conn = traci.getConnection(label="main")
    traci.simulationStep() # first step, initializes simulation
    log("Made first simulation step")

    listener = post_step_actions()
    traci.addStepListener(listener)
    log("Assigned step listener")

    action_event = Event()
    step_event = Event()

    Thread(target=run_client, args=(flags, action_event, step_event)).start()

    step_event.set()

    while not sg.EXIT:
        action_event.wait()
        step_event.clear()
        traci.simulationStep()
        step_event.set()

    main_conn.close()
    traci.close()


def main():
    """
    Main method of the script.
    """

    flags = tpp.get_main_flags()
    sumo_args = prepare_sumo_args(flags["sumo.config_path"])
    run_simulation(sumo_args, flags)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        sg.EXCEPTION("Got unhandled exception in main!")
        raise e
