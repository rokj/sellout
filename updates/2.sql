ALTER TABLE pos_billcompany DROP COLUMN tax_payer;
ALTER TABLE pos_billcompany ADD COLUMN "tax_payer" varchar(3) default 'no' NOT NULL;
ALTER TABLE pos_contact ADD COLUMN "tax_payer" varchar(3) default 'no' NOT NULL;
alter table pos_contact add column additional_info text;

alter table contact_contactregistry drop column company_name;
alter table contact_contactregistry add column company_name character varying (200);
alter table contact_contactregistry drop column city;
alter table contact_contactregistry add column city character varying (100);

alter table pos_contact drop column company_name;
alter table pos_contact add column company_name character varying (200);
alter table pos_contact drop column city;
alter table pos_contact add column city character varying (100);

alter table pos_billcontact add column tax_payer character varying(3) not null default 'no';
alter table pos_billcontact add column additional_info text;

alter table pos_billitem drop column stock;
