import requests
import asyncio


async def get_lrc(song_name):
    """
    Retrieves the lyrics (lrc format) for a given song.

    Parameters:
        song_name (str): The name of the song.

    Returns:
        lrc (str): The lyrics of the song in lrc format, or None if the song is not found.
    """
    id = await get_id(song_name=song_name)

    if id:
        url = f"https://api.injahow.cn/meting/?type=lrc&id={id}"
        req = requests.get(url=url)
        lrc = req.content.decode()
        print(lrc)

        return lrc
    else:
        return None


async def get_id(song_name):
    """
    Retrieves the ID of a song from the music.163.com API based on the given song name.

    Args:
        song_name (str): The name of the song to search for.

    Returns:
        song_id (int): The ID of the song if found, or None if no song is found.
    """
    url = f"https://music.163.com/api/search/get/web?csrf_token=hlpretag=&hlposttag=&s={song_name}&type=1&offset=0&total=true&limit=1"
    req = requests.get(url=url)
    data = req.json()
    # print(data)
    song_id = data["result"]["songs"][0]["id"]

    return song_id if song_id else None


async def main():
    await get_lrc("Gold Steps")


if __name__ == "__main__":
    asyncio.run(main())
