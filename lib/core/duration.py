import atexit  # Provides functionality to register functions that run automatically when the program exits.
import enum  # Used for creating enumerations, which are a set of symbolic names bound to unique, constant values.
import os  # Allows interaction with the operating system, such as executing other programs or terminating processes.
import sys  # Provides access to system-specific parameters and functions, such as command-line arguments and the Python executable.
import logging  # A built-in module for creating logs to track application behavior and debug issues.
from typing import Optional  # Importing Optional to use for type annotations

# Set up a logger for recording lifecycle-related actions
logger = logging.getLogger("logger")

# Define the public API of this module, explicitly stating what should be accessible when imported
__all__ = ["duration"]

# Define an enumeration class to represent different behaviors of the program lifecycle
Behavior = enum.Enum("Behavior", "NONE TERMINATE RESTART")


class Duration:
    """
    This class manages the program's lifecycle, determining how it behaves when the program exits.

    Key Responsibilities:
    - Define actions on program exit, such as restarting or terminating the program.
    - Allow configuration of exit behavior via attributes.
    - Register an `onExit` function to execute lifecycle actions at exit.
    """

    def __init__(self) -> None:
        # Default behavior is to do nothing on exit
        self.behavior = Behavior.NONE

        # Exit code for the program; used only if Behavior.TERMINATE is set
        self.exitcode: int = 0

        # Optional file path for storing the program's state during a restart
        self.state_file: Optional[str] = None

        # Register the `onExit` method to be called automatically when the program exits
        # This ensures cleanup or restart logic is executed appropriately
        atexit.register(self.onExit)

    def onExit(self) -> None:
        """
        Called automatically at program exit. It decides the action to take based on `self.behavior`:
        - RESTART: Reconstructs the command-line arguments and restarts the program.
        - TERMINATE: Exits the program with a specified exit code.
        - NONE: Performs no action, allowing the program to exit naturally.
        """
        if self.behavior is Behavior.RESTART:
            # Handle restarting the program
            self._restart_program()
        elif self.behavior is Behavior.TERMINATE:
            # Handle terminating the program
            self._terminate_program()

    def _restart_program(self) -> None:
        """
        Restart the program by reconstructing the command-line arguments and using `os.execv`.
        - This method ensures the program restarts with the same Python interpreter and arguments.
        """
        # Construct the command to relaunch the program
        argv = [sys.executable] + sys.argv  # `sys.executable` gives the path to the Python interpreter

        # Avoid multiple restarts by adding a no-spawn flag if not already present
        if "--no-spawn" not in argv:
            argv.append("--no-spawn")

        # Remove any arguments that specify the current state, as the new process will generate its own
        argv = [s for s in argv if not s.startswith("--with-state")]

        # If a state file is specified, include it in the arguments for the restarted process
        if self.state_file:
            argv.append("--with-state=" + self.state_file)

        # Log the restart action for debugging and traceability
        logger.warning("Restarting program with arguments: %s", argv)

        # Restart the program; this replaces the current process with a new one
        # No code after this line will execute in the current process
        try:
            os.execv(sys.executable, argv)
        except Exception as e:
            logger.error("Failed to restart the program: %s", e)

    def _terminate_program(self) -> None:
        """
        Terminate the program with the specified exit code.
        - This bypasses Python's cleanup mechanisms for speed and simplicity.
        """
        # Log the termination action
        logger.warning("Terminating program with exit code: %d", self.exitcode)

        # Exit the program immediately, skipping any additional cleanup code
        os._exit(self.exitcode if self.exitcode else 0)


# Create a single instance of the `Duration` class.
# This shared instance can be used across the application to manage its lifecycle.
duration = Duration()
