import asyncio
import threading
import tkinter as tk
from tkinter import Canvas, ttk
from queue import Queue, Empty
from get_title import get_spotify_window_title
from api import get_lrc
import time
import win32api
import win32con
import win32gui

queue = Queue()
current_task = None
label_lyrics = None
label_translation = None
root = None
is_paused = False  # To track if the song is paused
current_line_index = 0  # To track the current line being displayed
lyrics_lines = []  # To store the parsed lyrics
last_displayed_timestamp = 0  # To store the timestamp of the last displayed line
pause_time = 0  # To store the time when the song was paused
current_song_title = None  # To store the title of the current song


def create_subtitle():
    global label_lyrics, label_translation, root

    root = tk.Tk()
    root.overrideredirect(True)  # Remove title bar
    root.attributes("-topmost", True)  # Keep on top

    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()

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
    global current_task, label_lyrics, label_translation, lyrics_lines, current_line_index, last_displayed_timestamp

    if current_task is not None:
        root.after_cancel(current_task)

    label_lyrics.config(text="")
    label_translation.config(text="")

    lyrics_lines.clear()  # Clear old lyrics
    current_line_index = 0  # Reset the current line index
    last_displayed_timestamp = 0  # Reset the last displayed timestamp

    for line in lrc.splitlines():
        if line.startswith("[") and "]" in line:
            timestamp = line.split("]")[0]
            text_with_translation = line.split("]")[1].strip()

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

    display_line(current_line_index)  # Start displaying lyrics from the first line


def display_line(index):
    global current_task, is_paused, current_line_index, last_displayed_timestamp, pause_time

    if is_paused or index >= len(lyrics_lines):
        return

    current_line_index = index  # Update the current line index

    timestamp, lyrics_text, translation_text = lyrics_lines[index]
    label_lyrics.config(text=lyrics_text)
    label_translation.config(text=translation_text)

    last_displayed_timestamp = timestamp  # Update the last displayed timestamp

    if index + 1 < len(lyrics_lines):
        next_timestamp = lyrics_lines[index + 1][0]
    else:
        next_timestamp = timestamp + 5  # Default to 5 seconds delay for the last line

    delay = max(0, (next_timestamp - timestamp) * 1000)

    # Adjust the delay if resuming after a pause
    if pause_time > 0:
        elapsed_pause_time = time.time() - pause_time
        delay -= int(elapsed_pause_time * 1000)
        pause_time = 0  # Reset pause time

    current_task = root.after(int(delay), lambda: display_line(index + 1))


def parse_timestamp(timestamp):
    minutes, seconds = timestamp[1:3], timestamp[4:9]
    return int(minutes) * 60 + float(seconds)


async def monitor():
    global is_paused, current_task, current_line_index, last_displayed_timestamp, pause_time, current_song_title

    last_title = None
    while True:
        current_title = await get_spotify_window_title()

        if current_title and current_title != last_title:
            last_title = current_title
            print(f"Music changed: {current_title}")

            if current_title.lower() in ["spotify", "spotify free"]:
                if not is_paused:
                    is_paused = True
                    pause_time = time.time()  # Record the pause time
                    if current_task is not None:
                        root.after_cancel(current_task)  # Pause lyrics
            else:
                if is_paused:
                    is_paused = False
                    if current_song_title != current_title:  # Check if the song has changed
                        lrc = await get_lrc(current_title)
                        if lrc:
                            queue.queue.clear()
                            queue.put(lrc)
                            current_song_title = current_title  # Update the current song title
                    else:
                        display_line(current_line_index)  # Resume from the current line
                else:
                    lrc = await get_lrc(current_title)
                    if lrc:
                        queue.queue.clear()
                        queue.put(lrc)
                        current_song_title = current_title  # Update the current song title


async def main():
    threading.Thread(target=create_subtitle).start()
    await monitor()


if __name__ == "__main__":
    asyncio.run(main())
