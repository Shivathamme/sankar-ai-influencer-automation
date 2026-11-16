from pathlib import Path
import pandas as pd
import config, database as db
def export_local():
    out=Path('exports');out.mkdir(exist_ok=True)
    p=pd.DataFrame(db.people()); e=pd.DataFrame(db.emails()); a=pd.DataFrame(db.activity())
    x=out/'crm_export.xlsx'
    with pd.ExcelWriter(x,engine='openpyxl') as w:
        p.to_excel(w,sheet_name='Influencers',index=False);e.to_excel(w,sheet_name='Emails',index=False);a.to_excel(w,sheet_name='Activity',index=False)
    p.to_csv(out/'influencers.csv',index=False);e.to_csv(out/'emails.csv',index=False)
    return str(x)
def sync():
    if not config.GOOGLE_SHEET_ID:return 'Google Sheets not configured; local export is available.'
    try:
        import gspread
        gc=gspread.service_account(filename=config.GOOGLE_SERVICE_ACCOUNT_FILE);sh=gc.open_by_key(config.GOOGLE_SHEET_ID)
        for name,df in [('Influencers',pd.DataFrame(db.people())),('Emails',pd.DataFrame(db.emails()))]:
            try:ws=sh.worksheet(name)
            except gspread.WorksheetNotFound:ws=sh.add_worksheet(title=name,rows=1000,cols=25)
            ws.clear(); values=[list(df.columns)]+df.fillna('').astype(str).values.tolist() if len(df.columns) else [['No data']]
            ws.update(values=values,range_name='A1')
        return 'Google Sheets synced successfully.'
    except Exception as e:return f'Google Sheets sync error: {e}'
