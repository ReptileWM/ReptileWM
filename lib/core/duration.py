import atexit  # Provides a way to register functions that will run when the program exits
import enum  # Used to define an enumeration for predefined constants
import os  # Enables interaction with the operating system
import sys  # Provides access to system-specific parameters and functions
import logging

logger = logging.getLogger("logger")

# Define the public API of this module
__all__ = [
    "duration",
]

# Define an enumeration for the possible behaviors of the duration
Behavior = enum.Enum("Behavior", "NONE TERMINATE RESTART")


class Duration:
    """
    This class handles the duration of the application, ensuring that critical cleanup
    and specific exit behaviors are executed properly. 

    Notes:
    - The primary goal is to manage termination and restart behavior of the reptile window manager.
    - Uses `atexit` to ensure some actions are executed at the last possible moment before termination.
    - Be cautious about keeping references in this class, as objects referenced here won't be
      garbage-collected during program termination.
    """

    def __init__(self) -> None:
        # Default duration behavior: do nothing
        self.behavior = Behavior.NONE
        
        # Exit code to be used when the application terminates
        self.exitcode: int = 0
        
        # Optional state file for storing information during a restart
        self.state_file: str | None = None
        
        # Register the `onExit` method to run automatically when the program exits
        atexit.register(self.onExit)

    def onExit(self) -> None:
        """
        Handles the specific behaviors during the program's termination or restart.

        - If `Behavior.RESTART`, restarts the program using `os.execv`.
        - If `Behavior.TERMINATE`, ensures a proper exit with a specified exit code.
        - If `Behavior.NONE`, no special action is performed.
        """
        if self.behavior is Behavior.RESTART:
            # Reconstruct the command-line arguments for restarting
            argv = [sys.executable] + sys.argv  # sys.executable gives the Python interpreter
            
            # Avoid spawning multiple restarts
            if "--no-spawn" not in argv:
                argv.append("--no-spawn")
            
            # Remove arguments related to the current state
            argv = [s for s in argv if not s.startswith("--with-state")]
            
            # Include the state file in the new arguments if specified
            if self.state_file is not None:
                argv.append("--with-state=" + self.state_file)
            
            # Log the restart action
            logger.warning("Restarting Reptile with os.execv(...)")
            
            # Restart the process (no code after this line will execute)
            os.execv(sys.executable, argv)

        elif self.behavior is Behavior.TERMINATE:
            # Log the termination action
            logger.warning("Reptile will now terminate")
            
            # Exit immediately using `os._exit`, skipping cleanup for speed
            # Useful to avoid executing additional atexit handlers
            if self.exitcode:  # Ensure an exit code is specified
                os._exit(self.exitcode)

        elif self.behavior is Behavior.NONE:
            # Do nothing, effectively a no-op
            pass


# Create a single instance of the Duration class
# This instance can be used throughout the application to manage its duration
duration = Duration()
