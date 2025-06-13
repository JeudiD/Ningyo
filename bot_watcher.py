import subprocess
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import time
import threading

class RestartOnChangeHandler(FileSystemEventHandler):
    def __init__(self):
        self.process = None
        self.restart_timer = None
        self.start_process()

    def start_process(self):
        if self.process:
            self.process.terminate()
            self.process.wait()
        print("Starting bot.py...")
        self.process = subprocess.Popen(["python", "bot.py"])

    def on_modified(self, event):
        if (
            event.is_directory
            or "__pycache__" in event.src_path
            or not event.src_path.endswith(".py")
            or event.src_path.startswith(".#")
        ):
            return

        # Cancel any previously scheduled restart to debounce rapid events
        if self.restart_timer:
            self.restart_timer.cancel()

        print(f"{event.src_path} changed, scheduling bot restart...")

        # Schedule the restart 1 second later; resets if new event comes in
        self.restart_timer = threading.Timer(1.0, self.start_process)
        self.restart_timer.start()

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



