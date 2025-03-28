--
-- PostgreSQL database dump
--

-- Dumped from database version 17.2
-- Dumped by pg_dump version 17.2

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

--
-- Name: topology; Type: SCHEMA; Schema: -; Owner: nebus
--

CREATE SCHEMA IF NOT EXISTS topology;


ALTER SCHEMA topology OWNER TO nebus;

--
-- Name: SCHEMA topology; Type: COMMENT; Schema: -; Owner: nebus
--

COMMENT ON SCHEMA topology IS 'PostGIS Topology schema';


--
-- Name: postgis; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS postgis WITH SCHEMA public;


--
-- Name: EXTENSION postgis; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION postgis IS 'PostGIS geometry and geography spatial types and functions';


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: nebus
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


ALTER TABLE public.alembic_version OWNER TO nebus;

--
-- Name: buildings; Type: TABLE; Schema: public; Owner: nebus
--

CREATE TABLE public.buildings (
    id integer NOT NULL,
    address character varying,
    coordinates public.geometry(Point)
);


ALTER TABLE public.buildings OWNER TO nebus;

--
-- Name: buildings_id_seq; Type: SEQUENCE; Schema: public; Owner: nebus
--

CREATE SEQUENCE public.buildings_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.buildings_id_seq OWNER TO nebus;

--
-- Name: buildings_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: nebus
--

ALTER SEQUENCE public.buildings_id_seq OWNED BY public.buildings.id;


--
-- Name: categories; Type: TABLE; Schema: public; Owner: nebus
--

CREATE TABLE public.categories (
    id integer NOT NULL,
    parent_id integer,
    name character varying NOT NULL
);


ALTER TABLE public.categories OWNER TO nebus;

--
-- Name: categories_id_seq; Type: SEQUENCE; Schema: public; Owner: nebus
--

CREATE SEQUENCE public.categories_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.categories_id_seq OWNER TO nebus;

--
-- Name: categories_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: nebus
--

ALTER SEQUENCE public.categories_id_seq OWNED BY public.categories.id;


--
-- Name: companies; Type: TABLE; Schema: public; Owner: nebus
--

CREATE TABLE public.companies (
    id integer NOT NULL,
    name character varying,
    building_id integer
);


ALTER TABLE public.companies OWNER TO nebus;

--
-- Name: companies_id_seq; Type: SEQUENCE; Schema: public; Owner: nebus
--

CREATE SEQUENCE public.companies_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.companies_id_seq OWNER TO nebus;

--
-- Name: companies_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: nebus
--

ALTER SEQUENCE public.companies_id_seq OWNED BY public.companies.id;


--
-- Name: company_category_association; Type: TABLE; Schema: public; Owner: nebus
--

CREATE TABLE public.company_category_association (
    company_id integer NOT NULL,
    category_id integer NOT NULL
);


ALTER TABLE public.company_category_association OWNER TO nebus;

--
-- Name: phone_numbers; Type: TABLE; Schema: public; Owner: nebus
--

CREATE TABLE public.phone_numbers (
    id integer NOT NULL,
    phone_number character varying(20),
    company_id integer
);


ALTER TABLE public.phone_numbers OWNER TO nebus;

--
-- Name: phone_numbers_id_seq; Type: SEQUENCE; Schema: public; Owner: nebus
--

CREATE SEQUENCE public.phone_numbers_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.phone_numbers_id_seq OWNER TO nebus;

--
-- Name: phone_numbers_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: nebus
--

ALTER SEQUENCE public.phone_numbers_id_seq OWNED BY public.phone_numbers.id;


--
-- Name: buildings id; Type: DEFAULT; Schema: public; Owner: nebus
--

ALTER TABLE ONLY public.buildings ALTER COLUMN id SET DEFAULT nextval('public.buildings_id_seq'::regclass);


--
-- Name: categories id; Type: DEFAULT; Schema: public; Owner: nebus
--

ALTER TABLE ONLY public.categories ALTER COLUMN id SET DEFAULT nextval('public.categories_id_seq'::regclass);


--
-- Name: companies id; Type: DEFAULT; Schema: public; Owner: nebus
--

ALTER TABLE ONLY public.companies ALTER COLUMN id SET DEFAULT nextval('public.companies_id_seq'::regclass);


--
-- Name: phone_numbers id; Type: DEFAULT; Schema: public; Owner: nebus
--

ALTER TABLE ONLY public.phone_numbers ALTER COLUMN id SET DEFAULT nextval('public.phone_numbers_id_seq'::regclass);


--
-- Data for Name: alembic_version; Type: TABLE DATA; Schema: public; Owner: nebus
--

COPY public.alembic_version (version_num) FROM stdin;
71f39b660b75
\.


--
-- Data for Name: buildings; Type: TABLE DATA; Schema: public; Owner: nebus
--

COPY public.buildings (id, address, coordinates) FROM stdin;
5	Москва, улица Льва Толстого, 16	0101000020E61000005A92CBB367DE4B40910C959D4FCB4240
6	Москва, улица Тимура Фрунзе, 20	0101000020E61000005C9E84781EDE4B403F2D07DD4DCB4240
\.


--
-- Data for Name: categories; Type: TABLE DATA; Schema: public; Owner: nebus
--

COPY public.categories (id, parent_id, name) FROM stdin;
1	\N	Технологии
2	1	Разработка
3	1	Машиностроение
4	\N	Еда
5	4	Молочная продукция
6	5	Маслобойни
7	4	Продуктовые магазины
8	\N	Розничная торговля
9	8	Супермаркеты
10	4	Пекарни
\.


--
-- Data for Name: companies; Type: TABLE DATA; Schema: public; Owner: nebus
--

COPY public.companies (id, name, building_id) FROM stdin;
13	Яндекс	5
14	Вкусвилл	5
15	Пекарня Столичная	6
\.


--
-- Data for Name: company_category_association; Type: TABLE DATA; Schema: public; Owner: nebus
--

COPY public.company_category_association (company_id, category_id) FROM stdin;
13	2
14	4
14	9
14	10
15	10
\.


--
-- Data for Name: phone_numbers; Type: TABLE DATA; Schema: public; Owner: nebus
--

COPY public.phone_numbers (id, phone_number, company_id) FROM stdin;
3	+79023456789	13
4	+72023456	13
5	+79053456609	14
6	+72035681	14
7	+79078896540	15
\.


--
-- Data for Name: spatial_ref_sys; Type: TABLE DATA; Schema: public; Owner: nebus
--

COPY public.spatial_ref_sys (srid, auth_name, auth_srid, srtext, proj4text) FROM stdin;
\.


--
-- Name: buildings_id_seq; Type: SEQUENCE SET; Schema: public; Owner: nebus
--

SELECT pg_catalog.setval('public.buildings_id_seq', 6, true);


--
-- Name: categories_id_seq; Type: SEQUENCE SET; Schema: public; Owner: nebus
--

SELECT pg_catalog.setval('public.categories_id_seq', 10, true);


--
-- Name: companies_id_seq; Type: SEQUENCE SET; Schema: public; Owner: nebus
--

SELECT pg_catalog.setval('public.companies_id_seq', 15, true);


--
-- Name: phone_numbers_id_seq; Type: SEQUENCE SET; Schema: public; Owner: nebus
--

SELECT pg_catalog.setval('public.phone_numbers_id_seq', 7, true);


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: nebus
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: buildings buildings_pkey; Type: CONSTRAINT; Schema: public; Owner: nebus
--

ALTER TABLE ONLY public.buildings
    ADD CONSTRAINT buildings_pkey PRIMARY KEY (id);


--
-- Name: categories categories_pkey; Type: CONSTRAINT; Schema: public; Owner: nebus
--

ALTER TABLE ONLY public.categories
    ADD CONSTRAINT categories_pkey PRIMARY KEY (id);


--
-- Name: companies companies_pkey; Type: CONSTRAINT; Schema: public; Owner: nebus
--

ALTER TABLE ONLY public.companies
    ADD CONSTRAINT companies_pkey PRIMARY KEY (id);


--
-- Name: company_category_association company_category_association_pkey; Type: CONSTRAINT; Schema: public; Owner: nebus
--

ALTER TABLE ONLY public.company_category_association
    ADD CONSTRAINT company_category_association_pkey PRIMARY KEY (company_id, category_id);


--
-- Name: phone_numbers phone_numbers_pkey; Type: CONSTRAINT; Schema: public; Owner: nebus
--

ALTER TABLE ONLY public.phone_numbers
    ADD CONSTRAINT phone_numbers_pkey PRIMARY KEY (id);


--
-- Name: idx_buildings_coordinates; Type: INDEX; Schema: public; Owner: nebus
--

CREATE INDEX idx_buildings_coordinates ON public.buildings USING gist (coordinates);


--
-- Name: ix_buildings_id; Type: INDEX; Schema: public; Owner: nebus
--

CREATE INDEX ix_buildings_id ON public.buildings USING btree (id);


--
-- Name: ix_categories_id; Type: INDEX; Schema: public; Owner: nebus
--

CREATE INDEX ix_categories_id ON public.categories USING btree (id);


--
-- Name: ix_companies_id; Type: INDEX; Schema: public; Owner: nebus
--

CREATE INDEX ix_companies_id ON public.companies USING btree (id);


--
-- Name: ix_phone_numbers_id; Type: INDEX; Schema: public; Owner: nebus
--

CREATE INDEX ix_phone_numbers_id ON public.phone_numbers USING btree (id);


--
-- Name: categories categories_parent_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nebus
--

ALTER TABLE ONLY public.categories
    ADD CONSTRAINT categories_parent_id_fkey FOREIGN KEY (parent_id) REFERENCES public.categories(id);


--
-- Name: companies companies_building_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nebus
--

ALTER TABLE ONLY public.companies
    ADD CONSTRAINT companies_building_id_fkey FOREIGN KEY (building_id) REFERENCES public.buildings(id);


--
-- Name: company_category_association company_category_association_category_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nebus
--

ALTER TABLE ONLY public.company_category_association
    ADD CONSTRAINT company_category_association_category_id_fkey FOREIGN KEY (category_id) REFERENCES public.categories(id);


--
-- Name: company_category_association company_category_association_company_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nebus
--

ALTER TABLE ONLY public.company_category_association
    ADD CONSTRAINT company_category_association_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.companies(id);


--
-- Name: phone_numbers phone_numbers_company_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nebus
--

ALTER TABLE ONLY public.phone_numbers
    ADD CONSTRAINT phone_numbers_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.companies(id);


--
-- PostgreSQL database dump complete
--

