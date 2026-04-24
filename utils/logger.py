"""
utils/logger.py
Colored, structured terminal logging.
"""

from colorama import init, Fore, Style

init(autoreset=True)


class Logger:
    def banner(self):
        print(Fore.CYAN + Style.BRIGHT + """
╔═══════════════════════════════════════════╗
║       CommitGenerator_Edu  🎓             ║
║   Git Timestamp Education Tool            ║
║   For Educational Use Only               ║
╚═══════════════════════════════════════════╝
""" + Style.RESET_ALL)

    def info(self, msg):
        print(Fore.BLUE + f"[INFO]  " + Style.RESET_ALL + msg)

    def success(self, msg):
        print(Fore.GREEN + f"[OK]    " + Style.RESET_ALL + msg)

    def warning(self, msg):
        print(Fore.YELLOW + f"[WARN]  " + Style.RESET_ALL + msg)

    def error(self, msg):
        print(Fore.RED + f"[ERROR] " + Style.RESET_ALL + msg)

    def debug(self, msg):
        print(Fore.MAGENTA + f"[DEBUG] " + Style.RESET_ALL + msg)
