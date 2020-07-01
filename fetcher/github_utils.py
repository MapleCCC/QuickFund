import requests

__all__ = ["get_latest_released_version", "get_latest_released_asset"]


def get_latest_released_version(user: str, repo: str) -> str:
    # TODO Handle the case when the lastest release's tag name is not semantic
    # version.
    response = requests.get(
        f"https://api.github.com/repos/{user}/{repo}/releases/latest"
    )
    response.encoding = "utf-8"
    json_data = response.json()
    tag_name = json_data["tag_name"]
    return tag_name


def get_latest_released_asset(user: str, repo: str, asset_name: str) -> bytes:
    print("获取最新分发版本......")
    response = requests.get(
        f"https://api.github.com/repos/{user}/{repo}/releases/latest"
    )
    response.encoding = "utf-8"
    json_data = response.json()
    assets = json_data["assets"]
    candidates = list(filter(lambda asset: asset["name"] == asset_name, assets))
    if len(candidates) == 00:
        raise RuntimeError(
            f"No asset with name {asset_name} can be found in the latest release"
        )
    elif len(candidates) > 1:
        raise RuntimeError(
            f"More than one assets with name {asset_name} are found in the latest release"
        )
    asset = candidates[0]
    print("下载最新版本......")
    # TODO: add display progress bar when downloading latest asset
    return requests.get(
        asset["url"], headers={"Accept": "application/octet-stream"}
    ).content
