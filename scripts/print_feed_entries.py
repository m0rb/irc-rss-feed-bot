"""Print entries from a specific configured feed.

The feed settings are parsed from the user configuration file.

Usage:
CLI arg example: --config-path ~/irc-rss-feed-bot/config.yaml
Customize CHANNEL and FEED.
"""

import logging
import os

import bitlyshortener

from ircrssfeedbot import config
from ircrssfeedbot.__main__ import load_instance_config
from ircrssfeedbot.feed import Feed

# pylint: disable=invalid-name

CHANNEL = "##CoV"  # CUSTOMIZE
# FEED = "stats:🌎"  # World
FEED = "stats:🇺🇸"  # USA
# FEED = "stats:🇮🇹"  # Italy
# FEED = "stats:🇷🇺"  # Russia
# FEED = "stats:🇨🇳"  # China
# FEED = "COVID-19:stats:USA:NY"
CHANNEL, FEED = "##CoV", "LitCovid:TSV"

config.LOGGING["loggers"][config.PACKAGE_NAME]["level"] = "DEBUG"  # type: ignore
config.configure_logging()

log = logging.getLogger(__name__)

config.runtime.alert = lambda *args: log.exception(args[0])
config.runtime.identity = ""
load_instance_config(log_details=False)
config.INSTANCE["feeds"][CHANNEL][FEED]["style"] = None

_url_shortener = bitlyshortener.Shortener(
    tokens=[token.strip() for token in os.environ["BITLY_TOKENS"].strip().split(",")],
    max_cache_size=config.BITLY_SHORTENER_MAX_CACHE_SIZE,
)

feed = Feed(channel=CHANNEL, name=FEED, db=None, url_shortener=_url_shortener)  # type: ignore
# feed = Feed(channel=CHANNEL, name=FEED, db=None, url_shortener=None)  # type: ignore
for index, entry in enumerate(feed.entries[:100]):
    post = f"\n#{index + 1:,}: {entry.message}"
    if entry.categories:
        post += "\nCategories: " + ", ".join(entry.categories)
    print(post)
