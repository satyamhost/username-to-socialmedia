from flask import Flask, request, jsonify
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

app = Flask(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36"
}

PLATFORMS = {
    "github": "https://github.com/{}",
    "instagram": "https://www.instagram.com/{}/",
    "twitter": "https://x.com/{}",
    "tiktok": "https://www.tiktok.com/@{}",
    "pinterest": "https://www.pinterest.com/{}/",
    "reddit": "https://www.reddit.com/user/{}/",
    "medium": "https://medium.com/@{}",
    "github_gist": "https://gist.github.com/{}",
    "steam": "https://steamcommunity.com/id/{}",
    "telegram_preview": "https://t.me/{}"
}

TIMEOUT = 8


def check_username(platform, url_template, username):
    url = url_template.format(username)

    try:
        response = requests.get(
            url,
            headers=HEADERS,
            timeout=TIMEOUT,
            allow_redirects=True
        )

        status_code = response.status_code
        final_url = response.url

        found = False

        if platform in ["github", "github_gist", "reddit", "medium", "pinterest", "steam", "telegram_preview"]:
            found = status_code == 200

        elif platform == "instagram":
            # Instagram aksar login page de deta hai, isliye simple existence अंदाज़ा
            if status_code == 200 and "Page Not Found" not in response.text and "login" not in final_url.lower():
                found = True
            elif status_code == 200 and username.lower() in response.text.lower():
                found = True

        elif platform == "twitter":
            if status_code == 200 and "This account doesn’t exist" not in response.text:
                found = True

        elif platform == "tiktok":
            if status_code == 200 and "Couldn't find this account" not in response.text:
                found = True

        return {
            "platform": platform,
            "url": url,
            "found": found,
            "status_code": status_code
        }

    except requests.RequestException as e:
        return {
            "platform": platform,
            "url": url,
            "found": False,
            "status_code": None,
            "error": str(e)
        }


@app.route("/")
def home():
    return jsonify({
        "success": True,
        "message": "Username OSINT API is running",
        "developer": "@TEAMRAX0",
        "endpoint": "/username?user=example"
    })


@app.route("/username", methods=["GET"])
def username_lookup():
    username = request.args.get("user", "").strip()

    if not username:
        return jsonify({
            "success": False,
            "error": "Missing required parameter: user"
        }), 400

    if len(username) < 2 or len(username) > 50:
        return jsonify({
            "success": False,
            "error": "Username length must be between 2 and 50 characters"
        }), 400

    results = []
    found_on = []

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [
            executor.submit(check_username, platform, url_template, username)
            for platform, url_template in PLATFORMS.items()
        ]

        for future in as_completed(futures):
            result = future.result()
            results.append(result)
            if result.get("found"):
                found_on.append(result["platform"])

    results.sort(key=lambda x: x["platform"])

    return jsonify({
        "success": True,
        "developer": "@TEAMRAX0",
        "query": username,
        "total_checked": len(PLATFORMS),
        "total_found": len(found_on),
        "found_on": found_on,
        "results": results
    })


if __name__ == "__main__":
    app.run(debug=True)
