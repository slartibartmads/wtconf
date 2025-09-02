import yaml                  # for reading/writing YAML config files
import subprocess            # to run external programs (like your editor)
import sys                   # for exiting the program
import os                    # for system calls (like clearing the screen)
import argparse              # for handling command-line arguments
from pathlib import Path     # for resolving paths
import shutil

def init():
    CONFIG_DIR = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / ""
    SETTINGS_FILE = CONFIG_DIR/"wtconf" / "settings.yaml"
    CONFIGLIST_FILE = CONFIG_DIR/"wtconf" /"configlist.yaml"

    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)

    if not CONFIGLIST_FILE.exists():
        CONFIGLIST_FILE.touch()
    if not SETTINGS_FILE.exists():
        SETTINGS_FILE.write_text("editor: nano")

    # Load the list of config files from YAML file into a Python dictionary
    with open(CONFIGLIST_FILE) as f:
        loaded = yaml.safe_load(f) or {}

    # Load config.yaml
    with open(SETTINGS_FILE) as f:
        config = yaml.safe_load(f) or {}

    editor = config.get("editor", "nano") # fallback to nano if missing        


init()

# Setup argparse: this defines what arguments the program accepts
parser = argparse.ArgumentParser(description="wtconf is a tiny config file launcher")
parser.add_argument("--add", help="Add new config")  # e.g. configulator --add /etc/foo.conf
args = parser.parse_args()






# Handle adding new configs to CONFIGLIST_FILE
if args.add:
#    print(args.add)  # TEMP: show what was passed in (for debugging/learning)
    path = Path(args.add).expanduser().resolve()
    label = os.path.splitext(os.path.basename(args.add))[0]

    # add to dict
    loaded[label] = str(path)

    # write to YAML
    with open(CONFIGLIST_FILE, "w") as f:
        yaml.safe_dump(loaded, f, sort_keys=False)

        print(f"Added {label}: {path}")






banner = r"""
          _                   __ 
__      _| |_ ___ ___  _ __  / _|
\ \ /\ / / __/ __/ _ \| '_ \| |_ 
 \ V  V /| || (_| (_) | | | |  _|
  \_/\_/  \__\___\___/|_| |_|_|  
a tiny config launcher
  
  
"""

def print_centered(text):
    cols = 60
    for line in text.splitlines():
        # .center pads the line with spaces on both sides
        print(line.center(cols))

def print_config():
    """Main menu loop: show configs, let user pick one, open it in editor."""
    while True:
        # Clear terminal for a clean look each time
        os.system("clear")
        print_centered(banner)
        #print(banner)
        
        # Print table header
        print(f"{'ID':<3} {'Label'.ljust(16)} Path")
        print("-" * 60)

        # Convert configs dict into list of (label, path) pairs
        items = list(loaded.items())

        # Print each config as a row with an index number
        for i, (key, value) in enumerate(items, start=1):
            print(f"{i:<3} {key.ljust(16)} {value}")

        def get_selection(items):
            """Ask user to select a config ID or quit."""
            while True:
                selection = input("\nSelect ID, (s)ettings, (c)onfigist or (q)uit: ").strip()
                if not selection.isdigit():
                    # Handle non-numbers
                    if selection.lower() == "q":
                        print("\nSo long!\n")
                        sys.exit(0)  # exit the whole program
                    if selection.lower() =="s":
                        subprocess.run([editor, SETTINGS_FILE]).returncode
                    if selection.lower() == "c":
                        subprocess.run([editor, CONFIGLIST_FILE]).returncode
                    print("ID must be a number.")
                    continue
                # Convert selection to list index
                idx = int(selection) - 1
                if 0 <= idx < len(items):
                    return items[idx]   # returns (label, path)
                print("ID out of range.")

        # Wait for user to pick a config
        label, path = get_selection(items)

        # Open the config in the editor (micro)
        # This blocks until the editor is closed
        rc = subprocess.run([editor, path]).returncode

        # If editor exits with error code, let the user know
        if rc != 0:
            print(f"\n(editor exited with code {rc})\n")
            input("Press Enter to continue")

# Default behavior: if no --add argument is passed, show the menu
if args.add is None:
    print_config()