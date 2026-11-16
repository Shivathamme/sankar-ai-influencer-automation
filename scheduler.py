"""Run as a separate long-lived process: python scheduler.py"""
import time, logging
import config,database as db,workflow
logging.basicConfig(level=logging.INFO,format='%(asctime)s %(levelname)s %(message)s')
def main():
    db.init();logging.info('Scheduler started; poll interval=%s seconds',config.SCHEDULER_POLL_SECONDS)
    while True:
        try:
            f=workflow.run_followups();logging.info('Inbox + follow-up scan: %s',f)
        except Exception as e:logging.exception('Scheduled run failed safely: %s',e)
        time.sleep(config.SCHEDULER_POLL_SECONDS)
if __name__=='__main__':main()
