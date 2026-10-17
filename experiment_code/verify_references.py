#!/usr/bin/env python3
"""Verify every reference in references.bib against an authoritative registry.

Three failure modes motivated this script, all of which are invisible when
reading the .bib file by eye:

  1. A DOI that resolves to a *different* paper than the entry describes.
  2. A title that looks entirely plausible but was never published.
  3. A real paper with a truncated or mistyped DOI, so the link is dead.

Registries used, in order of authority:
  * doi.org            -> liveness of the identifier itself
  * Crossref API       -> metadata for most scholarly DOIs
  * DataCite API       -> metadata for repository DOIs (Zenodo, figshare, ...)
  * arXiv API          -> preprints, bare or as 10.48550/arXiv.*
  * OpenAlex           -> venues Crossref does not index (e.g. JMLR)

Books and misc entries carry no resolvable identifier and are reported as
such rather than guessed at.

Usage:  python3 verify_references.py [path/to/references.bib]
Exit code 0 = every entry verified, 1 = at least one entry needs attention.
"""
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

BIB = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1] / 'references.bib'
UA = {'User-Agent': 'reference-verification/1.0 (mailto:author@example.org)'}
NON_CROSSREF_PREFIXES = ('10.5281', '10.48550', '10.6084', '10.5281')


def parse_entries(text):
    """Return [(key, {field: value})] for every entry in the bib file."""
    out = []
    for m in re.finditer(r'@(\w+)\s*\{\s*([^,\s]+)\s*,(.*?)\n\}', text, re.S):
        key, body, etype = m.group(2), m.group(3), m.group(1).lower()
        fields = {'__type__': etype}
        for fm in re.finditer(r'(\w+)\s*=\s*\{', body):
            name = fm.group(1).lower()
            start, depth, i = fm.end(), 1, fm.end()
            while i < len(body) and depth:
                if body[i] == '{':
                    depth += 1
                elif body[i] == '}':
                    depth -= 1
                i += 1
            fields[name] = body[start:i - 1]
        out.append((key, fields))
    return out


def norm(s):
    s = re.sub(r'[{}\\]', '', s or '')
    s = re.sub(r'[^a-z0-9 ]', ' ', s.lower())
    return ' '.join(s.split())


def strip_paren(s):
    return re.sub(r'\(.*?\)', ' ', s)


def get(url, timeout=40, head=False):
    req = urllib.request.Request(url, headers=UA)
    if head:
        req.get_method = lambda: 'HEAD'
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, r.read().decode('utf-8', 'replace')


def doi_alive(doi):
    """True if doi.org resolves the identifier, False if it 404s, None if unknown.

    Uses curl rather than urllib because urllib follows the 302 redirect to the
    publisher, where Cloudflare answers 403 and every live DOI would look dead.
    """
    import shutil
    import subprocess
    if not shutil.which('curl'):
        return None
    try:
        out = subprocess.run(
            ['curl', '-s', '-o', '/dev/null', '-w', '%{http_code}',
             '-m', '25', '--max-redirs', '0', f'https://doi.org/{doi}'],
            capture_output=True, text=True, timeout=40).stdout.strip()
    except Exception:                                           # noqa: BLE001
        return None
    if not out.isdigit():
        return None
    return int(out) < 400


def crossref(doi):
    m = json.loads(get('https://api.crossref.org/works/' + urllib.parse.quote(doi))[1])['message']
    year = None
    for k in ('published-print', 'published', 'issued', 'published-online'):
        dp = m.get(k, {}).get('date-parts')
        if dp and dp[0] and dp[0][0]:
            year = str(dp[0][0])
            break
    return {'title': (m.get('title') or [''])[0], 'year': year, 'source': 'crossref'}


def datacite(doi):
    body = get('https://api.datacite.org/dois/' + urllib.parse.quote(doi))[1]
    a = json.loads(body)['data']['attributes']
    return {'title': (a.get('titles') or [{}])[0].get('title', ''),
            'year': a.get('publicationYear'), 'source': 'DataCite'}


def arxiv_record(aid):
    """Return {'title':..., 'year':...} for an arXiv id, or None."""
    xml = get('http://export.arxiv.org/api/query?id_list=' + aid)[1]
    m = re.search(r'<entry>.*?<title>(.*?)</title>', xml, re.S)
    if not m:
        return None
    d = re.search(r'<published>(\d{4})', xml)
    return {'title': ' '.join(m.group(1).split()), 'year': d.group(1) if d else None}


def openalex_search(title):
    """OpenAlex indexes venues Crossref does not (JMLR, ICLR, ...)."""
    url = ('https://api.openalex.org/works?search='
           + urllib.parse.quote(title) + '&per-page=5')
    req = urllib.request.Request(url, headers=UA)
    items = json.loads(urllib.request.urlopen(req, timeout=40).read().decode())['results']
    want = norm(strip_paren(title))
    best, best_score = None, 0.0
    for w in items:
        cr = norm(w.get('title') or '')
        if not cr:
            continue
        score = len(set(cr.split()) & set(want.split())) / max(1, len(set(want.split())))
        if score > best_score:
            best, best_score = w, score
    return best if best_score >= 0.75 else None


def titles_agree(a, b):
    short, long_ = sorted([norm(a), norm(b)], key=len)
    return bool(short) and short in long_


def check(key, fields):
    """Return (verdict, identifier, detail)."""
    etype = fields.get('__type__', '')
    doi = fields.get('doi', '').strip()
    aid = None
    m = re.search(r'arXiv[:\s/]*(\d{4}\.\d{4,5})',
                  fields.get('note', '') + ' ' + fields.get('eprint', '') + ' ' + doi)
    if m:
        aid = m.group(1)
    elif re.fullmatch(r'\d{4}\.\d{4,5}', fields.get('eprint', '').strip()):
        aid = fields['eprint'].strip()          # bare id, e.g. eprint={1711.00740}
    if not aid and doi.startswith('10.48550/arXiv.'):
        m = re.search(r'(\d{4}\.\d{4,5})', doi)
        aid = m.group(1) if m else None

    # ---- arXiv path -------------------------------------------------------
    if aid:
        ident = f'arXiv:{aid}'
        try:
            rec = arxiv_record(aid)
        except Exception as e:                                   # noqa: BLE001
            return ('FETCH-ERROR', ident, str(e)[:50])
        if not rec:
            return ('FAIL (not on arXiv)', ident, '')
        if not titles_agree(rec['title'], fields.get('title', '')):
            return ('FAIL (title)', ident, f"arXiv: {rec['title'][:50]!r}")
        by = fields.get('year', '')
        if by and rec['year'] and by != rec['year']:
            # a preprint year legitimately differs from the venue year
            if abs(int(by) - int(rec['year'])) <= 2:
                return ('PASS', ident, f"arXiv {rec['year']} preprint, bib {by} (venue year)")
            return ('CHECK (year)', ident, f"arXiv {rec['year']} vs bib {by}")
        return ('PASS', ident, f"arXiv: {rec['title'][:50]!r}")

    # ---- DOI path ---------------------------------------------------------
    if doi:
        rec, err = None, None
        for label, fn in (('crossref', crossref), ('datacite', datacite)):
            try:
                rec = fn(doi)
                break
            except urllib.error.HTTPError as e:
                if e.code != 404:
                    err = f'{label} HTTP {e.code}'
            except Exception as e:                               # noqa: BLE001
                err = str(e)[:40]
        if rec is None:
            # Neither registry knows this DOI. It is either dead or registered
            # somewhere neither covers; only doi.org can tell us which.
            if err:
                return ('FETCH-ERROR', doi, err)
            alive = doi_alive(doi)
            if alive is False:
                return ('FAIL (dead DOI)', doi, 'not in Crossref/DataCite, doi.org 404')
            if alive is None:
                return ('CHECK (unverified)', doi, 'no registry record; liveness unknown')
            return ('PASS (resolves)', doi, 'live DOI; no Crossref/DataCite record')
        if not titles_agree(rec.get('title', ''), fields.get('title', '')):
            return ('FAIL (title)', doi, f"{rec['source']}: {rec.get('title','')[:50]!r}")
        by, ry = fields.get('year', ''), str(rec.get('year') or '')
        if by and ry and by != ry:
            if abs(int(by) - int(ry)) <= 2:
                return ('PASS', doi, f"{rec['source']} year {ry} vs bib {by}")
            return ('CHECK (year)', doi, f"{rec['source']} year {ry} vs bib {by}")
        return ('PASS', doi, f"{rec['source']}: {norm(rec.get('title',''))[:50]!r}")

    # ---- no identifier ----------------------------------------------------
    if etype in ('book', 'misc', 'manual', 'techreport', 'unpublished'):
        return ('NO-ID (book/misc)', '', 'no resolvable identifier; not registry-checked')
    title = strip_paren(fields.get('title', '')).strip()
    if not title:
        return ('NO-ID', '', 'no title')
    try:
        rec = openalex_search(title)
    except Exception as e:                                       # noqa: BLE001
        return ('FETCH-ERROR', '', str(e)[:50])
    if not rec:
        return ('CHECK (unverified)', '', 'no registry match for this title')
    cr = rec.get('title') or ''
    ident = (rec.get('doi') or '').replace('https://doi.org/', '')
    if titles_agree(cr, title):
        yrs = [str(rec.get('publication_year'))] if rec.get('publication_year') else []
        if fields.get('year') and yrs and fields['year'] not in yrs:
            return ('CHECK (year)', ident, f"openalex {yrs} vs bib {fields['year']}")
        return ('PASS (by title)', ident, f"openalex: {norm(cr)[:50]!r}")
    return ('CHECK (unverified)', ident, f"closest: {norm(cr)[:50]!r}")


def main():
    entries = parse_entries(BIB.read_text())
    rows = []
    for key, f in entries:
        verdict, ident, detail = check(key, f)
        rows.append((key, ident, verdict, detail))
        time.sleep(0.15)                       # be polite to the APIs

    width = max(len(r[0]) for r in rows) + 1
    print(f'{"entry":{width}} {"verdict":20} {"identifier":30} detail')
    print('-' * 118)
    for key, ident, verdict, detail in rows:
        print(f'{key:{width}} {verdict:20} {ident:30} {detail}')
    bad = [r for r in rows if not r[2].startswith(('PASS', 'NO-ID'))]
    print(f'\n{len(rows) - len(bad)}/{len(rows)} verified or unverifiable-by-design; '
          f'{len(bad)} need attention')
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
