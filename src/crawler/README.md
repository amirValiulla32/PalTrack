# Crawler

## Finding New Feeds

Enter `nix develop` mode and run:

``` python
$ python3
>>> from feedsearch_crawler import search
>>> feeds = search('url_of_site')
>>> feeds
```

Examine the returned URLs, and add them to `feeds.json`.
