import asyncio
import threading
import tkinter as tk
from tkinter import ttk
from queue import Queue, Empty
from get_title import get_spotify_window_title
from api import get_lrc

queue = Queue()
current_task = None
label_lyrics = None
label_translation = None
root = None


def create_subtitle():
    """
    Create a subtitle window to display lyrics and translations.

    """
    global label_lyrics, label_translation, root

    root = tk.Tk()
    root.overrideredirect(True)  # Remove title bar
    root.attributes("-topmost", True)  # Keep on top

    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()

    # Set the window size and position it at the bottom of the screen
    root.geometry(
        f"{screen_width}x100+0+{screen_height - 100}"
    )  # Full width, bottom of the screen

    # Set up click-through functionality
    root.wm_attributes("-transparentcolor", "black")  # Set black as transparent color

    root.configure(bg="black")
    root.attributes("-alpha", 0.9)  # Set transparency

    # Create a frame to center text
    frame = tk.Frame(root, bg="black")
    frame.pack(fill=tk.X, pady=(10, 0))

    # Create labels for lyrics and translation
    label_lyrics = ttk.Label(
        frame,
        text="",
        font=("Arial", 18),
        background="black",
        foreground="white",
        anchor="center",
        justify="center",
    )
    label_lyrics.pack()

    label_translation = ttk.Label(
        frame,
        text="",
        font=("Arial", 14),
        background="black",
        foreground="white",
        anchor="center",
        justify="center",
    )
    label_translation.pack()

    # Run the Tkinter event loop
    def check_queue():
        try:
            lyrics = queue.get_nowait()
            update_lyrics(lyrics)
        except Empty:
            pass
        root.after(100, check_queue)  # Check the queue every 100ms

    root.after(100, check_queue)
    root.mainloop()


def update_lyrics(lrc):
    """
    Update the lyrics display with the provided LRC format lyrics.

    Args:
        lrc (str): The lyrics in LRC format.

    """
    global current_task, label_lyrics, label_translation

    # Cancel any previous scheduled tasks
    if current_task is not None:
        root.after_cancel(current_task)

    # Clear any remaining lyrics
    label_lyrics.config(text="")
    label_translation.config(text="")

    # Parse lyrics and timestamps
    lyrics_lines = []
    for line in lrc.splitlines():
        if line.startswith("[") and "]" in line:
            timestamp = line.split("]")[0]
            text_with_translation = line.split("]")[1].strip()
            # Split text and translation
            parts = text_with_translation.split("(")
            if len(parts) == 2:
                lyrics_text = parts[0].strip()
                translation_text = parts[1].strip(" )")
            else:
                lyrics_text = text_with_translation
                translation_text = ""

            lyrics_lines.append(
                (parse_timestamp(timestamp), lyrics_text, translation_text)
            )

    if not lyrics_lines:
        return

    def display_line(index):
        """
        Displays the lyrics and translation for a given index in the lyrics_lines list.

        Args:
            index (int): The index of the line to be displayed.

        """
        if index >= len(lyrics_lines):
            return

        timestamp, lyrics_text, translation_text = lyrics_lines[index]
        label_lyrics.config(text=lyrics_text)
        label_translation.config(text=translation_text)

        # Calculate delay for the next line
        if index + 1 < len(lyrics_lines):
            next_timestamp = lyrics_lines[index + 1][0]
        else:
            next_timestamp = (
                timestamp + 5
            )  # Default to 5 seconds delay for the last line

        delay = max(0, (next_timestamp - timestamp) * 1000)  # Convert to milliseconds
        global current_task
        current_task = root.after(
            int(delay), lambda: display_line(index + 1)
        )  # Schedule next line

    display_line(0)


def parse_timestamp(timestamp):
    """
    Convert a timestamp [00:00.00] to seconds.

    Args:
        timestamp (str): The timestamp string in the format [MM:SS.SS].

    Returns:
        timestamp (float): The converted timestamp in seconds.
    """
    minutes, seconds = timestamp[1:3], timestamp[4:9]
    return int(minutes) * 60 + float(seconds)


async def monitor():
    """
    Monitors the Spotify window title and retrieves the lyrics for the currently playing song.

    This function continuously checks for changes in the Spotify window title. If the title changes,
    it prints a message indicating that the music has changed. It then retrieves the lyrics for the
    current song and adds them to a queue.

    Note: This function assumes the existence of the following functions:
    - get_spotify_window_title(): Retrieves the current Spotify window title.
    - get_lrc(title): Retrieves the lyrics for the given song title.

    """
    last_title = None
    while True:
        current_title = await get_spotify_window_title()

        if current_title and current_title != last_title:
            last_title = current_title
            print(f"Music changed: {current_title}")

            lrc = await get_lrc(current_title)
            if lrc:
                queue.queue.clear()
                queue.put(lrc)


async def main():
    threading.Thread(target=create_subtitle).start()
    await monitor()


if __name__ == "__main__":
    asyncio.run(main())
