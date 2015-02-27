/*
author: Rok Jaklič
date: 4. 12. 2014
company: Blocklogic
*/

-- must be run as superuser
-- on pos database
CREATE LANGUAGE plpythonu;

DROP FUNCTION bl_insert_user(email CHARACTER VARYING) CASCADE;
DROP FUNCTION bl_update_user(email CHARACTER VARYING) CASCADE;

CREATE OR REPLACE FUNCTION bl_insert_user(email CHARACTER VARYING, source CHARACTER VARYING) RETURNS VOID AS $bl_insert_user_function$
    import json
    import psycopg2

    host = '10.0.0.35'
    dbname = 'users'
    in_user = 'users'
    password = 'iQeeLEsw'

    plan = plpy.prepare("SELECT username, password, first_name, last_name, email, sex, country, type FROM blusers_blocklogicuser WHERE email = $1", ["text"])
    result1 = plpy.execute(plan, [email])

    if result1 and len(result1) == 1:
        data = {'username': result1[0]['username'], 'first_name': result1[0]['first_name'], 'last_name': result1[0]['last_name'], 'email': result1[0]['email'], 'sex': result1[0]['sex'], 'country': result1[0]['country'], 'type': result1[0]['type']}

        conn = psycopg2.connect("host=" + host + " dbname=" + dbname + " user=" + in_user + " password=" + password)
        cursor = conn.cursor()

        cursor.execute("SELECT email, password, data FROM users WHERE email = %s", [result1[0]['email']])
        result2 = cursor.fetchone()

        if result2 is None:
            cursor.execute("INSERT INTO users(email, password, data, type, created_by, updated_by) VALUES (%s, %s, %s, %s, %s, %s)", [result1[0]['email'], result1[0]['password'], json.dumps(data), result1[0]['type'], source, source])

        conn.commit()
        conn.close()

$bl_insert_user_function$ LANGUAGE plpythonu;

CREATE OR REPLACE FUNCTION bl_update_user(email CHARACTER VARYING, source CHARACTER VARYING) RETURNS VOID AS $bl_update_user_function$
    import json
    import psycopg2

    host = '10.0.0.35'
    dbname = 'users'
    in_user = 'users'
    password = 'iQeeLEsw'

    plan = plpy.prepare("SELECT username, password, first_name, last_name, email, sex, country, type FROM blusers_blocklogicuser WHERE email = $1", ["text"])
    rows = plpy.execute(plan, [email])
    if rows and len(rows) == 1:
        data = {'username': rows[0]['username'], 'first_name': rows[0]['first_name'], 'last_name': rows[0]['last_name'], 'email': rows[0]['email'], 'sex': rows[0]['sex'], 'country': rows[0]['country'], 'type': rows[0]['type']}

        conn = psycopg2.connect("host=" + host + " dbname=" + dbname + " user=" + in_user + " password=" + password)
        cursor = conn.cursor()

        cursor.execute("SELECT email, password, data FROM users WHERE email = %s", [email])
        result = cursor.fetchone()

        if result and len(result) > 0:
            cursor.execute("UPDATE users SET data = %s, password = %s, type = %s, datetime_updated = NOW(), updated_by = %s WHERE email = %s", [json.dumps(data), rows[0]['password'], rows[0]['type'], source, email])
        else:
            plan = plpy.prepare("SELECT bl_insert_user($1)", ["text"])
            plpy.execute(plan, [email,])

        conn.commit()
        conn.close()

$bl_update_user_function$ LANGUAGE plpythonu;