delete from pos_billitem where bill_id in (select id from pos_bill where company_id = XX);
delete from pos_bill where company_id = XX;

