/*
author: Rok Jaklič
date: 9. 8. 2013
company: Blocklogic
*/

-- START of bl_auth
-- must be run as superuser
-- on pos database
CREATE LANGUAGE plpythonu;

DROP FUNCTION bl_insert_user() CASCADE;
CREATE FUNCTION bl_insert_user() RETURNS TRIGGER AS $bl_insert_user_trigger$
    import json
    import psycopg2

    host = '127.0.0.1'
    dbname = 'users'
    in_user = 'users'
    password = 'users'
    source = 'pos'

    if TD['new']['type'] != "google":
        data = {source: {'username': TD['new']['username'], 'first_name': TD['new']['first_name'], 'last_name': TD['new']['last_name'], 'email': TD['new']['email'], 'password': TD['new']['password']}}

        conn = psycopg2.connect("host=" + host + " dbname=" + dbname + " user=" + in_user + " password=" + password)
        cursor = conn.cursor()

        cursor.execute("SELECT email, password, data FROM users WHERE email = %s", [TD['new']['email']])
        result = cursor.fetchone()

        if result is None:
            cursor.execute("INSERT INTO users(email, password, data, created_by, updated_by) VALUES (%s, %s, %s, %s, %s)", [TD['new']['email'], TD['new']['password'], json.dumps(data), source, source])

        conn.commit()

$bl_insert_user_trigger$ LANGUAGE plpythonu;

DROP FUNCTION bl_update_user() CASCADE;
CREATE FUNCTION bl_update_user() RETURNS TRIGGER AS $bl_update_user_trigger$
    import json
    import psycopg2

    host = '127.0.0.1'
    dbname = 'users'
    in_user = 'users'
    password = 'users'
    source = 'pos'

    if TD['new']['type'] != "google":
        data = {'username': TD['new']['username'], 'first_name': TD['new']['first_name'], 'last_name': TD['new']['last_name'], 'email': TD['new']['email'], 'password': TD['new']['password']}

        conn = psycopg2.connect("host=" + host + " dbname=" + dbname + " user=" + in_user + " password=" + password)
        cursor = conn.cursor()

        cursor.execute("SELECT email, password, data FROM users WHERE email = %s", [TD['new']['email']])
        result = cursor.fetchone()

        if result and len(result) > 0:
            tmp_data = json.loads(result[2])
            if len(tmp_data) > 0 and source in tmp_data:
                for k, v in tmp_data[source].items():
                    if k not in data:
                        data[k] = v

                tmp_data[source] = data

            if len(tmp_data) > 0 and source not in tmp_data:
                tmp_data[source] = data

            cursor.execute("UPDATE users SET password = %s, data = %s WHERE email = %s", [TD['new']['password'], json.dumps(data), TD['new']['email']])

        conn.commit()

$bl_update_user_trigger$ LANGUAGE plpythonu;

DROP FUNCTION bl_update_mail_user_password(in_email character varying, password character varying) CASCADE;
CREATE FUNCTION bl_update_mail_user_password(in_email character varying, password character varying) RETURNS boolean AS $bl_update_mail_user_password_function$
    import psycopg2

    host = '127.0.0.1'
    dbname = 'mail'
    dbuser = 'vmail'
    dbpassword = 'dMbXlDZQ'
    port = '5432'
    source = 'pos'

    conn = psycopg2.connect("host=" + host + " port=" + port + " dbname=" + dbname + " user=" + dbuser + " password=" + dbpassword)
    cursor = conn.cursor()

    email = in_email.split("@")

    if len(email) < 2:
        return

    cursor.execute("SELECT username, domain FROM mailbox WHERE username = %s AND domain = %s", [email[0], email[1]])
    result = cursor.fetchone()

    if result and len(result) > 0:
        cursor.execute("UPDATE mailbox SET password = MD5(%s), datetime_updated = NOW() WHERE username = %s AND domain = %s", [password, email[0], email[1]])

    conn.commit()

$bl_update_mail_user_password_function$ LANGUAGE plpythonu;

DROP TRIGGER auth_bl_user_insert ON blusers_blocklogicuser CASCADE;
CREATE TRIGGER auth_bl_user_insert
    AFTER INSERT ON blusers_blocklogicuser
    FOR EACH ROW
    EXECUTE PROCEDURE bl_insert_user();

DROP TRIGGER auth_bl_user_update ON blusers_blocklogicuser CASCADE;
CREATE TRIGGER auth_bl_user_update
    AFTER UPDATE ON blusers_blocklogicuser
    FOR EACH ROW
    EXECUTE PROCEDURE bl_update_user();
--- END of bl_auth

--- This is used to insert deleted data into "history"
DROP FUNCTION insert_deleted() CASCADE;
CREATE FUNCTION insert_deleted() RETURNS TRIGGER AS $insert_deleted_trigger$
    import json

    plan = plpy.prepare("INSERT INTO deleted_data(table_name, data) VALUES ($1,  $2)", ["text", "text"])
    plpy.execute(plan, [TD['table_name'], json.dumps(TD)])

$insert_deleted_trigger$ LANGUAGE plpythonu;

DROP TRIGGER group_group_deleted ON group_group CASCADE;
CREATE TRIGGER group_group_deleted
    AFTER DELETE ON group_group
    FOR EACH ROW
    EXECUTE PROCEDURE insert_deleted();

DROP TRIGGER tasks_task_deleted ON group_group CASCADE;
CREATE TRIGGER tasks_task_deleted
    AFTER DELETE ON tasks_task
    FOR EACH ROW
    EXECUTE PROCEDURE insert_deleted();

DROP TRIGGER blusers_userprofile_deleted ON group_group CASCADE;
CREATE TRIGGER blusers_userprofile
    AFTER DELETE ON tasks_task
    FOR EACH ROW
    EXECUTE PROCEDURE insert_deleted();
--- end of insert_deleted

-- can be run as pos user
CREATE SEQUENCE deleted_data_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

DROP TABLE deleted_data;

CREATE TABLE deleted_data (
	id INTEGER NOT NULL PRIMARY KEY DEFAULT nextval('deleted_data_id_seq'),
	table_name VARCHAR(50) NOT NULL,
	data TEXT NOT NULL,
	datetime_created TIMESTAMP WITH TIME ZONE
);

ALTER TABLE deleted_data OWNER TO pos;
ALTER SEQUENCE deleted_data_id_seq OWNER TO pos;

-- test queris
-- DELETE FROM blusers_blocklogicuser WHERE id = 2;
-- DELETE FROM blusers_blocklogicuser;
-- SELECT * FROM blusers_blocklogicuser;
-- INSERT INTO blusers_blocklogicuser(id, username, first_name, last_name, email, password, is_staff, is_active, is_superuser, last_login, date_joined, datetime_created, datetime_updated) VALUES (2, 'rjaklic', 'Rok', 'Jaklic', 'rjaklic@gmail.com', 'rok123', false, false, false, NOW(), NOW(), NOW(), NOW());
-- UPDATE blusers_blocklogicuser SET password = 'DADAAD' WHERE email = 'rok@blocklogic.net';
