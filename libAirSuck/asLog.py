"""
asLog by ThreeSixes (https://github.com/ThreeSixes)

This project is licensed under GPLv3. See COPYING for dtails.

This file is part of the airSuck project (https://github.com/ThreeSixes/airSuck).
"""

# Imports
import datetime
import syslog

# Main class
class asLog():
    """
    airSuck logging class.
    """
    
    def __init__(self, loggingMode="stdout"):
        """
        Class constructor
        """
        
        # Check for acceptable logging mode.
        if loggingMode in ('stdout', 'syslog', 'none'):
            # Set class-wide logging mode.
            self.mode = loggingMode
        else:
            raise ValueError("Loging mode not specified.")
        
        if loggingMode == "syslog":
            syslog.openlog(logoption=syslog.LOG_PID, facility=syslog.LOG_DAEMON)
    
    def __logStdout(self, message):
        """
        __logStdout(message)
        
        Log a message to stdout with a UTC timestamp.
        """
        # Get timestamp.
        dts = str(datetime.datetime.utcnow())
        
        # Keep the log looking pretty and uniform.
        if len(dts) == 19:
            dts = dts + ".000000"
        
        # Dump the message.
        print("%s - %s" %(dts, message))
    
    def __logSyslog(self, message, sev=syslog.LOG_NOTICE):
        """
        __logSyslog(message, [sev])
        
        Log a message to syslog.
        """
        
        # Log it.
        syslog.syslog(sev, message)
    
    def log(self, message):
        """
        log(message)
        
        Log a message.
        """
        
        # If we don't want to do anything...
        if self.mode == "stdout":
            # Log to stdout.
            self.__logStdout(message)
        
        elif self.mode == "syslog":
            # Log to syslog. Not fully implemented yet.
            self.__logSyslog(message)
        
        elif self.mode == "none":
            # This logs absolutely nothing.
            None