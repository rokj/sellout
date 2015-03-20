/*
author: Rok Jaklič
date: 30. 11. 2014
company: Blocklogic
*/

-- must be run as superuser
-- on users database

--
-- PostgreSQL database dump
--

SET statement_timeout = 0;
SET lock_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET client_min_messages = warning;

SET search_path = public, pg_catalog;

SET default_tablespace = '';

SET default_with_oids = false;

--
-- Name: users; Type: TABLE; Schema: public; Owner: users; Tablespace: 
--

CREATE TABLE users (
    email character varying(75) NOT NULL,
    password character varying(128) NOT NULL,
    data character varying(1000),
    datetime_created timestamp with time zone DEFAULT now() NOT NULL,
    datetime_updated timestamp with time zone DEFAULT now() NOT NULL,
    datetime_deleted timestamp with time zone,
    created_by character varying(100) NOT NULL,
    updated_by character varying(100) NOT NULL
);


ALTER TABLE public.users OWNER TO postgres;

--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: users
--

COPY users (email, password, data, datetime_created, datetime_updated, datetime_deleted, created_by, updated_by) FROM stdin;
rjaklic@dada.net		{"pos.si": {"username": "rjaklic@dada.net", "password": "", "first_name": "", "last_name": "", "email": "rjaklic@dada.net"}}	2013-11-11 14:13:47.505216+01	2013-11-11 14:13:47.505216+01	\N	pos.si	pos.si
rok@blocklogic.net	pbkdf2_sha256$10000$sq2oxFln9EWY$u4jgnbTW6a+wKbX/vg1SuTlZLL6hFYokwdyojBq0MjE=	{"username": "rok@blocklogic.net", "password": "pbkdf2_sha256$10000$sq2oxFln9EWY$u4jgnbTW6a+wKbX/vg1SuTlZLL6hFYokwdyojBq0MjE=", "first_name": "Rok", "last_name": "Pok", "email": "rok@blocklogic.net"}	2013-10-27 11:20:33.273744+01	2013-10-27 11:20:33.273744+01	\N	pos.si	pos.si
rjaklic@gmail.com	pbkdf2_sha256$10000$NDty6P4Ir8dk$nm0CUZ5CQOBnORVE15oTdzrNNNtVG0e5mx3YWeGMFUY=	{"username": "rjaklic@gmail.com", "password": "pbkdf2_sha256$10000$NDty6P4Ir8dk$nm0CUZ5CQOBnORVE15oTdzrNNNtVG0e5mx3YWeGMFUY=", "first_name": "Fak", "last_name": "Saklic", "email": "rjaklic@gmail.com"}	2013-10-27 11:25:24.043642+01	2013-10-27 11:25:24.043642+01	\N	pos.si	pos.si
\.


--
-- Name: users_email_pk; Type: CONSTRAINT; Schema: public; Owner: users; Tablespace: 
--

ALTER TABLE ONLY users
    ADD CONSTRAINT users_email_pk PRIMARY KEY (email);

alter table users add column type character varying(15) not null default 'normal';
grant all on database users to users;

-- TRIGGERS

CREATE LANGUAGE plpythonu;

DROP FUNCTION update_django_users() CASCADE;

CREATE OR REPLACE FUNCTION update_django_users() RETURNS TRIGGER AS $update_django_users_trigger$
    import json
    import psycopg2
    import logging

    go = ''

    taskmanager_host = '127.0.0.1'
    taskmanager_dbname = 'taskmanager'
    taskmanager_in_user = 'taskmanager'
    taskmanager_password = 'taskmanager'

    pos_host = '127.0.0.1'
    pos_dbname = 'pos'
    pos_in_user = 'pos'
    pos_password = 'pos'

    conn = None

    if TD['new']['updated_by'] == 'taskmanager':
        go = 'pos'
    elif TD['new']['updated_by'] == 'pos':
        go = 'taskmanager'

    if go == 'taskmanager':
        conn = psycopg2.connect("host=" + taskmanager_host + " dbname=" + taskmanager_dbname + " user=" + taskmanager_in_user + " password=" + taskmanager_password)
        cursor = conn.cursor()
    elif go == 'pos':
        conn = psycopg2.connect("host=" + pos_host + " dbname=" + pos_dbname + " user=" + pos_in_user + " password=" + pos_password)
        cursor = conn.cursor()

    if go != '' and cursor:
        user_data = json.loads(TD['new']['data'])

        cursor.execute("SELECT email FROM blusers_blocklogicuser WHERE email = %s", [TD['new']['email']])
        result = cursor.fetchone()

        if result:
            cursor.execute("UPDATE blusers_blocklogicuser SET first_name = %s, last_name = %s, password = %s, datetime_updated = NOW() WHERE email = %s", [user_data['first_name'], user_data['last_name'], TD['new']['password'], TD['new']['email']])
            if 'sex' in user_data:
                cursor.execute("UPDATE blusers_blocklogicuser SET sex = %s WHERE email = %s", [user_data['sex'],  TD['new']['email']])
            if 'country' in user_data:
                cursor.execute("UPDATE blusers_blocklogicuser SET country = %s WHERE email = %s", [user_data['country'],  TD['new']['email']])

    if conn:
        conn.commit()

$update_django_users_trigger$ LANGUAGE plpythonu;

DROP TRIGGER update_django_users_trigger ON users CASCADE;
CREATE TRIGGER update_django_users_trigger
    AFTER UPDATE ON users
    FOR EACH ROW
    EXECUTE PROCEDURE update_django_users();

-- update users set updated_by = 'pos' where email = 'rok@blocklogic.net';
