import streamlit as st, pandas as pd
import config,database as db,research,workflow,sheets_service
from campaign_store import load_campaign,save_campaign
from ai_service import AIError
from gmail_service import GmailError
st.set_page_config(page_title='Sankar | Influencer Outreach',page_icon='📣',layout='wide')
db.init()
st.title('📣 AI-Powered Influencer Research & Email Outreach')
st.caption('Sankar Group · AI Automation Internship Assignment')
if config.DEMO_MODE:st.info('DEMO MODE: emails are simulated; no external email is sent. AI responses are simulated if the selected provider key is not configured.')
else:st.warning('LIVE MODE: Gmail actions can send real emails. TEST_RECIPIENT is strongly recommended during validation.')
with st.sidebar:
    st.subheader('Campaign configuration')
    camp=load_campaign()
    brand=st.text_input('Brand name',camp['brand_name'])
    desc=st.text_area('Brand description',camp['brand_description'])
    offer=st.text_area('Collaboration offer',camp['offer'])
    niche_cfg=st.text_input('Target niche',camp['niche'])
    location_cfg=st.text_input('Target location',camp['location'])
    keywords_cfg=st.text_input('Campaign keywords',camp['keywords'])
    sender_cfg=st.text_input('Sender display name',camp['sender'])
    if st.button('Save campaign settings'):
        save_campaign({'brand_name':brand,'brand_description':desc,'offer':offer,'niche':niche_cfg,'location':location_cfg,'keywords':keywords_cfg,'sender':sender_cfg})
        st.success('Campaign settings saved.')
    st.metric('Leads in CRM',len(db.people()));st.metric('Emails sent today',db.count_sent_today())
tabs=st.tabs(['1 Research','2 AI Filter','3 CRM / Sheets','4 Email Outreach','5 Follow-ups','6 Replies','7 Export / Demo'])
with tabs[0]:
    st.subheader('Discover public Instagram profiles')
    c1,c2,c3=st.columns(3);niche=c1.text_input('Niche','fitness');location=c2.text_input('Location','India');keywords=c3.text_input('Keywords','fitness, wellness, creator')
    c4,c5,c6=st.columns(3);mn=c4.number_input('Minimum followers',0,100000000,1000);mx=c5.number_input('Maximum followers',0,100000000,1000000);lim=c6.number_input('Maximum profiles',1,50,15)
    enrich_emails=st.checkbox('Also search public web pages for published business emails (extra search requests)',value=False)
    if st.button('🔎 Search public profiles',type='primary'):
        try:
            with st.spinner('Searching public web index...'):st.session_state['candidates']=research.search(niche,location,keywords,int(mn),int(mx),int(lim),enrich_emails)
        except Exception as e:st.error(str(e))
    if st.button('Load synthetic demo records'):st.session_state['candidates']=research.demo_data()
    uploaded=st.file_uploader('Import your own verified CSV',type=['csv'])
    if uploaded and st.button('Import CSV'):
        try:st.session_state['candidates']=pd.read_csv(uploaded).fillna('').to_dict('records')
        except Exception as e:st.error(str(e))
    cands=st.session_state.get('candidates',[])
    if cands:
        st.dataframe(pd.DataFrame(cands),use_container_width=True)
        if st.button('Save candidates to CRM (duplicates skipped)'):
            new=dup=0
            for p in cands:
                _,created=db.upsert_person(p);new+=created;dup+=not created
            st.success(f'Saved {new}; skipped {dup} duplicates.');st.session_state.pop('candidates',None)
with tabs[1]:
    st.write('The selected AI provider analyses profile facts, assigns a suitability score and prioritises qualified prospects.')
    st.caption(f'Provider: {config.AI_PROVIDER}. Groq requires GROQ_API_KEY; Claude requires ANTHROPIC_API_KEY. Offline demo responses are labelled as simulated. The assignment specifically names Claude; use Groq only if your coordinator accepts the alternative.')
    if st.button('Run AI filtering',type='primary'):
        try:st.success(workflow.run_analysis())
        except Exception as e:st.error(str(e))
    ps=db.people();st.dataframe(pd.DataFrame(ps)[[c for c in ['username','niche','followers','location','score','relevant','category','summary','reason'] if c in (ps[0] if ps else {})]] if ps else pd.DataFrame(),use_container_width=True)
with tabs[2]:
    st.subheader('Lead pipeline')
    status=st.selectbox('Filter status',['All']+db.STATUSES);ps=db.people(status)
    if ps:st.dataframe(pd.DataFrame(ps),use_container_width=True)
    if ps:
        chosen=st.selectbox('Select lead',ps,format_func=lambda p:f"@{p['username']} · {p['status']}")
        new_status=st.selectbox('Update status',db.STATUSES,index=db.STATUSES.index(chosen['status']) if chosen['status'] in db.STATUSES else 0)
        if st.button('Update CRM status'):db.update_person(chosen['id'],status=new_status);db.log(chosen['id'],'manual_status_update',new_status);st.rerun()
    if st.button('Sync CRM to Google Sheets'):
        st.info(sheets_service.sync())
with tabs[3]:
    st.subheader('Personalised outreach · human approval required')
    if st.button('Generate initial email drafts'):
        try:st.success(f"Created {workflow.create_initial_drafts()} drafts.")
        except Exception as e:st.error(str(e))
    drafts=db.emails(direction='out',kind='initial',status='draft')
    for e in drafts:
        p=db.person(e['influencer_id'])
        with st.expander(f"@{p['username']} · {e['subject']}"):
            subject=st.text_input('Subject',e['subject'],key=f'sub{e["id"]}');body=st.text_area('Email body',e['body'],height=220,key=f'body{e["id"]}')
            if st.button('Save edits',key=f'save{e["id"]}'):
                db.update_email(e['id'],subject=subject,body=body);st.success('Saved')
            if st.button('Approve and send',key=f'send{e["id"]}',type='primary'):
                try:db.update_email(e['id'],subject=subject,body=body);st.success(workflow.approve_and_send(e['id']));st.rerun()
                except Exception as ex:st.error(str(ex))
    st.caption(f"Daily send limit: {config.DAILY_SEND_LIMIT}. Test recipient override: {'configured' if config.TEST_RECIPIENT else 'not configured'}.")
with tabs[4]:
    st.subheader('Scheduled follow-ups')
    st.write(f'First follow-up after {config.FOLLOWUP1_DAYS} days; second after another {config.FOLLOWUP2_DAYS} days.')
    st.write('Run `python scheduler.py` in a separate terminal to check replies and process due follow-ups automatically.')
    if st.button('Run follow-up check now'):
        try:st.success(workflow.run_followups())
        except Exception as e:st.error(f'Follow-up run stopped safely: {e}')
    fs=[e for e in db.emails(direction='out') if e['kind'] in ('followup1','followup2')]
    if fs:
        st.dataframe(pd.DataFrame(fs),use_container_width=True)
        for draft in [x for x in fs if x['status']=='draft']:
            person=db.person(draft['influencer_id'])
            with st.expander(f"Follow-up approval · @{person['username']} · {draft['kind']}"):
                st.write(draft['subject']);st.text_area('Follow-up body',draft['body'],key=f"fubody{draft['id']}")
                if st.button('Approve and send follow-up',key=f"fusend{draft['id']}"):
                    try:st.success(workflow.approve_and_send(draft['id']));st.rerun()
                    except Exception as ex:st.error(str(ex))
with tabs[5]:
    st.subheader('Inbox reply management')
    if st.button('Check Gmail for replies'):
        try:st.success(workflow.process_incoming())
        except Exception as e:st.error(str(e))
    ps=db.people();sent=[p for p in ps if db.emails(i=p['id'],direction='out',status='sent')]
    if config.DEMO_MODE and sent:
        with st.expander('Demo: simulate a reply'):
            who=st.selectbox('Influencer',sent,format_func=lambda p:'@'+p['username']);txt=st.text_area('Reply text','Sounds interesting. Could you share the budget and deliverables?')
            if st.button('Classify demo reply'):
                try:st.json(workflow.simulate_reply(who['id'],txt));st.rerun()
                except Exception as e:st.error(str(e))
    incoming=db.emails(direction='in')
    for e in incoming:
        p=db.person(e['influencer_id'])
        with st.expander(f"@{p['username']} · {e.get('classification') or 'unprocessed'}"):
            st.write(e['body']);st.write(e.get('summary',''));st.write(e.get('next_action',''))
    replies=db.emails(direction='out',kind='reply',status='draft')
    for e in replies:
        with st.expander('Reply draft · '+e['subject']):
            st.write(e['body'])
            if st.button('Approve and send reply',key=f'reply{e["id"]}'):
                try:st.success(workflow.approve_and_send(e['id']));st.rerun()
                except Exception as ex:st.error(str(ex))
with tabs[6]:
    st.subheader('Exports and assignment demo')
    if st.button('Export Excel / CSV'):
        try:st.success(sheets_service.export_local())
        except Exception as e:st.error(str(e))
    st.write('Activity log');st.dataframe(pd.DataFrame(db.activity()),use_container_width=True)
    st.markdown('**Suggested screen recording:** Research → save leads → AI filter → CRM → generate/edit/approve initial email → send to test mailbox → simulate or receive reply → classify → approve reply → show follow-up scheduler → export CRM.')
