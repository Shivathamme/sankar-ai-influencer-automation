"""Small CLI helpers for local smoke testing."""
import database as db,research,workflow,sheets_service

def demo():
    db.init()
    for p in research.demo_data():db.upsert_person(p)
    print('Analysis:',workflow.run_analysis())
    print('Initial drafts created:',workflow.create_initial_drafts())
    print('Drafts are intentionally left for human approval in the Streamlit UI.')
    print('CRM export:',sheets_service.export_local())
if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('command',choices=['demo','export']);a=p.parse_args();db.init()
    if a.command=='demo':demo()
    else:print(sheets_service.export_local())
