import apscheduler.schedulers.blocking
import notch
import os
import psycopg2.extras
import signal
import sys
import thysecser

log = notch.make_log('list-secrets-to-data-lake')


def main_job():
    cnx = psycopg2.connect(os.getenv('DB'), cursor_factory=psycopg2.extras.DictCursor)
    c = thysecser.SecretServerClient()

    records = []

    windows_secrets = c.get_secrets({
        'filter.folderId': os.getenv('SECRET_SERVER_FOLDER_ID_WINDOWS'),
        'take': 100,
    })

    for secret in windows_secrets:
        cloud, machine_id = secret.get('name').split('.', maxsplit=1)
        records.append({
            'cloud': cloud,
            'machine_id': machine_id,
            'thycotic_secret_id': secret.get('id'),
            'thycotic_folder_id': os.getenv('SECRET_FOLDER_ID_WINDOWS'),
        })

    linux_secrets = c.get_secrets({
        'filter.folderId': os.getenv('SECRET_SERVER_FOLDER_ID_LINUX'),
        'take': 100,
    })

    for secret in linux_secrets:
        cloud, machine_id = secret.get('name').split('.', maxsplit=1)
        records.append({
            'cloud': cloud,
            'machine_id': machine_id,
            'thycotic_secret_id': secret.get('id'),
            'thycotic_folder_id': os.getenv('SECRET_FOLDER_ID_LINUX'),
        })

    log.info(f'Found {len(records)} secrets in Thycotic')

    with cnx:
        with cnx.cursor() as cur:
            cur.execute('update machine_creds_in_thycotic set synced = false where synced is true')
            sql = '''
                insert into machine_creds_in_thycotic (
                    cloud, machine_id, thycotic_secret_id, thycotic_folder_id, synced
                ) values (
                    %(cloud)s, %(machine_id)s, %(thycotic_secret_id)s, %(thycotic_folder_id)s, true
                ) on conflict (machine_id) do update set
                    cloud = %(cloud)s, thycotic_secret_id = %(thycotic_secret_id)s,
                    thycotic_folder_id = %(thycotic_folder_id)s, synced = true
            '''
            psycopg2.extras.execute_batch(cur, sql, records)
            cur.execute('delete from machine_creds_in_thycotic where synced is false')

    cnx.close()


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
