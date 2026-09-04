#!/usr/bin/env python3
"""
Fetch OpenAI official chatgpt-voice.json and generate Shadowrocket ruleset files.
"""

import urllib.request
import json
import os
import datetime

VOICE_JSON_URL = "https://openai.com/chatgpt-voice.json"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

# Extra known LiveKit Cloud / WebRTC relay IPs observed in production
EXTRA_IPS = [
    (4, "20.219.124.186/32"),  # Microsoft Azure South India (Chennai) - LiveKit Cloud *.rtc.livekit.cloud
]

def fetch_voice_prefixes():
    req = urllib.request.Request(VOICE_JSON_URL, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    
    prefixes = set()
    for item in data.get("prefixes", []):
        if "ipv4Prefix" in item:
            prefixes.add((4, item["ipv4Prefix"].strip()))
        if "ipv6Prefix" in item:
            prefixes.add((6, item["ipv6Prefix"].strip()))
            
    for item in EXTRA_IPS:
        prefixes.add(item)
        
    def sort_key(item):
        ip_ver, prefix = item
        if ip_ver == 4:
            ip_str = prefix.split("/")[0]
            octets = [int(x) for x in ip_str.split(".")]
            return (4, octets)
        return (6, prefix)

    return sorted(list(prefixes), key=sort_key), data.get("creationTime", "")

def build_ruleset_content(sorted_prefixes, creation_time):
    now_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    lines = [
        "# NAME: ChatGPT-Voice",
        "# AUTHOR: neffepito",
        "# REPO: https://github.com/neffepito/proxy",
        f"# SOURCE: {VOICE_JSON_URL}",
        f"# SOURCE CREATION TIME: {creation_time}",
        f"# UPDATED: {now_str}",
        f"# TOTAL: {len(sorted_prefixes)}",
        ""
    ]
    for ip_ver, prefix in sorted_prefixes:
        cidr_tag = "IP-CIDR6" if ip_ver == 6 else "IP-CIDR"
        lines.append(f"{cidr_tag},{prefix},no-resolve")
    lines.append("")
    return "\n".join(lines)

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    target_files = [
        os.path.join(base_dir, "Shadowrocket", "Filter", "AI", "ChatGPT-Voice.list"),
        os.path.join(base_dir, "ruleset", "ChatGPT-Voice.list")
    ]
    
    prefixes, creation_time = fetch_voice_prefixes()
    content = build_ruleset_content(prefixes, creation_time)
    
    for tf in target_files:
        os.makedirs(os.path.dirname(tf), exist_ok=True)
        with open(tf, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Successfully generated {tf} ({len(prefixes)} entries)")

if __name__ == "__main__":
    main()
