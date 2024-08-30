import requests
import re

# GitHub API endpoint for geodrillcalc releases
REPO_API_URL = "https://api.github.com/repos/08dhuh/geodrillcalc/releases/latest"
response = requests.get(REPO_API_URL)
release_info = response.json()

latest_asset_url = ""
for asset in release_info["assets"]:
    if asset["name"].endswith(".whl"):
        latest_asset_url = asset["browser_download_url"]
        break

if not latest_asset_url:
    raise ValueError("No wheel file found in the latest release.")

with open("requirements.txt", "r") as f:
    lines = f.readlines()

with open("requirements.txt", "w") as f:
    for line in lines:
        if line.startswith("geodrillcalc @ "):
            f.write(f"geodrillcalc @ {latest_asset_url}\n")
            break
        else:
            f.write(line)

print("requirements.txt has been updated with the latest geodrillcalc release.")
