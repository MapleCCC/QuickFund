import requests

from .utils import try_catch_raise


__all__ = ["get_latest_release_version", "get_latest_release_asset"]


# Reference to GitHub official REST API document:
# https://docs.github.com/en/rest

ENDPOINT = "https://api.github.com"


@try_catch_raise(RuntimeError, "获取 {owner}/{repo} 最新发布版本时出现错误")
def get_latest_release_version(owner: str, repo: str) -> str:
    """
    Get the latest release version of a repository of the url: https://github.com/<owner>/<repo>
    """

    # According to the GitHub REST API doc, it's recommended to specify the ACCEPT key to following value in the request header.
    headers = {"accept": "application/vnd.github.v3+json"}
    response = requests.get(
        f"{ENDPOINT}/repos/{owner}/{repo}/releases/latest", headers=headers
    )
    response.raise_for_status()
    response.encoding = "utf-8"
    json_data = response.json()
    tag_name = json_data["tag_name"]
    return tag_name


@try_catch_raise(
    RuntimeError, "下载 GitHub 仓库 {owner}/{repo} 中 asset id 为 {asset_id} 的 asset 时发生错误"
)
def download_asset(owner: str, repo: str, asset_id: str) -> bytes:
    """
    Download the asset with given asset id from a repository of the url: https://github.com/<owner>/<repo>
    """

    # TODO: add display progress bar when downloading latest asset
    # According to the GitHub REST API doc, it's recommended to specify the ACCEPT key to following value in the request header.
    headers = {"Accept": "application/octet-stream"}
    download_url = f"{ENDPOINT}/repos/{owner}/{repo}/releases/assets/{asset_id}"
    r = requests.get(download_url, headers=headers,)
    r.raise_for_status()
    return r.content


@try_catch_raise(
    RuntimeError, "下载 GitHub 仓库 {owner}/{repo} 中 asset 名为 {asset_name} 的 asset 时发生错误"
)
def get_latest_release_asset(owner: str, repo: str, asset_name: str) -> bytes:
    """
    Download the latest released asset with given asset name from a repository of the url: https://github.com/<owner>/<repo>
    """

    print("获取最新分发版本......")
    # According to the GitHub REST API doc, it's recommended to specify the ACCEPT key to following value in the request header.
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
