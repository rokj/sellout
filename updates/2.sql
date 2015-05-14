ALTER TABLE pos_billcompany DROP COLUMN tax_payer;
ALTER TABLE pos_billcompany ADD COLUMN "tax_payer" varchar(3) default 'no' NOT NULL;
ALTER TABLE pos_contact ADD COLUMN "tax_payer" varchar(3) default 'no' NOT NULL;
