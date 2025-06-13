import subprocess #IMPORTING THIS LETS THE CODE MANAGE NINGYO/EXTERNAL PROCESS
from watchdog.observers import Observer #IMPORTS A WATCHER TO MONITOR SYSTEM FILES
from watchdog.events import FileSystemEventHandler #IMPORTS BASE CLASS FOR HANDELING/MANAGEING FILE SYSTEM EVENTS (sounds like this just give the code perms to manage files)
import time #PROVIDES TIME RELATED FUNCTIONS (this is used to keep the program running)


class RestartOnChangeHandler(FileSystemEventHandler): #this class restart inherits filesystems |THIS CLASS WILL OVERRIDE METHODS TO REACT TO FILE CHANGES
    def __init__(self):
        self.process = None
        self.start_process()

    def start_process(self):
        if self.process:
            self.process.terminate() #THIS SECTION IS WHAT LOGS OUT AND IN THE BOT ON CODE EDIT| it terminates, waits for full terminate, then logs inagain
            self.process.wait()
        self.process = subprocess.Popen(["python", "bot.py"])  # Change "bot.py" to your bot file name

    def on_modified(self, event):
        if event.src_path.endswith(".py"):
            print(f"{event.src_path} changed, restarting bot...")
            self.start_process()

if __name__ == "__main__":
    path = "."  # watch current directory
    event_handler = RestartOnChangeHandler()
    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)
    observer.start()
    print("Watching for file changes. Press Ctrl+C to stop.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
