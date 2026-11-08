def UploadVideo(server_url: str, video_path: str, company_name: str) -> str:
    """Uploads a video file to the server and returns its URL."""
    import requests
    url = f"{server_url.rstrip('/')}/upload"
    with open(video_path, 'rb') as f:
        files = {'file': (video_path.split('/')[-1], f, 'video/webm')}
        data = {'company_name': company_name}
        response = requests.post(url, files=files, data=data)
    
    response.raise_for_status()
    return response.json()["video_url"]


def GetVideoURL(server_url: str, company_name: str) -> str:
    """Returns the video URL for the given company name."""
    import requests
    url = f"{server_url.rstrip('/')}/get_video_url"
    response = requests.get(url, params={'company_name': company_name})
    response.raise_for_status()
    return response.json()["video_url"]