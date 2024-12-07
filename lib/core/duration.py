import signal  # Provides a way to handle OS-level signals (e.g., SIGINT, SIGTERM)
import subprocess  # Used to manage and run subprocesses for restarting the program
import structlog  # Modern library for structured logging
from enum import IntEnum  # Extends the enum functionality with integer comparison
from typing import Optional  # Used for type hints when a value can be None
import sys

# Set up a structured logger for better log clarity
logger = structlog.get_logger()

class Behavior(IntEnum):
    """
    Enum to define possible behaviors for the program lifecycle.
    - NONE: No special action on exit.
    - TERMINATE: Exit the program with a specified exit code.
    - RESTART: Restart the program with the same Python interpreter and arguments.
    """
    NONE = 0
    TERMINATE = 1
    RESTART = 2

class Duration:
    """
    Manages the lifecycle of the application:
    - Configures what happens when the application exits.
    - Supports behaviors like restart and termination.
    - Registers signal handlers for cleanup and graceful shutdown.
    """
    def __init__(self):
        self.behavior = Behavior.NONE  # Default behavior: do nothing
        self.exitcode: int = 0  # Exit code for termination
        self.state_file: Optional[str] = None  # Optional state file for restarts

        # Register signal handlers for process exit events
        signal.signal(signal.SIGINT, self.on_exit)  # Handle Ctrl+C (Interrupt)
        signal.signal(signal.SIGTERM, self.on_exit)  # Handle termination signals

    def on_exit(self, signal_received, frame):
        """
        Handles program exit events based on the current behavior:
        - RESTART: Rebuilds the command-line arguments and restarts the program.
        - TERMINATE: Ensures proper exit with the specified exit code.
        - NONE: No special action, allows normal termination.
        """
        logger.info(
            "Exiting program",
            signal=signal_received,
            behavior=self.behavior.name,
            exit_code=self.exitcode,
        )

        if self.behavior == Behavior.RESTART:
            self.restart_program()
        elif self.behavior == Behavior.TERMINATE:
            self.terminate_program()

    def restart_program(self):
        """
        Restart the program by rebuilding the command-line arguments and spawning a new process.
        """
        # Construct command-line arguments for the new process
        args = [sys.executable] + sys.argv  # Use the same Python interpreter and args
        if "--no-spawn" not in args:  # Avoid spawning loops
            args.append("--no-spawn")

        # Add the state file to the arguments if specified
        if self.state_file:
            args.append(f"--with-state={self.state_file}")

        logger.info("Restarting program", args=args)

        try:
            # Restart the program using subprocess
            subprocess.run(args)
        except Exception as e:
            logger.error("Failed to restart the program", error=str(e))

    def terminate_program(self):
        """
        Terminate the program with the specified exit code.
        """
        logger.warning("Terminating program", exit_code=self.exitcode)
        exit(self.exitcode if self.exitcode else 0)

# Global instance to manage program lifecycle
duration = Duration()

# Example Usage:
if __name__ == "__main__":
    # Simulate setting a behavior (e.g., Restart or Terminate)
    duration.behavior = Behavior.RESTART  # Change this to Behavior.TERMINATE to test termination
    duration.state_file = "example_state.json"  # Example of a state file (optional)
    logger.info("Program is running... Press Ctrl+C to exit.")
    
    # Simulate a long-running process
    try:
        while True:
            pass  # Replace with your application logic
    except KeyboardInterrupt:
        logger.info("Interrupt received. Exiting gracefully.")
