#!/usr/bin/env python3
"""Resolve a title against the Crossref registry and print the best match."""
import json
import sys
import urllib.parse
import urllib.request


def search(title, rows=3):
    url = ('https://api.crossref.org/works?query.bibliographic='
           + urllib.parse.quote(title) + f'&rows={rows}')
    req = urllib.request.Request(
        url, headers={'User-Agent': 'reference-verification/1.0 (mailto:author@example.org)'})
    with urllib.request.urlopen(req, timeout=40) as r:
        return json.load(r)['message']['items']


for title in sys.argv[1:]:
    print('=' * 78)
    print('QUERY:', title)
    for it in search(title):
        t = it.get('title', [''])[0]
        yr = ''
        for k in ('published-print', 'published', 'issued'):
            if it.get(k, {}).get('date-parts'):
                yr = it[k]['date-parts'][0][0]
                break
        au = '; '.join(a.get('family', '') for a in it.get('author', [])[:4])
        ven = (it.get('container-title') or [''])[0]
        print(f"  doi={it.get('DOI')}")
        print(f"    {t}")
        print(f"    {au} | {yr} | {ven} | p.{it.get('page')}")
    print()
