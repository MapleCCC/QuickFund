import requests

__all__ = ["get_latest_release_version", "get_latest_release_asset"]


# Reference to GitHub official REST API document:
# https://docs.github.com/en/rest

ENDPOINT = "https://api.github.com"


def get_latest_release_version(owner: str, repo: str) -> str:
    headers = {"accept": "application/vnd.github.v3+json"}
    response = requests.get(
        f"{ENDPOINT}/repos/{owner}/{repo}/releases/latest", headers=headers
    )
    response.raise_for_status()
    response.encoding = "utf-8"
    json_data = response.json()
    tag_name = json_data["tag_name"]
    return tag_name


def get_latest_release_id(owner: str, repo: str) -> int:
    headers = {"accept": "application/vnd.github.v3+json"}
    response = requests.get(
        f"{ENDPOINT}/repos/{owner}/{repo}/releases/latest", headers=headers
    )
    response.raise_for_status()
    response.encoding = "utf-8"
    json_data = response.json()
    release_id = json_data["id"]
    return release_id


def download_asset(owner: str, repo: str, asset_id: str) -> bytes:
    # TODO: add display progress bar when downloading latest asset
    headers = {"Accept": "application/octet-stream"}
    download_url = f"{ENDPOINT}/repos/{owner}/{repo}/releases/assets/{asset_id}"
    r = requests.get(download_url, headers=headers,)
    r.raise_for_status()
    return r.content


def get_latest_release_asset(owner: str, repo: str, asset_name: str) -> bytes:
    print("获取最新分发版本......")
    headers = {"accept": "application/vnd.github.v3+json"}
    response = requests.get(
        f"{ENDPOINT}/repos/{owner}/{repo}/releases/latest", headers=headers
    )
    response.raise_for_status()
    response.encoding = "utf-8"
    json_data = response.json()
    assets = json_data["assets"]
    candidates = list(filter(lambda asset: asset["name"] == asset_name, assets))
    if len(candidates) == 0:
        raise RuntimeError(
            f"No asset with name {asset_name} can be found in the latest release"
        )
    elif len(candidates) > 1:
        raise RuntimeError(
            f"More than one assets with name {asset_name} are found in the latest release"
        )
    that_asset = candidates[0]
    that_asset_id = that_asset["id"]
    print("下载最新版本......")
    return download_asset(owner, repo, that_asset_id)


def create_release(
    owner: str,
    repo: str,
    tag_name: str,
    *,
    target_commitish: str = None,
    name: str = None,
    body: str = None,
    draft: bool = None,
    prerelease: bool = None,
) -> None:
    # Reference: https://docs.github.com/en/rest/reference/repos#create-a-release
    # https://developer.github.com/v3/repos/releases/#create-a-release
    headers = {
        "accept": "application/vnd.github.v3+json",
        "tag_name": tag_name,
        "target_commitish": target_commitish,
        "name": name,
        "body": body,
        "draft:": draft,
        "prerelease:": prerelease,
    }
    r = requests.post(f"{ENDPOINT}/repos/{owner}/{repo}/releases", headers=headers)
    r.raise_for_status()
    if r.status_code != 201:
        raise RuntimeError("Error when create release")


def upload_asset(
    owner: str, repo: str, release_id: int, filename: str, content_type: str
) -> None:
    headers = {"accept": "application/vnd.github.v3+json"}
    file_tuple = (filename, open(filename, "rb"))
    if content_type:
        file_tuple += (content_type,)
    files = {"file": file_tuple}
    url = f"{ENDPOINT}/repos/{owner}/{repo}/releases/{release_id}/assets"
    r = requests.post(url, headers, files=files)
    r.raise_for_status()
    if r.status_code != 201:
        raise RuntimeError("Error when upload asset")
