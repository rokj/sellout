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


--
-- PostgreSQL database dump complete
--

alter table users add column type character varying(15) not null default 'normal';
grant all on database users to users;
