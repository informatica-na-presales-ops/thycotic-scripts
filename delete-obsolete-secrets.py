import apscheduler.schedulers.blocking
import notch
import os
import psycopg2.extras
import signal
import sys
import thysecser

log = notch.make_log('delete-obsolete-secrets')


def get_obsolete_secrets() -> list:
    cnx = psycopg2.connect(os.getenv('DB'), cursor_factory=psycopg2.extras.DictCursor)
    with cnx:
        with cnx.cursor() as cur:
            sql = '''
                select s.thycotic_secret_id, s.cloud, s.machine_id
                from machine_creds_in_thycotic s
                left join cloud_vm_ownership m on m.machine_id = s.machine_id
                where m.machine_id is null
            '''
            cur.execute(sql)
            data = cur.fetchall()
    cnx.close()
    return data


def main_job():
    obsolete_secrets = get_obsolete_secrets()
    log.info(f'Found {len(obsolete_secrets)} obsolete secrets')

    ssc = thysecser.SecretServerClient()
    for row in obsolete_secrets:
        secret_id = row.get('thycotic_secret_id')
        cloud = row.get('cloud')
        machine_id = row.get('machine_id')
        log.info(f'Removing {secret_id} ({cloud}.{machine_id})')
        ssc.delete_secret(secret_id)


def main():
    repeat = os.getenv('REPEAT', 'false').lower() in ('1', 'on', 'true', 'yes')
    if repeat:
        repeat_interval_minutes = int(os.getenv('REPEAT_INTERVAL_MINUTES', 15))
        log.info(f'This job will repeat every {repeat_interval_minutes} minutes')
        log.info('Change this value by setting the REPEAT_INTERVAL_MINUTES environment variable')
        scheduler = apscheduler.schedulers.blocking.BlockingScheduler()
        scheduler.add_job(main_job, 'interval', minutes=repeat_interval_minutes)
        scheduler.add_job(main_job)
        scheduler.start()
    else:
        main_job()


def handle_sigterm(_signal, _frame):
    sys.exit()


if __name__ == '__main__':
    signal.signal(signal.SIGTERM, handle_sigterm)
    main()
