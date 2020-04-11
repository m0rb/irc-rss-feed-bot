# irc-rss-feed-bot
**irc-rss-feed-bot** is a Python 3.8 and IRC based RSS/Atom and scraped HTML/JSON/CSV feed posting bot.
It essentially posts the entries of feeds in IRC channels, one entry per message.
More specifically, it posts the titles and shortened URLs of entries.

If viewing this readme on Docker Hub, note that it may be misformatted.
In this case, it can be viewed correctly on [GitHub](https://github.com/impredicative/irc-rss-feed-bot).

## Features
* Multiple channels on an IRC server are supported, with each channel having its own set of feeds.
For use with multiple servers, a separate instance of the bot process can be run for each server.
* Entries are posted only if the channel has not had any conversation for a certain minimum amount of time, 
thereby avoiding the interruption of any preexisting conversations.
This amount of time is 15 minutes for any feed which has a polling period greater than 12 minutes.
There is however no delay for any feed which has a polling period less than or equal to 12 minutes as such a feed is
considered urgent.
* A SQLite database file records hashes of the entries that have been posted, thereby preventing them from being
reposted.
* The [`hext`](https://pypi.org/project/hext/), [`jmespath`](https://pypi.org/project/jmespath/), and 
[`pandas`](https://pandas.pydata.org/) DSLs are supported for flexibly parsing arbitrary HTML, JSON, and CSV content 
respectively.
* Entry titles are formatted for neatness.
Any HTML tags and excessive whitespace are stripped, all-caps are replaced,
and excessively long titles are sanely truncated. 
* ETag and TTL based compressed in-memory caches of URL content are conditionally used for preventing unnecessary URL
reads.
Any websites with a mismatched _strong_ ETag are probabilistically detected, and this caching is then disabled for them
for the duration of the process. Note that this detection is skipped for a _weak_ ETag.
The TTL cache is used only for URLs that are used by more than one feed each.
* Encoded Google News URLs are decoded.

For more features, see the customizable [global settings](#global-settings) and
[feed-specific settings](#feed-specific-settings).

## Links
* Code: https://github.com/impredicative/irc-rss-feed-bot
* Changelog: https://github.com/impredicative/irc-rss-feed-bot/releases
* Container: https://hub.docker.com/r/ascensive/irc-rss-feed-bot

## Examples
```text
<Feed[bot]> [ArXiv:cs.AI] Concurrent Meta Reinforcement Learning → https://arxiv.org/abs/1903.02710v1
<Feed[bot]> [ArXiv:cs.AI] Attack Graph Obfuscation → https://arxiv.org/abs/1903.02601v1
<Feed[bot]> [InfoWorld] What is a devops engineer? And how do you become one? → https://j.mp/2NOgQ3g
<Feed[bot]> [InfoWorld] What is Jupyter Notebook? Data analysis made easier → https://j.mp/2NMailP
<Feed[bot]> [AWS:OpenData] COVID-19 Open Research Dataset (CORD-19): Full-text and metadata dataset of
COVID-19 and coronavirus-related research articles. → https://registry.opendata.aws/cord-19
```
![](images/sample_posts.png)

## Usage
### Configuration: secret
Prepare a private `secrets.env` environment file using the sample below.
```ini
IRC_PASSWORD=YourActualPassword
BITLY_TOKENS=5e71a58b19582f48edcb0235637ac3536dd3b6dc,bd90119a7b617e81b293ddebbbfed3e955eac5af,42f309642a018e6b4d7cfba6854080719dccf0cc,0819552eb8b42e52dbc8b4c3e1654f5cd96c0dcc,430a002fe9d4e8f94097f7a5cd974ffce85eb605,71f9856bc96c6a8eabeac4f763daaec16896e183,81f6d477cfcef006a6dd35c4b947d1c1fdcbf445,06441b445c75d2251f0a56ae87506c69dc468af5,1e71089487fb70f42fff51b7ad49f192ffcb00f2
```

Bitly tokens are required for shortening URLs.
URL shortening is enabled for all feeds by default but can be disabled selectively per feed.
The sample tokens above are for illustration only and are invalid.
To obtain tokens, refer to [these instructions](https://github.com/impredicative/bitlyshortener#usage).
Providing multiple comma-separated tokens, perhaps as many as 20 free ones or sufficient commercial ones, is required.
Failing this, Bitly imposed rate limits for shortening URLs will lead to errors.
If there are errors, the batched new entries in a feed may get reprocessed the next time the feed is read.
It is safer to provide more tokens than are necessary.

### Configuration: non-secret
Prepare a version-controlled `config.yaml` file using the sample below.
A full-fledged real-world example is also
[available](https://github.com/impredicative/freenode-bots/blob/master/irc-rss-feed-bot/config.yaml).
```yaml
host: chat.freenode.net
ssl_port: 6697
nick: MyFeed[bot]
alerts_channel: '##mybot-alerts'
mode:
defaults:
  new: all
feeds:
  "##mybot-alerts":
    irc-rss-feed-bot:
      url: https://github.com/impredicative/irc-rss-feed-bot/releases.atom
      period: 12
      shorten: false
  "#some_chan1":
    AWS:OpenData:
      url: https://registry.opendata.aws/rss.xml
      message:
        summary: true
    j:AJCN:
      url: https://academic.oup.com/rss/site_6122/3981.xml
      period: 12
      blacklist:
        title:
          - ^Calendar\ of\ Events$
    MedicalXpress:nutrition:
      url: https://medicalxpress.com/rss-feed/search/?search=nutrition
    r/FoodNerds:
      url: https://www.reddit.com/r/FoodNerds/new/.rss
      shorten: false
      sub:
        url:
          pattern: ^https://www\.reddit\.com/r/.+?/comments/(?P<id>.+?)/.+$
          repl: https://redd.it/\g<id>
    LitCovid:
      url: https://www.ncbi.nlm.nih.gov/research/coronavirus-api/export
      pandas: |-
        read_csv(file, comment="#", sep="\t") \
        .assign(link=lambda r: "https://pubmed.ncbi.nlm.nih.gov/" + r["pmid"].astype("str")) \
        .convert_dtypes()
  "##some_chan2":
    ArXiv:cs.AI: &ArXiv
      url: http://export.arxiv.org/rss/cs.AI
      period: 1.5
      https: true
      shorten: false
      group: ArXiv:cs
      alerts:
        empty: false
      format:
        re:
          title: '^(?P<name>.+?)\.?\ \(arXiv:.+(?P<ver>v\d+)\ '
        str:
          title: '{name}'
          url: '{url}{ver}'
    ArXiv:cs.NE:
      <<: *ArXiv
      url: http://export.arxiv.org/rss/cs.NE
    ArXiv:stat.ML:
      <<: *ArXiv
      url: http://export.arxiv.org/rss/stat.ML
      group: null
    AWS:status:
      url: https://status.aws.amazon.com/rss/all.rss
      period: .2
      https: true
      new: none
      sub:
        title:
          pattern: ^(?:Informational\ message|Service\ is\ operating\ normally):\ \[RESOLVED\]
          repl: '[RESOLVED]'
      format:
        re:
          id: /\#(?P<service>[^_]+)
        str:
          title: '[{service}] {title} | {summary}'
          url: '{id}'
    BioRxiv:
      url: https://connect.biorxiv.org/biorxiv_xml.php?subject=all
      alerts:
        read: false
      https: true
    Fb:Research:
      url: https://research.fb.com/publications/
      hext: |-
        <div>
            <a href:link><h3 @text:title/></a>
            <div class="areas-wrapper"><a href @text:category/></div>
        </div>
        <div><form class="download-form" action/></div>
      whitelist:
        category:
          - ^(?:Facebook\ AI\ Research|Machine\ Learning|Natural\ Language\ Processing\ \&\ Speech)$
    InfoWorld:
      url: https://www.infoworld.com/index.rss
    KDnuggets:
      url: https://us-east1-ml-feeds.cloudfunctions.net/kdnuggets
      new: some
    libraries.io/pypi/scikit-learn:
      url: https://libraries.io/pypi/scikit-learn/versions.atom
      new: none
      period: 8
      shorten: false
    r/MachineLearning:100+:
      url: https://www.reddit.com/r/MachineLearning/hot/.json?limit=50
      jmes: 'data.children[*].data | [?score >= `100`].{title: title, link: join(``, [`https://redd.it/`, id])}'
      shorten: false
    PwC:Trending:
      url: https://us-east1-ml-feeds.cloudfunctions.net/pwc/trending
      period: 0.5
      dedup: feed
    TalkRL:
      url: https://www.talkrl.com/feed
      period: 8
      message:
        title: false
        summary: true
    YT:3Blue1Brown: &YT
      url: https://www.youtube.com/feeds/videos.xml?channel_id=UCYO_jab_esuFRV4b17AJtAw
      period: 12
      shorten: false
      style:
        name:
          bg: red
          fg: white
          bold: true
      sub:
        url:
          pattern: ^https://www\.youtube\.com/watch\?v=(?P<id>.+?)$
          repl: https://youtu.be/\g<id>
    YT:AGI:
      url: https://www.youtube.com/results?search_query=%22artificial+general+intelligence%22&sp=CAISBBABGAI%253D
      hext: <a href:filter("/watch\?v=(.+)"):prepend("https://youtu.be/"):link href^="/watch?v=" title:title/>
      period: 12
      shorten: false
      blacklist:
        title:
          - \bWikipedia\ audio\ article\b
    YT:LexFridman:
      <<: *YT
      url: https://www.youtube.com/feeds/videos.xml?channel_id=UCSHZKyawb77ixDdsGog4iWA
      whitelist:
        title:
          - \bAGI\b
```

#### Global settings

##### Mandatory
* **`host`**: IRC server address.
* **`ssl_port`**: IRC server SSL port.
* **`nick`**: This is a registered IRC nick. If the nick is in use, it will be regained.

##### Optional
* **`alerts_channel`**: Some but not all warning and error alerts are sent to the this channel.
Its default value is `##{nick}-alerts`. The key `{nick}`, if present in the value, is formatted with the actual nick.
For example, if the nick is `MyFeed[bot]`, alerts will by default be sent to `##MyFeed[bot]-alerts`.
Since a channel name starts with #, the name if provided **must be quoted**.
It is recommended that the alerts channel be registered and monitored.
* **`mode`**: This can for example be `+igR` for [Freenode](https://freenode.net/kb/answer/usermodes).
Setting it is recommended.
* **`once`**: If `true`, each feed is queued only once. The default is `false`. This can be useful for testing purposes.

#### Feed-specific settings
A feed is defined under a channel as in the sample configuration. The feed's key represents its name.

The order of execution of the interacting operations is: `blacklist`, `whitelist`, `https`, `sub`, `format`, `shorten`.
Refer to the sample configuration for usage examples.

YAML [anchors and references](https://en.wikipedia.org/wiki/YAML#Advanced_components) can be used to reuse nodes.
Examples of this are in the sample.

##### Mandatory
* **`url`**: This is the URL of the feed.

##### Optional
These are optional and are independent of each other:
* **`alerts.empty`**: If `true`, an alert is sent if the feed has no entries. If `false`, such an alert is not sent.
Its default value is `true`.
* **`alerts.read`**: If `true`, an alert is sent if an error occurs three or more consecutive times when reading or 
processing the feed.
If `false`, such an alert is not sent.
Its default value is `true`.
* **`blacklist.category`**: This is an arbitrarily nested dictionary or list or their mix of regular expression patterns 
that result in an entry being skipped if a [search](https://docs.python.org/3/library/re.html#re.search) finds any of 
the patterns in any of the categories of the entry.
The nesting permits lists to be creatively reused between feeds via YAML anchors and references.
* **`blacklist.title`**: This is an arbitrarily nested dictionary or list or their mix of regular expression patterns 
that result in an entry being skipped if a [search](https://docs.python.org/3/library/re.html#re.search) finds any of 
the patterns in the title.
The nesting permits lists to be creatively reused between feeds via YAML anchors and references.
* **`blacklist.url`**: Similar to `blacklist.title`.
* **`dedup`**: This indicates how to deduplicate posts for the feed, thereby preventing them from being reposted.
The default value is `channel` (per-channel), and an alternate possible value is `feed` (per-feed per-channel).
* **`group`**: If a string, this delays the processing of a feed that has just been read until all other feeds having
the same group are also read.
This encourages multiple feeds having the same group to be be posted in succession, except if interrupted by
conversation.
It is however possible that unrelated feeds of any channel gets posted between ones having the same group.
To explicitly specify the absence of a group when using a YAML reference, the value can be specified as `null`.
It is recommended that feeds in the same group have the same `period`.
* **`https`**: If `true`, entry links that start with `http://` are changed to start with `https://` instead.
Its default value is `false`.
* **`message.summary`**: If `true`, the entry summary (description) is included in its message.
Its default value is `false`.
* **`message.title`**: If `false`, the entry title is not included in its message. Its default value is `true`.
* **`new`**: This indicates up to how many entries of a new feed to post.
A new feed is defined as one with no prior posts in its channel.
The default value is `some` which is interpreted as 3.
The default is intended to limit flooding a channel when one or more new feeds are added.
A string value of `none` is interpreted as 0 and will skip all entries for a new feed.
A value of `all` will skip no entries for a new feed; it is not recommended and should be used sparingly if at all.
In any case, future entries in the feed are not affected by this option on subsequent reads,
and they are all forwarded without a limit.
* **`period`**: This indicates how frequently to read the feed in hours on an average. Its default value is 1.
Conservative polling is recommended. Any value below 0.2 is changed to a minimum of 0.2.
Note that 0.2 hours is equal to 12 minutes.
To make service restarts safer by preventing excessive reads, the first read is delayed by half the period.
To better distribute the load of reading multiple feeds, a uniformly distributed random ±5% is applied to the period for
each read.
* **`shorten`**: This indicates whether to post shortened URLs for the feed.
The default value is `true`.
The alternative value `false` is recommended if the URL is naturally small, or if `sub` or `format` can be used to make
it small.
* **`style.name.bg`**: This is a string representing the name of a background color applied to the feed's name.
It can be one of: white, black, blue, green, red, brown, purple, orange, yellow, lime, teal, aqua, royal, pink, grey,
silver. The channel modes must allow formatting for this option to be effective.
* **`style.name.bold`**: If `true`, bold formatting is applied to the feed's name. Its default value is `false`.
The channel modes must allow formatting for this option to be effective.
* **`style.name.fg`**: Foreground color similar to `style.name.bg`.
* **`whitelist.category`**: This is an arbitrarily nested dictionary or list or their mix of regular expression patterns 
that result in an entry being skipped unless a [search](https://docs.python.org/3/library/re.html#re.search) finds any 
of the patterns in any of the categories of the entry.
The nesting permits lists to be creatively reused between feeds via YAML anchors and references.
* **`whitelist.explain`**: This applies only to `whitelist.title`.
It can be useful for understanding which portion of a post's title matched the whitelist.
If `true` and if a `style` is defined, the matching text of each posted title is italicized.
For example, "This is a _matching sample_ title".
If `true` and if a `style` is not defined, the matching text of each posted title is enclosed by asterisks.
For example, "This is a \*matching sample\* title".
The default value is `false`.
* **`whitelist.title`**: This is an arbitrarily nested dictionary or list or their mix of regular expression patterns 
that result in an entry being skipped unless a [search](https://docs.python.org/3/library/re.html#re.search) finds any 
of the patterns in the title.
The nesting permits lists to be creatively reused between feeds via YAML anchors and references.
* **`whitelist.url`**: Similar to `whitelist.title`.

##### Parser
For a non-XML feed, one of the following parsers can be used.
Each parsed entry must at a minimum include a `title`, a `link`, an optional `summary` (description),
and zero or more values for `category`.

Some sites require a custom user agent or other custom headers for successful scraping; such a customization can be
requested by creating an issue.
* **`hext`**: This is a string representing the [hext](https://hext.thomastrapp.com/documentation) DSL for parsing a
list of entry [dictionaries](https://en.wikipedia.org/wiki/Associative_array#Example) from a HTML web page. 
Before using, it can be tested in the form [here](https://hext.thomastrapp.com/).
* **`jmes`**: This is a string representing the [jmespath](http://jmespath.org/examples.html) DSL for parsing a list
of entry [dictionaries](https://en.wikipedia.org/wiki/Associative_array#Example) from JSON.
Before using, it can be tested in the form [here](http://jmespath.org/).
* **`pandas`**: This is a string command evaluated using [pandas](https://pandas.pydata.org/) for parsing a dataframe
of entries. The raw content is made available to the parser as a file-like object named `file`.
This parser uses [`eval`](https://docs.python.org/3/library/functions.html?#eval) which is unsafe, and so its
use must be confirmed to be safe.
The provisioned packages are `json`, `numpy` (as `np`), and `pandas` (as `pd`).
The value requires compatibility with the versions of `pandas` and `numpy` defined in 
[`requirements.txt`](requirements.txt), noting that these version requirements are expected to be routinely updated.


##### Conditional
The sample configuration above contains examples of these:
* **`format.re.title`**: This is a single regular expression pattern that is
[searched](https://docs.python.org/3/library/re.html#re.search) for in the title.
It is used to collect named [key-value pairs](https://docs.python.org/3/library/re.html#re.Match.groupdict) from the
match if there is one.
* **`format.re.url`**: Similar to `format.re.title`.
* **`format.str.title`**: The key-value pairs collected using `format.re.title` and `format.re.url`,
both of which are optional, are combined along with the default additions of `title`, `url`, and `categories` as keys.
Any additional keys returned by the parser are also available.
The key-value pairs are used to [format](https://docs.python.org/3/library/stdtypes.html#str.format_map) the provided
quoted title string.
If the title formatting fails for any reason, a warning is logged, and the title remains unchanged.
The default value is `{title}`.
* **`format.str.url`**: Similar to `format.str.title`. The default value is `{url}`.
If this is specified, it can sometimes be relevant to set `shorten` to `false` for the feed.
* **`sub.title.pattern`**: This is a single regular expression pattern that if found results in the entry
title being [substituted](https://docs.python.org/3/library/re.html#re.sub).
* **`sub.title.repl`**: If `sub.title.pattern` is found, the entry title is replaced with this replacement, otherwise it
is forwarded unchanged.
* **`sub.url.pattern`**: Similar to `sub.title.pattern`.
If a pattern is specified, it can sometimes be relevant to set `shorten` to `false` for the feed.
* **`sub.url.repl`**: Similar to `sub.title.repl`.

#### Feed default settings
A global default value can optionally be set under `defaults` for some feed-specific settings, 
namely `new` and `shorten`.
This value overrides its internal default.
It facilitates not having to set the same value individually for many feeds.

Refer to "Feed-specific settings" for the possible values and internal defaults of these settings.
Refer to the embedded sample configuration for a usage example.

Note that even if a default of `shorten: false` is set, the `BITLY_TOKENS` environment variable is still required.

### Deployment
* As a reminder, it is recommended that the alerts channel be registered and monitored.

* It is recommended that the bot be auto-voiced (+V) in each channel.
Failing this, messages from the bot risk being silently dropped by the server.
This is despite the bot-enforced limit of two seconds per message across the server.

* It is recommended that the bot be run as a Docker container using using Docker ≥18.09.2, possibly with
Docker Compose ≥1.24.0.
To run the bot using Docker Compose, create or add to a version-controlled `docker-compose.yml` file such as:
```yaml
version: '3.7'
services:
  irc-rss-feed-bot:
    container_name: irc-rss-feed-bot
    image: ascensive/irc-rss-feed-bot:latest
    restart: always
    logging:
      options:
        max-size: 2m
        max-file: "5"
    volumes:
      - ./irc-rss-feed-bot:/config
    env_file:
      - ./irc-rss-feed-bot/secrets.env
```

* In the above service definition in `docker-compose.yml`:
  * `image`: For better reproducibility, use a specific
  [versioned tag](https://hub.docker.com/r/ascensive/irc-rss-feed-bot/tags?ordering=last_updated), e.g. `0.9.1` instead of `latest`.
  * `volumes`: Customize the relative path to the previously created `config.yaml` file, e.g. `./irc-rss-feed-bot`.
  This volume source directory must be writable by the container using the UID defined in the Dockerfile; it is 999.
  A simple way to ensure it is writable is to run a command such as `chmod a+w ./irc-rss-feed-bot` once on the host.
  * `env_file`: Customize the relative path to `secrets.env`.

* From the directory containing `docker-compose.yml`, run `docker-compose up -d irc-rss-feed-bot`.
Use `docker logs -f irc-rss-feed-bot` to see and follow informational logs.

### Maintenance
* If `config.yaml` is updated, the container must be restarted to use the updated file.
* If `secrets.env` or the service definition in `docker-compose.yml` are updated, the container must be recreated
(and not merely restarted) to use the updated file.
* A `posts.v2.db` database file is written by the bot in the same directory as `config.yaml`.
This database file must be preserved with routine backups. After restoring a backup, before starting the container,
ensure the database file is writable by running a command such as `chmod a+w ./irc-rss-feed-bot/posts.v2.db`.
* The database file grows as new posts are made. For the most part this indefinite growth can be ignored.
Currently the standard approach for handling this, if necessary, is to stop the bot and delete the
database file if it has grown unacceptably large.
Restarting the bot after deleting the database will then create a new database file, and all configured feeds will be
handled as new.
This deletion is however discouraged as a routine measure.
