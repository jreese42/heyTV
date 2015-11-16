from datetime import datetime

class Logger:
    fd = -1

    def __init__(self, fd):
        """Initialize a logger instance which will write to fd"""
        self.fd = fd    

    def logDebug(self, text):
        """Print a debug message containing text"""
        time = datetime.now().strftime("%H:%M:%S ")
        self.log(time + "(DBG):\t", text)

    def logWarning(self, text):
        """Print a debug message containing text"""
        time = datetime.now().strftime("%H:%M:%S ")
        self.log(time + "(WARN):\t", text)

    def logError(self, text):
        """Print a debug message containing text"""
        time = datetime.now().strftime("%H:%M:%S ")
        self.log(time + "(ERR):\t", text)



    def log(self, prefix, text):
        """Print a log message with a prefix"""
        if self.fd > -1:
            self.fd.write(prefix + text + "\n")
        
