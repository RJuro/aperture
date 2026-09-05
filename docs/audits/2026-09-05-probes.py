"""Offline audit reproductions. Synthetic data; in-memory databases; no live LLM calls.

These assert the observed defects at revision 92ed796. They are diagnostic probes,
not desired-behavior regression tests; an assertion should change when its defect is fixed.
Run from the repository with: .venv/bin/python docs/audits/2026-09-05-probes.py
"""
import json, os, sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from app import db, store, ingest, llm, jobs, rerun
from app.engine import account, synth, check, read, verify

os.environ['APERTURE_PROVIDER'] = 'minimax'
results = {}

def setup():
    conn = db.connect(':memory:')
    pid = store.create_project(conn, 'Audit synthetic project', 'Work')
    raw = 'I worked at the bakery. We joined a union. My shift began at six. We voted for a strike. The shop closed on Sunday.'
    mid = store.add_material(conn, pid, 'Synthetic document A', raw)
    store.save_sentences(conn, mid, ingest.sentences(raw))
    tid = store.save_theme(conn, pid, tid=None, name='Work', gist='Paid work', code_ids=[])
    sents = store.sentences(conn, mid)
    store.save_moments(conn, mid, tid, [{'claim': text, 'anchor': text, 'sid': sid} for sid, text in sents[:4]])
    return conn, pid, mid, tid

with patch.object(llm, 'chat_json', side_effect=AssertionError('No real model calls allowed')):
    c,p,m,t = setup()
    fp = account.fingerprint(c,p,t)
    b = store.add_material(c,p,'Synthetic unread B','A second document.')
    cover = account.coverage(c,p,t)
    absent = [r for r in cover['per_material'] if not r['claims']]
    results['missing_follow_becomes_looked_for'] = 'LOOKED FOR AND TOO THIN' in account._absent_block(c,p,t,absent)
    results['account_fingerprint_ignores_added_material'] = fp == account.fingerprint(c,p,t)
    store.set_focus(c,p,'A different research question')
    results['account_fingerprint_ignores_focus'] = fp == account.fingerprint(c,p,t)
    first = store.thread(c,m,t)[0]
    store.mark_support(c, [(first['id'],'partly','Synthetic unsupported wording')])
    results['account_fingerprint_ignores_support_change'] = fp == account.fingerprint(c,p,t)

    captured=[]
    def account_answer(system,user,**kwargs):
        captured.append(system+'\n'+user)
        return {'account':'A synthetic account.'}
    fid = store.add_feedback(c,p,'theme',t,'note','AUDIT_NOTE_MUST_REACH_ACCOUNT')
    with patch.object(llm,'chat_json',side_effect=account_answer):
        jobs.run_now(c,p,rerun.plan(c,fid))
    results['theme_feedback_consumed_without_prompt'] = bool(rerun.feedback(c,fid)['consumed_by_run']) and not any('AUDIT_NOTE_MUST_REACH_ACCOUNT' in s for s in captured)

    c,p,m,t = setup()
    prior = [x['id'] for x in store.thread(c,m,t)]
    with patch.object(llm,'chat_json',return_value={'moments':[]}):
        out = synth.doc(c,m,only_theme=t)
    results['thin_rerun_preserves_old_live_claims'] = prior == [x['id'] for x in store.thread(c,m,t)] and not out['threads']
    results['thin_rerun_records_thin_with_old_live_claims'] = store.followed(c,p)[(t,m)] == 'thin' and bool(store.thread(c,m,t))

    c,p,m,t = setup()
    checked=[]
    def check_answer(system,user,**kwargs):
        checked.append(user)
        return {'found':[]}
    with patch.object(llm,'chat_json',side_effect=check_answer):
        out=check.run(c,p,'material',m,'Did they join a union?')
    results['check_omits_existing_answer_passage'] = out['verdict']=='not found' and not any('We joined a union.' in x for x in checked)
    results['check_search_count'] = out['searched_n']

    store.save_codes(c,p,m,[{'name':'Work','definition':'Paid work','sids':['S001']}])
    with patch.object(llm,'chat_json',side_effect=llm.LLMError('synthetic outage')):
        try: read.run(c,m)
        except llm.LLMError: pass
    results['failed_read_erases_old_hits'] = len(store.hits(c,m)) == 0

    c,p,m,t=setup()
    first=store.thread(c,m,t)[0]
    store.mark_support(c, [(first['id'],'partly','Synthetic qualification')])
    with patch.object(llm,'chat_json',return_value={'verdicts':[]}):
        verify.run(c,m)
    results['missing_verdict_clears_prior_warning'] = store.moment(c,first['id'])['support']==''

    store.set_hold(c,t,'candidate')
    results['candidate_without_codes_passes_gate'] = synth._marked_here(c,m,t)
    store.save_summary(c,'material',m,'reading','The synthetic participant describes employment.')
    captured=[]
    def project_answer(system,user,**kwargs):
        captured.append(user)
        return {'summary':'A synthetic summary.','interpretation':''}
    with patch.object(llm,'chat_json',side_effect=project_answer):
        synth.project(c,p)
    results['candidate_only_project_receives_no_claim_ids'] = not any(x['id'] in captured[0] for x in store.moments(c,m))

    try:
        carrying=[{'material_id':str(i),'title':str(i),'name':str(i),'kind':'document','claims':1} for i in range(151)]
        rows=[{'material_id':str(i),'id':str(i),'claim':'c','anchor':'a'} for i in range(151)]
        account._blocks(rows,carrying)
        results['account_151_materials'] = 'no error'
    except Exception as exc:
        results['account_151_materials'] = type(exc).__name__

print(json.dumps(results,indent=2))
assert all(v is True for k,v in results.items() if k not in ('check_search_count','account_151_materials'))
assert results['account_151_materials']=='ZeroDivisionError'
