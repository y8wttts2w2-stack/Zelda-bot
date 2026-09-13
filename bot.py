import json
import time
import requests
from bs4 import BeautifulSoup

WEBHOOK = "https://discord.com/api/webhooks/1548476529246470285/-i8-BxsjV5uCKnOE2b8ssfXSsN5TtVOek-GE56NU-0uNrZU7iCspG9IztjrjMwFYS2mk"

CHECK_INTERVAL = 15
CONFIRM_DELAY = 3
CONFIRM_CHECKS = 3

with open("retailers.json") as f:
    retailers = json.load(f)

last_status = {}


def check_site(name, url):
    try:
        r = requests.get(
            url,
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=30
        )

        if r.status_code != 200:
            return "NO DATA"

        if name.lower() == "nintendo":
            if "OutOfStock" in r.text:
                return "UNAVAILABLE"

            if "InStock" in r.text:
                return "AVAILABLE"

            return "NO DATA"

        soup = BeautifulSoup(r.text, "html.parser")

        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()

        text = soup.get_text(" ", strip=True).lower()

        if any(x in text for x in [
            "out of stock",
            "sold out",
            "currently unavailable"
        ]):
            return "UNAVAILABLE"

        if any(x in text for x in [
            "add to cart",
            "add for shipping",
            "buy now"
        ]):
            return "AVAILABLE"

        return "NO DATA"

    except Exception as e:
        print(name, "error:", e)
        return "NO DATA"

def confirm_stock(name, url):
    print("Possible stock:", name)

    for n in range(1, CONFIRM_CHECKS + 1):
        status = check_site(name, url)

        print(
            "Confirmation",
            n,
            "/",
            CONFIRM_CHECKS,
            "=>",
            status
        )

        if status != "AVAILABLE":
            print("Stock not confirmed.")
            return False

        if n < CONFIRM_CHECKS:
            time.sleep(CONFIRM_DELAY)

    print("STOCK CONFIRMED:", name)
    return True


def alert(name, url):
    try:
        r = requests.post(
            WEBHOOK,
            json={
                "content": (
                    "ZELDA SWITCH 2 ALERT!\n\n"
                    "Retailer: " + name + "\n"
                    "Status: CONFIRMED AVAILABLE\n\n"
                    + url
                )
            },
            timeout=15
        )

        print("Discord:", r.status_code)

    except Exception as e:
        print("Discord error:", e)


print("Zelda Switch 2 Stock Monitor")
print("Checking every", CHECK_INTERVAL, "seconds...")
print()

while True:

    for retailer in retailers:

        if not retailer.get("enabled", True):
            continue

        name = retailer["name"]
        url = retailer["url"]

        status = check_site(name, url)

        print(name, "=>", status)

        previous = last_status.get(name)

        if status == "AVAILABLE" and previous != "AVAILABLE":
            if confirm_stock(name, url):
                alert(name, url)

        last_status[name] = status

    print("---")
    time.sleep(CHECK_INTERVAL)
