import win32gui
import win32process
import psutil


async def get_spotify_window_title():
    """
    Retrieves the window title of the Spotify application.

    Returns:
        title (str): The window title of the Spotify application, or None if Spotify is not running.
    """

    def callback(hwnd, windows):
        if win32gui.IsWindowVisible(hwnd):
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            process = psutil.Process(pid)
            if process.name().lower() == "spotify.exe":
                windows.append(win32gui.GetWindowText(hwnd))

    windows = []
    win32gui.EnumWindows(callback, windows)

    # print(windows[0])

    return windows[0] if windows else None


async def main():
    while True:
        await get_spotify_window_title()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main=main())
