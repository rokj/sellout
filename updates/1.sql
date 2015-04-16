
-- to sve su apdejti na bill
delete from pos_billitem;
delete from pos_bill;

alter table pos_bill drop column formatted_serial;  -- možda to i nije treba
alter table pos_bill drop column serial;

alter table pos_bill add column serial varchar(64) null;
alter table pos_bill add column serial_number int null;
alter table pos_bill add column serial_prefix varchar(32) null;
