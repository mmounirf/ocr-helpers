import logging
import datetime


class CustomFormatter(logging.Formatter):
    """Logging colored formatter, adapted from https://stackoverflow.com/a/56944256/3638629"""

    GREY = '\x1b[38;21m'
    BLUE = '\x1b[38;5;39m'
    YELLOW = '\x1b[38;5;226m'
    RED = '\x1b[38;5;196m'
    BOLD_RED = '\x1b[31;1m'
    GREEN = '\x1b[38;5;34m'
    ORANGE = '\x1b[38;5;202m'
    MAGENTA = '\x1b[38;5;165m'
    CYAN = '\x1b[38;5;45m'
    RESET = '\x1b[0m'

    def __init__(self, fmt):
        super().__init__(fmt)

    def format(self, record):
        log_fmt = self._get_log_format(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)

    def _get_log_format(self, levelno):
        color = self._get_color(levelno)
        log_format = f"{color}%(asctime)s | %(message)s{self.RESET}"
        return log_format

    def _get_color(self, levelno):
        if levelno == logging.DEBUG:
            return self.GREY
        elif levelno == logging.INFO:
            return self.BLUE
        elif levelno == logging.WARNING:
            return self.YELLOW
        elif levelno == logging.ERROR:
            return self.RED
        elif levelno == logging.CRITICAL:
            return self.BOLD_RED
        elif levelno == logging.INFO + 1:
            return self.GREEN
        elif levelno == logging.INFO + 2:
            return self.ORANGE
        elif levelno == logging.INFO + 3:
            return self.MAGENTA
        elif levelno == logging.INFO + 4:
            return self.CYAN
        elif levelno == logging.INFO + 5:
            return self.BLUE
        elif levelno == logging.INFO + 6:
            return self.YELLOW
        elif levelno == logging.INFO + 7:
            return self.RED
        else:
            return ""


class CustomLogger(logging.Logger):
    """Custom logger with colored log messages"""

    def __init__(self, name, level=logging.DEBUG):
        super().__init__(name, level)
        self.formatter = CustomFormatter('%(asctime)s | %(message)s')

    def blue(self, msg):
        self.log(logging.INFO, msg)

    def yellow(self, msg):
        self.log(logging.WARNING, msg)

    def red(self, msg):
        self.log(logging.ERROR, msg)

    def critical(self, msg):
        self.log(logging.CRITICAL, msg)

    def green(self, msg):
        self.log(logging.INFO + 1, msg)

    def orange(self, msg):
        self.log(logging.INFO + 2, msg)

    def magenta(self, msg):
        self.log(logging.INFO + 3, msg)

    def cyan(self, msg):
        self.log(logging.INFO + 4, msg)

    def blue(self, msg):
        self.log(logging.INFO + 5, msg)

    def yellow(self, msg):
        self.log(logging.INFO + 6, msg)

    def red(self, msg):
        self.log(logging.INFO + 7, msg)


# Create custom logger logging all five levels
logger = CustomLogger(__name__)
logger.setLevel(logging.DEBUG)

# Define format for logs
fmt = '%(asctime)s | %(levelname)s | %(message)s'

# Create stdout handler for logging to the console (logs all five levels)
stdout_handler = logging.StreamHandler()
stdout_handler.setLevel(logging.DEBUG)
stdout_handler.setFormatter(logger.formatter)

# Create file handler for logging to a file (logs all five levels)
today = datetime.date.today()
file_handler = logging.FileHandler('my_app_{}.log'.format(today.strftime('%Y_%m_%d')))
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(logger.formatter)

# Add both handlers to the logger
logger.addHandler(stdout_handler)
logger.addHandler(file_handler)
