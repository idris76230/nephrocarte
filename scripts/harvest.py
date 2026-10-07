import json, urllib.request, urllib.parse, sys, os
out = sys.argv[1]
COND = ('kidney OR renal OR nephropathy OR nephritis OR glomerulonephritis OR glomerulopathy OR glomerulosclerosis '
        'OR "nephrotic syndrome" OR dialysis OR hemodialysis OR "peritoneal dialysis" OR nephrology OR uremic '
        'OR "IgA nephropathy" OR "lupus nephritis" OR "ANCA" OR "hemolytic uremic syndrome" OR "C3 glomerulopathy" '
        'OR "polycystic kidney" OR Alport OR Fabry OR cystinosis OR "membranous nephropathy" OR FSGS OR nephrolithiasis '
        'OR "kidney stones" OR hyperoxaluria OR "end stage renal disease" OR "kidney failure" OR hyperkalemia')
STAT = 'RECRUITING,NOT_YET_RECRUITING,ENROLLING_BY_INVITATION,ACTIVE_NOT_RECRUITING'
allst = {}
for country in ('France', 'Belgium'):
    tok = None; n = 0
    while True:
        q = {'query.cond': COND, 'query.locn': country, 'filter.overallStatus': STAT,
             'pageSize': 1000, 'countTotal': 'true', 'format': 'json'}
        if tok: q['pageToken'] = tok
        url = 'https://clinicaltrials.gov/api/v2/studies?' + urllib.parse.urlencode(q)
        d = json.load(urllib.request.urlopen(url, timeout=120))
        if not tok: print(country, 'total', d.get('totalCount'))
        for s in d['studies']:
            allst[s['protocolSection']['identificationModule']['nctId']] = s; n += 1
        tok = d.get('nextPageToken')
        if not tok: break
    print(country, 'fetched', n)
json.dump(allst, open(out, 'w'))
print('unique', len(allst))
