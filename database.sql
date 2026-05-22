--
-- PostgreSQL database dump
--

\restrict XVuei3THKP8ce48HnOlre5DRWI75LpvGCHEpqRdLvg4e5JByv3S9S8WLhxVsFoL

-- Dumped from database version 18.3 (Homebrew)
-- Dumped by pg_dump version 18.3 (Homebrew)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: alert_acknowledgements; Type: TABLE; Schema: public; Owner: kowtharabdiqadir
--

CREATE TABLE public.alert_acknowledgements (
    id integer NOT NULL,
    alert_id character varying(255) NOT NULL,
    patient_id integer NOT NULL,
    acknowledged_by integer NOT NULL,
    acknowledged_at timestamp without time zone DEFAULT now() NOT NULL,
    note text
);


ALTER TABLE public.alert_acknowledgements OWNER TO kowtharabdiqadir;

--
-- Name: alert_acknowledgements_id_seq; Type: SEQUENCE; Schema: public; Owner: kowtharabdiqadir
--

CREATE SEQUENCE public.alert_acknowledgements_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.alert_acknowledgements_id_seq OWNER TO kowtharabdiqadir;

--
-- Name: alert_acknowledgements_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: kowtharabdiqadir
--

ALTER SEQUENCE public.alert_acknowledgements_id_seq OWNED BY public.alert_acknowledgements.id;


--
-- Name: caregiver_notes; Type: TABLE; Schema: public; Owner: kowtharabdiqadir
--

CREATE TABLE public.caregiver_notes (
    id integer NOT NULL,
    patient_id integer NOT NULL,
    author_id integer NOT NULL,
    note_text text NOT NULL,
    tag character varying(32),
    related_time time without time zone,
    created_at timestamp without time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.caregiver_notes OWNER TO kowtharabdiqadir;

--
-- Name: caregiver_notes_id_seq; Type: SEQUENCE; Schema: public; Owner: kowtharabdiqadir
--

CREATE SEQUENCE public.caregiver_notes_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.caregiver_notes_id_seq OWNER TO kowtharabdiqadir;

--
-- Name: caregiver_notes_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: kowtharabdiqadir
--

ALTER SEQUENCE public.caregiver_notes_id_seq OWNED BY public.caregiver_notes.id;


--
-- Name: caregiver_patient; Type: TABLE; Schema: public; Owner: kowtharabdiqadir
--

CREATE TABLE public.caregiver_patient (
    id integer NOT NULL,
    caregiver_id integer NOT NULL,
    patient_id integer NOT NULL,
    assigned_at timestamp without time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.caregiver_patient OWNER TO kowtharabdiqadir;

--
-- Name: caregiver_patient_id_seq; Type: SEQUENCE; Schema: public; Owner: kowtharabdiqadir
--

CREATE SEQUENCE public.caregiver_patient_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.caregiver_patient_id_seq OWNER TO kowtharabdiqadir;

--
-- Name: caregiver_patient_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: kowtharabdiqadir
--

ALTER SEQUENCE public.caregiver_patient_id_seq OWNED BY public.caregiver_patient.id;


--
-- Name: doctor_patient; Type: TABLE; Schema: public; Owner: kowtharabdiqadir
--

CREATE TABLE public.doctor_patient (
    id integer NOT NULL,
    doctor_id integer NOT NULL,
    patient_id integer NOT NULL,
    assigned_at timestamp without time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.doctor_patient OWNER TO kowtharabdiqadir;

--
-- Name: doctor_patient_id_seq; Type: SEQUENCE; Schema: public; Owner: kowtharabdiqadir
--

CREATE SEQUENCE public.doctor_patient_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.doctor_patient_id_seq OWNER TO kowtharabdiqadir;

--
-- Name: doctor_patient_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: kowtharabdiqadir
--

ALTER SEQUENCE public.doctor_patient_id_seq OWNED BY public.doctor_patient.id;


--
-- Name: medication_events; Type: TABLE; Schema: public; Owner: kowtharabdiqadir
--

CREATE TABLE public.medication_events (
    id integer NOT NULL,
    event_type text,
    event_time time without time zone,
    container_id text,
    weight_change double precision,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    patient_id integer NOT NULL
);


ALTER TABLE public.medication_events OWNER TO kowtharabdiqadir;

--
-- Name: medication_events_id_seq; Type: SEQUENCE; Schema: public; Owner: kowtharabdiqadir
--

CREATE SEQUENCE public.medication_events_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.medication_events_id_seq OWNER TO kowtharabdiqadir;

--
-- Name: medication_events_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: kowtharabdiqadir
--

ALTER SEQUENCE public.medication_events_id_seq OWNED BY public.medication_events.id;


--
-- Name: medication_schedules; Type: TABLE; Schema: public; Owner: kowtharabdiqadir
--

CREATE TABLE public.medication_schedules (
    id integer NOT NULL,
    medication_name text NOT NULL,
    scheduled_time text NOT NULL,
    dose text NOT NULL,
    patient_id integer NOT NULL
);


ALTER TABLE public.medication_schedules OWNER TO kowtharabdiqadir;

--
-- Name: medication_schedules_id_seq; Type: SEQUENCE; Schema: public; Owner: kowtharabdiqadir
--

CREATE SEQUENCE public.medication_schedules_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.medication_schedules_id_seq OWNER TO kowtharabdiqadir;

--
-- Name: medication_schedules_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: kowtharabdiqadir
--

ALTER SEQUENCE public.medication_schedules_id_seq OWNED BY public.medication_schedules.id;


--
-- Name: patients; Type: TABLE; Schema: public; Owner: kowtharabdiqadir
--

CREATE TABLE public.patients (
    id integer NOT NULL,
    user_id integer NOT NULL,
    date_of_birth date,
    conditions text,
    created_at timestamp without time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.patients OWNER TO kowtharabdiqadir;

--
-- Name: patients_id_seq; Type: SEQUENCE; Schema: public; Owner: kowtharabdiqadir
--

CREATE SEQUENCE public.patients_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.patients_id_seq OWNER TO kowtharabdiqadir;

--
-- Name: patients_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: kowtharabdiqadir
--

ALTER SEQUENCE public.patients_id_seq OWNED BY public.patients.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: kowtharabdiqadir
--

CREATE TABLE public.users (
    id integer NOT NULL,
    email character varying(255) NOT NULL,
    password_hash text NOT NULL,
    full_name character varying(255) NOT NULL,
    role character varying(16) NOT NULL,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    CONSTRAINT users_role_check CHECK (((role)::text = ANY ((ARRAY['patient'::character varying, 'caregiver'::character varying, 'doctor'::character varying])::text[])))
);


ALTER TABLE public.users OWNER TO kowtharabdiqadir;

--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: kowtharabdiqadir
--

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.users_id_seq OWNER TO kowtharabdiqadir;

--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: kowtharabdiqadir
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- Name: wellbeing_checkins; Type: TABLE; Schema: public; Owner: kowtharabdiqadir
--

CREATE TABLE public.wellbeing_checkins (
    id integer NOT NULL,
    mood text,
    energy text,
    side_effects text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    patient_id integer NOT NULL
);


ALTER TABLE public.wellbeing_checkins OWNER TO kowtharabdiqadir;

--
-- Name: wellbeing_checkins_id_seq; Type: SEQUENCE; Schema: public; Owner: kowtharabdiqadir
--

CREATE SEQUENCE public.wellbeing_checkins_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.wellbeing_checkins_id_seq OWNER TO kowtharabdiqadir;

--
-- Name: wellbeing_checkins_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: kowtharabdiqadir
--

ALTER SEQUENCE public.wellbeing_checkins_id_seq OWNED BY public.wellbeing_checkins.id;


--
-- Name: alert_acknowledgements id; Type: DEFAULT; Schema: public; Owner: kowtharabdiqadir
--

ALTER TABLE ONLY public.alert_acknowledgements ALTER COLUMN id SET DEFAULT nextval('public.alert_acknowledgements_id_seq'::regclass);


--
-- Name: caregiver_notes id; Type: DEFAULT; Schema: public; Owner: kowtharabdiqadir
--

ALTER TABLE ONLY public.caregiver_notes ALTER COLUMN id SET DEFAULT nextval('public.caregiver_notes_id_seq'::regclass);


--
-- Name: caregiver_patient id; Type: DEFAULT; Schema: public; Owner: kowtharabdiqadir
--

ALTER TABLE ONLY public.caregiver_patient ALTER COLUMN id SET DEFAULT nextval('public.caregiver_patient_id_seq'::regclass);


--
-- Name: doctor_patient id; Type: DEFAULT; Schema: public; Owner: kowtharabdiqadir
--

ALTER TABLE ONLY public.doctor_patient ALTER COLUMN id SET DEFAULT nextval('public.doctor_patient_id_seq'::regclass);


--
-- Name: medication_events id; Type: DEFAULT; Schema: public; Owner: kowtharabdiqadir
--

ALTER TABLE ONLY public.medication_events ALTER COLUMN id SET DEFAULT nextval('public.medication_events_id_seq'::regclass);


--
-- Name: medication_schedules id; Type: DEFAULT; Schema: public; Owner: kowtharabdiqadir
--

ALTER TABLE ONLY public.medication_schedules ALTER COLUMN id SET DEFAULT nextval('public.medication_schedules_id_seq'::regclass);


--
-- Name: patients id; Type: DEFAULT; Schema: public; Owner: kowtharabdiqadir
--

ALTER TABLE ONLY public.patients ALTER COLUMN id SET DEFAULT nextval('public.patients_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: kowtharabdiqadir
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- Name: wellbeing_checkins id; Type: DEFAULT; Schema: public; Owner: kowtharabdiqadir
--

ALTER TABLE ONLY public.wellbeing_checkins ALTER COLUMN id SET DEFAULT nextval('public.wellbeing_checkins_id_seq'::regclass);


--
-- Data for Name: alert_acknowledgements; Type: TABLE DATA; Schema: public; Owner: kowtharabdiqadir
--

COPY public.alert_acknowledgements (id, alert_id, patient_id, acknowledged_by, acknowledged_at, note) FROM stdin;
1	wellbeing:1:2	1	2	2026-05-04 00:27:47.671261	\N
2	missed:1:0800:2026-05-06	1	2	2026-05-06 17:00:29.132428	\N
3	missed:1:1200:2026-05-06	1	2	2026-05-06 17:00:31.100256	\N
4	missed:1:1500:2026-05-19	1	2	2026-05-19 23:39:15.996904	\N
5	missed:1:1730:2026-05-19	1	2	2026-05-19 23:39:18.658219	\N
6	missed:1:2000:2026-05-19	1	2	2026-05-19 23:50:12.519018	\N
\.


--
-- Data for Name: caregiver_notes; Type: TABLE DATA; Schema: public; Owner: kowtharabdiqadir
--

COPY public.caregiver_notes (id, patient_id, author_id, note_text, tag, related_time, created_at) FROM stdin;
1	1	2	Vitamin D was taken today - test	Mood	12:00:00	2026-05-03 21:18:10.524456
2	1	2	slept in - test	Sleep	08:00:00	2026-05-03 21:43:57.072119
3	1	2	test	\N	\N	2026-05-03 21:45:15.712307
4	1	2	test	Pain	08:00:00	2026-05-04 00:28:20.936513
5	1	2	test	Appetite	08:00:00	2026-05-14 17:18:32.929783
6	1	2	tESTING	Side effect	\N	2026-05-19 18:41:07.27741
7	7	2	Needed paracetamol	Pain	\N	2026-05-20 01:59:04.194467
\.


--
-- Data for Name: caregiver_patient; Type: TABLE DATA; Schema: public; Owner: kowtharabdiqadir
--

COPY public.caregiver_patient (id, caregiver_id, patient_id, assigned_at) FROM stdin;
1	2	1	2026-05-03 20:07:50.998532
7	2	6	2026-05-20 01:26:38.008291
8	2	7	2026-05-20 01:26:38.008291
\.


--
-- Data for Name: doctor_patient; Type: TABLE DATA; Schema: public; Owner: kowtharabdiqadir
--

COPY public.doctor_patient (id, doctor_id, patient_id, assigned_at) FROM stdin;
1	3	1	2026-05-03 20:07:51.011338
4	3	7	2026-05-20 03:03:24.696639
5	3	6	2026-05-20 03:03:24.696639
\.


--
-- Data for Name: medication_events; Type: TABLE DATA; Schema: public; Owner: kowtharabdiqadir
--

COPY public.medication_events (id, event_type, event_time, container_id, weight_change, created_at, patient_id) FROM stdin;
1	taken	21:16:19	patient_dashboard:08:00	\N	2026-05-03 21:16:19.463123	1
2	taken	21:16:37	manual_dashboard:08:00	\N	2026-05-03 21:16:37.982442	1
3	taken	21:16:42	manual_dashboard:08:00	\N	2026-05-03 21:16:42.330216	1
4	taken	21:16:57	manual_dashboard:12:00	\N	2026-05-03 21:16:57.682252	1
5	taken	21:16:58	manual_dashboard:18:00	\N	2026-05-03 21:16:58.562744	1
6	taken	21:17:01	manual_dashboard:08:00	\N	2026-05-03 21:17:01.895176	1
7	taken	21:17:42	caregiver:08:00	\N	2026-05-03 21:17:42.961451	1
8	taken	21:17:46	caregiver:12:00	\N	2026-05-03 21:17:46.42738	1
9	taken	21:22:46	manual_dashboard:08:00	\N	2026-05-03 21:22:46.620376	1
10	taken	21:23:02	manual_dashboard:08:00	\N	2026-05-03 21:23:02.567841	1
11	taken	21:23:23	manual_dashboard:18:00	\N	2026-05-03 21:23:23.315297	1
12	taken	21:26:37	caregiver:08:00	\N	2026-05-03 21:26:37.91758	1
13	taken	21:37:42	patient_dashboard:20:00	\N	2026-05-03 21:37:42.629646	1
14	taken	00:29:16	patient_dashboard:08:00	\N	2026-05-04 00:29:16.773309	1
15	taken	13:31:05	patient_dashboard:12:00	\N	2026-05-04 13:31:05.995158	1
16	taken	18:08:48	patient_dashboard:18:00	\N	2026-05-04 18:08:48.473093	1
17	taken	16:32:21	patient_dashboard:08:00	\N	2026-05-14 16:32:21.673142	1
18	taken	16:46:52.746059	patient_dashboard:12:00	\N	2026-05-14 16:46:52.746059	1
19	taken	16:53:53.139596	patient_dashboard:12:00	\N	2026-05-14 16:53:53.139596	1
20	taken	16:54:28.630599	patient_dashboard:12:00	\N	2026-05-14 16:54:28.630599	1
21	taken	17:05:51	patient_dashboard:15:00	\N	2026-05-14 17:05:51.308656	1
22	taken	17:12:39.658335	patient_dashboard:12:00	\N	2026-05-14 17:12:39.658335	1
23	taken	17:23:32.986609	patient_dashboard:18:00	\N	2026-05-14 17:23:32.986609	1
24	taken	15:31:21	patient_dashboard:12:00	\N	2026-05-19 15:31:21.627756	1
25	taken	17:56:19	mobile_app:18:00	\N	2026-05-19 17:56:19.224472	1
225	taken	13:21:00	demo_seed:12:00	\N	2026-04-20 13:21:00	1
226	taken	18:47:00	demo_seed:17:30	\N	2026-04-20 18:47:00	1
227	taken	18:10:00	demo_seed:18:00	\N	2026-04-20 18:10:00	1
228	taken	12:06:00	demo_seed:12:00	\N	2026-04-21 12:06:00	1
229	taken	18:27:00	demo_seed:17:30	\N	2026-04-21 18:27:00	1
230	taken	18:02:00	demo_seed:18:00	\N	2026-04-21 18:02:00	1
231	taken	20:07:00	demo_seed:20:00	\N	2026-04-21 20:07:00	1
232	taken	12:00:00	demo_seed:12:00	\N	2026-04-22 12:00:00	1
233	taken	17:30:00	demo_seed:17:30	\N	2026-04-22 17:30:00	1
234	taken	18:11:00	demo_seed:18:00	\N	2026-04-22 18:11:00	1
235	taken	20:01:00	demo_seed:20:00	\N	2026-04-22 20:01:00	1
236	taken	12:11:00	demo_seed:12:00	\N	2026-04-23 12:11:00	1
237	taken	17:38:00	demo_seed:17:30	\N	2026-04-23 17:38:00	1
238	taken	18:36:00	demo_seed:18:00	\N	2026-04-23 18:36:00	1
239	taken	20:06:00	demo_seed:20:00	\N	2026-04-23 20:06:00	1
240	taken	13:16:00	demo_seed:12:00	\N	2026-04-24 13:16:00	1
241	taken	17:39:00	demo_seed:17:30	\N	2026-04-24 17:39:00	1
242	taken	18:11:00	demo_seed:18:00	\N	2026-04-24 18:11:00	1
243	taken	20:07:00	demo_seed:20:00	\N	2026-04-24 20:07:00	1
244	taken	12:08:00	demo_seed:12:00	\N	2026-04-25 12:08:00	1
245	taken	17:33:00	demo_seed:17:30	\N	2026-04-25 17:33:00	1
246	taken	19:18:00	demo_seed:18:00	\N	2026-04-25 19:18:00	1
247	taken	15:24:00	demo_seed:15:00	\N	2026-04-26 15:24:00	1
248	taken	17:52:00	demo_seed:17:30	\N	2026-04-26 17:52:00	1
249	taken	18:07:00	demo_seed:18:00	\N	2026-04-26 18:07:00	1
250	taken	18:41:00	demo_seed:17:30	\N	2026-04-27 18:41:00	1
251	taken	18:13:00	demo_seed:18:00	\N	2026-04-27 18:13:00	1
252	taken	21:07:00	demo_seed:20:00	\N	2026-04-27 21:07:00	1
253	taken	12:01:00	demo_seed:12:00	\N	2026-04-28 12:01:00	1
254	taken	15:03:00	demo_seed:15:00	\N	2026-04-28 15:03:00	1
255	taken	18:20:00	demo_seed:18:00	\N	2026-04-28 18:20:00	1
256	taken	20:01:00	demo_seed:20:00	\N	2026-04-28 20:01:00	1
257	taken	12:00:00	demo_seed:12:00	\N	2026-04-29 12:00:00	1
258	taken	15:45:00	demo_seed:15:00	\N	2026-04-29 15:45:00	1
259	taken	17:49:00	demo_seed:17:30	\N	2026-04-29 17:49:00	1
260	taken	18:04:00	demo_seed:18:00	\N	2026-04-29 18:04:00	1
261	taken	12:13:00	demo_seed:12:00	\N	2026-04-30 12:13:00	1
262	taken	17:50:00	demo_seed:17:30	\N	2026-04-30 17:50:00	1
263	taken	19:30:00	demo_seed:18:00	\N	2026-04-30 19:30:00	1
264	taken	20:02:00	demo_seed:20:00	\N	2026-04-30 20:02:00	1
265	taken	12:07:00	demo_seed:12:00	\N	2026-05-01 12:07:00	1
266	taken	17:40:00	demo_seed:17:30	\N	2026-05-01 17:40:00	1
267	taken	19:15:00	demo_seed:18:00	\N	2026-05-01 19:15:00	1
268	taken	20:01:00	demo_seed:20:00	\N	2026-05-01 20:01:00	1
269	taken	12:17:00	demo_seed:12:00	\N	2026-05-02 12:17:00	1
270	taken	15:58:00	demo_seed:15:00	\N	2026-05-02 15:58:00	1
271	taken	18:48:00	demo_seed:18:00	\N	2026-05-02 18:48:00	1
272	taken	12:17:00	demo_seed:12:00	\N	2026-05-03 12:17:00	1
273	taken	17:42:00	demo_seed:17:30	\N	2026-05-03 17:42:00	1
274	taken	18:19:00	demo_seed:18:00	\N	2026-05-03 18:19:00	1
275	taken	12:16:00	demo_seed:12:00	\N	2026-05-04 12:16:00	1
276	taken	17:42:00	demo_seed:17:30	\N	2026-05-04 17:42:00	1
277	taken	19:13:00	demo_seed:18:00	\N	2026-05-04 19:13:00	1
278	taken	12:06:00	demo_seed:12:00	\N	2026-05-05 12:06:00	1
279	taken	15:24:00	demo_seed:15:00	\N	2026-05-05 15:24:00	1
280	taken	17:46:00	demo_seed:17:30	\N	2026-05-05 17:46:00	1
281	taken	18:20:00	demo_seed:18:00	\N	2026-05-05 18:20:00	1
282	taken	17:52:00	demo_seed:17:30	\N	2026-05-06 17:52:00	1
283	taken	18:12:00	demo_seed:18:00	\N	2026-05-06 18:12:00	1
284	taken	12:11:00	demo_seed:12:00	\N	2026-05-07 12:11:00	1
285	taken	15:16:00	demo_seed:15:00	\N	2026-05-07 15:16:00	1
286	taken	17:42:00	demo_seed:17:30	\N	2026-05-07 17:42:00	1
287	taken	18:14:00	demo_seed:18:00	\N	2026-05-07 18:14:00	1
288	taken	12:21:00	demo_seed:12:00	\N	2026-05-08 12:21:00	1
289	taken	15:21:00	demo_seed:15:00	\N	2026-05-08 15:21:00	1
290	taken	18:26:00	demo_seed:17:30	\N	2026-05-08 18:26:00	1
291	taken	18:17:00	demo_seed:18:00	\N	2026-05-08 18:17:00	1
292	taken	12:18:00	demo_seed:12:00	\N	2026-05-09 12:18:00	1
293	taken	17:43:00	demo_seed:17:30	\N	2026-05-09 17:43:00	1
294	taken	18:21:00	demo_seed:18:00	\N	2026-05-09 18:21:00	1
295	taken	12:19:00	demo_seed:12:00	\N	2026-05-10 12:19:00	1
296	taken	15:03:00	demo_seed:15:00	\N	2026-05-10 15:03:00	1
297	taken	17:52:00	demo_seed:17:30	\N	2026-05-10 17:52:00	1
298	taken	18:17:00	demo_seed:18:00	\N	2026-05-10 18:17:00	1
299	taken	21:24:00	demo_seed:20:00	\N	2026-05-10 21:24:00	1
300	taken	12:02:00	demo_seed:12:00	\N	2026-05-11 12:02:00	1
301	taken	17:41:00	demo_seed:17:30	\N	2026-05-11 17:41:00	1
302	taken	12:55:00	demo_seed:12:00	\N	2026-05-12 12:55:00	1
303	taken	16:14:00	demo_seed:15:00	\N	2026-05-12 16:14:00	1
304	taken	17:53:00	demo_seed:17:30	\N	2026-05-12 17:53:00	1
305	taken	18:04:00	demo_seed:18:00	\N	2026-05-12 18:04:00	1
306	taken	20:10:00	demo_seed:20:00	\N	2026-05-12 20:10:00	1
307	taken	12:23:00	demo_seed:12:00	\N	2026-05-13 12:23:00	1
308	taken	16:27:00	demo_seed:15:00	\N	2026-05-13 16:27:00	1
309	taken	17:50:00	demo_seed:17:30	\N	2026-05-13 17:50:00	1
310	taken	19:16:00	demo_seed:18:00	\N	2026-05-13 19:16:00	1
311	taken	12:10:00	demo_seed:12:00	\N	2026-05-14 12:10:00	1
312	taken	15:12:00	demo_seed:15:00	\N	2026-05-14 15:12:00	1
313	taken	18:23:00	demo_seed:18:00	\N	2026-05-14 18:23:00	1
314	taken	12:06:00	demo_seed:12:00	\N	2026-05-15 12:06:00	1
315	taken	18:20:00	demo_seed:18:00	\N	2026-05-15 18:20:00	1
316	taken	20:49:00	demo_seed:20:00	\N	2026-05-15 20:49:00	1
317	taken	12:15:00	demo_seed:12:00	\N	2026-05-16 12:15:00	1
318	taken	15:02:00	demo_seed:15:00	\N	2026-05-16 15:02:00	1
319	taken	12:24:00	demo_seed:12:00	\N	2026-05-17 12:24:00	1
320	taken	15:12:00	demo_seed:15:00	\N	2026-05-17 15:12:00	1
321	taken	18:08:00	demo_seed:18:00	\N	2026-05-17 18:08:00	1
322	taken	15:12:00	demo_seed:15:00	\N	2026-05-18 15:12:00	1
323	taken	17:46:00	demo_seed:17:30	\N	2026-05-18 17:46:00	1
324	taken	18:43:00	demo_seed:18:00	\N	2026-05-18 18:43:00	1
325	taken	13:04:00	demo_seed:12:00	\N	2026-05-19 13:04:00	1
326	taken	15:22:00	demo_seed:15:00	\N	2026-05-19 15:22:00	1
327	taken	18:24:00	demo_seed:18:00	\N	2026-05-19 18:24:00	1
328	taken	20:06:00	demo_seed:20:00	\N	2026-05-19 20:06:00	1
130	taken	00:07:02	manual_dashboard:20:00	\N	2026-05-20 00:07:02.850153	1
333	taken	01:31:31	caregiver:As needed	\N	2026-05-20 01:31:31.569961	7
335	taken	01:33:39	caregiver:08:00	\N	2026-05-20 01:33:39.45644	6
337	taken	01:40:59	manual_dashboard:As needed	\N	2026-05-20 01:40:59.941762	7
339	taken	02:14:26	manual_dashboard:prn	\N	2026-05-20 02:14:26.49311	7
341	taken	02:53:48	manual_dashboard:prn	\N	2026-05-20 02:53:48.644252	7
343	dose_event	13:37:39.950853	physical_container_1	\N	2026-05-20 13:37:39.950853	1
345	taken	13:52:32.126616	physical_container_1	-50	2026-05-20 13:52:32.126616	1
347	taken	17:00:03	mobile_app:12:30	\N	2026-05-20 17:00:03.065372	1
349	taken	23:24:33	mobile_app:12:30	\N	2026-05-21 23:24:33.889115	1
351	taken	23:24:36	mobile_app:17:30	\N	2026-05-21 23:24:36.393701	1
353	taken	23:24:38	mobile_app:20:00	\N	2026-05-21 23:24:38.102748	1
334	taken	01:31:51	caregiver:As needed	\N	2026-05-20 01:31:51.263901	7
336	taken	01:40:52	caregiver:As needed	\N	2026-05-20 01:40:52.918906	7
338	taken	02:06:21	manual_dashboard:prn	\N	2026-05-20 02:06:21.382589	7
340	taken	02:36:28	manual_dashboard:prn	\N	2026-05-20 02:36:28.245927	7
342	taken	13:30:12	patient_dashboard:12:00	\N	2026-05-20 13:30:12.941804	1
344	suspicious	13:49:04.545527	physical_container_1	-50	2026-05-20 13:49:04.545527	1
346	taken	14:03:55.231159	physical_container_1	-50	2026-05-20 14:03:55.231159	1
348	taken	23:24:32	mobile_app:12:00	\N	2026-05-21 23:24:32.333034	1
350	taken	23:24:35	mobile_app:15:00	\N	2026-05-21 23:24:35.199304	1
352	taken	23:24:37	mobile_app:18:00	\N	2026-05-21 23:24:37.068657	1
354	taken	23:24:38	mobile_app:23:25	\N	2026-05-21 23:24:38.915881	1
329	taken	15:05:00	demo_seed:15:00	\N	2026-05-20 15:05:00	1
330	taken	18:09:00	demo_seed:17:30	\N	2026-05-20 18:09:00	1
331	taken	18:24:00	demo_seed:18:00	\N	2026-05-20 18:24:00	1
332	taken	20:18:00	demo_seed:20:00	\N	2026-05-20 20:18:00	1
\.


--
-- Data for Name: medication_schedules; Type: TABLE DATA; Schema: public; Owner: kowtharabdiqadir
--

COPY public.medication_schedules (id, medication_name, scheduled_time, dose, patient_id) FROM stdin;
3	Iron Tablet	18:00	1 tablet	1
4	Metformin	20:00	1 tablet	1
5	vitamin C	15:00:00	7MG	1
6	vitamin a	17:30:00	5mg	1
2	Vitamin b	12:00:00	2 tablet	1
11	Aspirin	08:00	100mg	6
12	Lisinopril	13:00	10mg	6
13	Vitamin D	18:30	1 tablet	6
14	Paracetamol PRN	23:59	500mg when needed	7
15	Vitamin D	12:30:00	5MG	1
16	Haemoglobin	23:25:00	7mg	1
\.


--
-- Data for Name: patients; Type: TABLE DATA; Schema: public; Owner: kowtharabdiqadir
--

COPY public.patients (id, user_id, date_of_birth, conditions, created_at) FROM stdin;
1	1	\N	\N	2026-05-03 19:34:07.76682
6	8	\N	\N	2026-05-20 01:26:38.008291
7	9	\N	\N	2026-05-20 01:26:38.008291
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: kowtharabdiqadir
--

COPY public.users (id, email, password_hash, full_name, role, created_at) FROM stdin;
1	patient@meditrack.demo	pbkdf2:sha256:1000000$pTs7kb1Re2akXjIV$be8fac0e408f3cb7133ff9fc6c66d26ac6d0db9b5127cd4cc5275274acebe418	Sarah Khan	patient	2026-05-03 19:34:07.76682
9	emma@meditrack.demo	pbkdf2:sha256:1000000$pTs7kb1Re2akXjIV$be8fac0e408f3cb7133ff9fc6c66d26ac6d0db9b5127cd4cc5275274acebe418	Emma Wilson	patient	2026-05-20 01:26:38.008291
8	michael@meditrack.demo	pbkdf2:sha256:1000000$pTs7kb1Re2akXjIV$be8fac0e408f3cb7133ff9fc6c66d26ac6d0db9b5127cd4cc5275274acebe418	Michael Brown	patient	2026-05-20 01:26:38.008291
2	caregiver@meditrack.demo	pbkdf2:sha256:1000000$pTs7kb1Re2akXjIV$be8fac0e408f3cb7133ff9fc6c66d26ac6d0db9b5127cd4cc5275274acebe418	Nurse Jane	caregiver	2026-05-03 19:34:07.76682
3	doctor@meditrack.demo	pbkdf2:sha256:1000000$pTs7kb1Re2akXjIV$be8fac0e408f3cb7133ff9fc6c66d26ac6d0db9b5127cd4cc5275274acebe418	Dr. Smith	doctor	2026-05-03 19:34:07.76682
\.


--
-- Data for Name: wellbeing_checkins; Type: TABLE DATA; Schema: public; Owner: kowtharabdiqadir
--

COPY public.wellbeing_checkins (id, mood, energy, side_effects, created_at, patient_id) FROM stdin;
1	Good	Moderate	None	2026-05-03 20:39:24.098686	1
2	Very Good	Low	Headache	2026-05-03 21:21:58.68924	1
3	Very Good	High	Other	2026-05-03 21:37:59.935217	1
4	Good	Moderate	None	2026-05-04 00:33:47.915002	1
5	Very Good	High	None	2026-05-04 13:31:43.435788	1
6	Very Good	High	None	2026-05-06 16:59:52.864877	1
7	Very Good	Low	Headache	2026-05-06 19:05:20.854388	1
8	Very good	High	None	2026-05-19 19:40:45.634596	1
9	Very good	High	None	2026-05-19 19:58:50.115549	1
10	Neutral	Very low	Dizziness	2026-05-20 02:53:42.068513	7
\.


--
-- Name: alert_acknowledgements_id_seq; Type: SEQUENCE SET; Schema: public; Owner: kowtharabdiqadir
--

SELECT pg_catalog.setval('public.alert_acknowledgements_id_seq', 6, true);


--
-- Name: caregiver_notes_id_seq; Type: SEQUENCE SET; Schema: public; Owner: kowtharabdiqadir
--

SELECT pg_catalog.setval('public.caregiver_notes_id_seq', 7, true);


--
-- Name: caregiver_patient_id_seq; Type: SEQUENCE SET; Schema: public; Owner: kowtharabdiqadir
--

SELECT pg_catalog.setval('public.caregiver_patient_id_seq', 8, true);


--
-- Name: doctor_patient_id_seq; Type: SEQUENCE SET; Schema: public; Owner: kowtharabdiqadir
--

SELECT pg_catalog.setval('public.doctor_patient_id_seq', 5, true);


--
-- Name: medication_events_id_seq; Type: SEQUENCE SET; Schema: public; Owner: kowtharabdiqadir
--

SELECT pg_catalog.setval('public.medication_events_id_seq', 354, true);


--
-- Name: medication_schedules_id_seq; Type: SEQUENCE SET; Schema: public; Owner: kowtharabdiqadir
--

SELECT pg_catalog.setval('public.medication_schedules_id_seq', 16, true);


--
-- Name: patients_id_seq; Type: SEQUENCE SET; Schema: public; Owner: kowtharabdiqadir
--

SELECT pg_catalog.setval('public.patients_id_seq', 11, true);


--
-- Name: users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: kowtharabdiqadir
--

SELECT pg_catalog.setval('public.users_id_seq', 17, true);


--
-- Name: wellbeing_checkins_id_seq; Type: SEQUENCE SET; Schema: public; Owner: kowtharabdiqadir
--

SELECT pg_catalog.setval('public.wellbeing_checkins_id_seq', 10, true);


--
-- Name: alert_acknowledgements alert_acknowledgements_alert_id_acknowledged_by_key; Type: CONSTRAINT; Schema: public; Owner: kowtharabdiqadir
--

ALTER TABLE ONLY public.alert_acknowledgements
    ADD CONSTRAINT alert_acknowledgements_alert_id_acknowledged_by_key UNIQUE (alert_id, acknowledged_by);


--
-- Name: alert_acknowledgements alert_acknowledgements_pkey; Type: CONSTRAINT; Schema: public; Owner: kowtharabdiqadir
--

ALTER TABLE ONLY public.alert_acknowledgements
    ADD CONSTRAINT alert_acknowledgements_pkey PRIMARY KEY (id);


--
-- Name: caregiver_notes caregiver_notes_pkey; Type: CONSTRAINT; Schema: public; Owner: kowtharabdiqadir
--

ALTER TABLE ONLY public.caregiver_notes
    ADD CONSTRAINT caregiver_notes_pkey PRIMARY KEY (id);


--
-- Name: caregiver_patient caregiver_patient_caregiver_id_patient_id_key; Type: CONSTRAINT; Schema: public; Owner: kowtharabdiqadir
--

ALTER TABLE ONLY public.caregiver_patient
    ADD CONSTRAINT caregiver_patient_caregiver_id_patient_id_key UNIQUE (caregiver_id, patient_id);


--
-- Name: caregiver_patient caregiver_patient_pkey; Type: CONSTRAINT; Schema: public; Owner: kowtharabdiqadir
--

ALTER TABLE ONLY public.caregiver_patient
    ADD CONSTRAINT caregiver_patient_pkey PRIMARY KEY (id);


--
-- Name: doctor_patient doctor_patient_doctor_id_patient_id_key; Type: CONSTRAINT; Schema: public; Owner: kowtharabdiqadir
--

ALTER TABLE ONLY public.doctor_patient
    ADD CONSTRAINT doctor_patient_doctor_id_patient_id_key UNIQUE (doctor_id, patient_id);


--
-- Name: doctor_patient doctor_patient_pkey; Type: CONSTRAINT; Schema: public; Owner: kowtharabdiqadir
--

ALTER TABLE ONLY public.doctor_patient
    ADD CONSTRAINT doctor_patient_pkey PRIMARY KEY (id);


--
-- Name: medication_events medication_events_pkey; Type: CONSTRAINT; Schema: public; Owner: kowtharabdiqadir
--

ALTER TABLE ONLY public.medication_events
    ADD CONSTRAINT medication_events_pkey PRIMARY KEY (id);


--
-- Name: medication_schedules medication_schedules_pkey; Type: CONSTRAINT; Schema: public; Owner: kowtharabdiqadir
--

ALTER TABLE ONLY public.medication_schedules
    ADD CONSTRAINT medication_schedules_pkey PRIMARY KEY (id);


--
-- Name: patients patients_pkey; Type: CONSTRAINT; Schema: public; Owner: kowtharabdiqadir
--

ALTER TABLE ONLY public.patients
    ADD CONSTRAINT patients_pkey PRIMARY KEY (id);


--
-- Name: patients patients_user_id_key; Type: CONSTRAINT; Schema: public; Owner: kowtharabdiqadir
--

ALTER TABLE ONLY public.patients
    ADD CONSTRAINT patients_user_id_key UNIQUE (user_id);


--
-- Name: users users_email_key; Type: CONSTRAINT; Schema: public; Owner: kowtharabdiqadir
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_email_key UNIQUE (email);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: kowtharabdiqadir
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: wellbeing_checkins wellbeing_checkins_pkey; Type: CONSTRAINT; Schema: public; Owner: kowtharabdiqadir
--

ALTER TABLE ONLY public.wellbeing_checkins
    ADD CONSTRAINT wellbeing_checkins_pkey PRIMARY KEY (id);


--
-- Name: idx_alert_acks_alert_id; Type: INDEX; Schema: public; Owner: kowtharabdiqadir
--

CREATE INDEX idx_alert_acks_alert_id ON public.alert_acknowledgements USING btree (alert_id);


--
-- Name: idx_alert_acks_patient; Type: INDEX; Schema: public; Owner: kowtharabdiqadir
--

CREATE INDEX idx_alert_acks_patient ON public.alert_acknowledgements USING btree (patient_id, acknowledged_at DESC);


--
-- Name: idx_caregiver_notes_author; Type: INDEX; Schema: public; Owner: kowtharabdiqadir
--

CREATE INDEX idx_caregiver_notes_author ON public.caregiver_notes USING btree (author_id);


--
-- Name: idx_caregiver_notes_patient_created; Type: INDEX; Schema: public; Owner: kowtharabdiqadir
--

CREATE INDEX idx_caregiver_notes_patient_created ON public.caregiver_notes USING btree (patient_id, created_at DESC);


--
-- Name: idx_medication_events_patient; Type: INDEX; Schema: public; Owner: kowtharabdiqadir
--

CREATE INDEX idx_medication_events_patient ON public.medication_events USING btree (patient_id);


--
-- Name: idx_medication_events_patient_created; Type: INDEX; Schema: public; Owner: kowtharabdiqadir
--

CREATE INDEX idx_medication_events_patient_created ON public.medication_events USING btree (patient_id, created_at DESC);


--
-- Name: idx_medication_schedules_patient; Type: INDEX; Schema: public; Owner: kowtharabdiqadir
--

CREATE INDEX idx_medication_schedules_patient ON public.medication_schedules USING btree (patient_id);


--
-- Name: idx_wellbeing_patient; Type: INDEX; Schema: public; Owner: kowtharabdiqadir
--

CREATE INDEX idx_wellbeing_patient ON public.wellbeing_checkins USING btree (patient_id);


--
-- Name: alert_acknowledgements alert_acknowledgements_acknowledged_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: kowtharabdiqadir
--

ALTER TABLE ONLY public.alert_acknowledgements
    ADD CONSTRAINT alert_acknowledgements_acknowledged_by_fkey FOREIGN KEY (acknowledged_by) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: alert_acknowledgements alert_acknowledgements_patient_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: kowtharabdiqadir
--

ALTER TABLE ONLY public.alert_acknowledgements
    ADD CONSTRAINT alert_acknowledgements_patient_id_fkey FOREIGN KEY (patient_id) REFERENCES public.patients(id) ON DELETE CASCADE;


--
-- Name: caregiver_notes caregiver_notes_author_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: kowtharabdiqadir
--

ALTER TABLE ONLY public.caregiver_notes
    ADD CONSTRAINT caregiver_notes_author_id_fkey FOREIGN KEY (author_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: caregiver_notes caregiver_notes_patient_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: kowtharabdiqadir
--

ALTER TABLE ONLY public.caregiver_notes
    ADD CONSTRAINT caregiver_notes_patient_id_fkey FOREIGN KEY (patient_id) REFERENCES public.patients(id) ON DELETE CASCADE;


--
-- Name: caregiver_patient caregiver_patient_caregiver_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: kowtharabdiqadir
--

ALTER TABLE ONLY public.caregiver_patient
    ADD CONSTRAINT caregiver_patient_caregiver_id_fkey FOREIGN KEY (caregiver_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: caregiver_patient caregiver_patient_patient_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: kowtharabdiqadir
--

ALTER TABLE ONLY public.caregiver_patient
    ADD CONSTRAINT caregiver_patient_patient_id_fkey FOREIGN KEY (patient_id) REFERENCES public.patients(id) ON DELETE CASCADE;


--
-- Name: doctor_patient doctor_patient_doctor_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: kowtharabdiqadir
--

ALTER TABLE ONLY public.doctor_patient
    ADD CONSTRAINT doctor_patient_doctor_id_fkey FOREIGN KEY (doctor_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: doctor_patient doctor_patient_patient_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: kowtharabdiqadir
--

ALTER TABLE ONLY public.doctor_patient
    ADD CONSTRAINT doctor_patient_patient_id_fkey FOREIGN KEY (patient_id) REFERENCES public.patients(id) ON DELETE CASCADE;


--
-- Name: medication_events medication_events_patient_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: kowtharabdiqadir
--

ALTER TABLE ONLY public.medication_events
    ADD CONSTRAINT medication_events_patient_id_fkey FOREIGN KEY (patient_id) REFERENCES public.patients(id) ON DELETE CASCADE;


--
-- Name: medication_schedules medication_schedules_patient_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: kowtharabdiqadir
--

ALTER TABLE ONLY public.medication_schedules
    ADD CONSTRAINT medication_schedules_patient_id_fkey FOREIGN KEY (patient_id) REFERENCES public.patients(id) ON DELETE CASCADE;


--
-- Name: patients patients_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: kowtharabdiqadir
--

ALTER TABLE ONLY public.patients
    ADD CONSTRAINT patients_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: wellbeing_checkins wellbeing_checkins_patient_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: kowtharabdiqadir
--

ALTER TABLE ONLY public.wellbeing_checkins
    ADD CONSTRAINT wellbeing_checkins_patient_id_fkey FOREIGN KEY (patient_id) REFERENCES public.patients(id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

\unrestrict XVuei3THKP8ce48HnOlre5DRWI75LpvGCHEpqRdLvg4e5JByv3S9S8WLhxVsFoL

