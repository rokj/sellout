/* change rjaklic@gmail.com to something else? */

delete from pos_stockupdatehistory where created_by_id = (select id from blusers_blocklogicuser where email = 'rjaklic@gmail.com');
delete from pos_stock where created_by_id = (select id from blusers_blocklogicuser where email = 'rjaklic@gmail.com');
delete from pos_billcompany where created_by_id = (select id from blusers_blocklogicuser where email = 'rjaklic@gmail.com');
delete from pos_billitemdiscount where created_by_id = (select id from blusers_blocklogicuser where email = 'rjaklic@gmail.com');
delete from pos_billitem where created_by_id = (select id from blusers_blocklogicuser where email = 'rjaklic@gmail.com');
delete from pos_bill where created_by_id = (select id from blusers_blocklogicuser where email = 'rjaklic@gmail.com');
delete from pos_billregister where created_by_id = (select id from blusers_blocklogicuser where email = 'rjaklic@gmail.com');
delete from pos_document where created_by_id = (select id from blusers_blocklogicuser where email = 'rjaklic@gmail.com');
delete from pos_purchaseprice where created_by_id = (select id from blusers_blocklogicuser where email = 'rjaklic@gmail.com');
delete from pos_price where created_by_id = (select id from blusers_blocklogicuser where email = 'rjaklic@gmail.com');
delete from pos_product where created_by_id = (select id from blusers_blocklogicuser where email = 'rjaklic@gmail.com');
delete from pos_category where created_by_id = (select id from blusers_blocklogicuser where email = 'rjaklic@gmail.com');
delete from payment_payment where created_by_id = (select id from blusers_blocklogicuser where email = 'rjaklic@gmail.com');
delete from pos_contact where created_by_id = (select id from blusers_blocklogicuser where email = 'rjaklic@gmail.com');
delete from sync_sync where company_id IN (select id from pos_company where created_by_id = (select id from blusers_blocklogicuser where email = 'rjaklic@gmail.com'));
delete from pos_permission where created_by_id = (select id from blusers_blocklogicuser where email = 'rjaklic@gmail.com');
delete from pos_register where created_by_id = (select id from blusers_blocklogicuser where email = 'rjaklic@gmail.com');
delete from pos_tax where created_by_id = (select id from blusers_blocklogicuser where email = 'rjaklic@gmail.com');
delete from config_userconfig where created_by_id = (select id from blusers_blocklogicuser where email = 'rjaklic@gmail.com');
delete from config_companyconfig where created_by_id = (select id from blusers_blocklogicuser where email = 'rjaklic@gmail.com');
delete from pos_company where created_by_id = (select id from blusers_blocklogicuser where email = 'rjaklic@gmail.com');
delete from pos_category where created_by_id = (select id from blusers_blocklogicuser where email = 'rjaklic@gmail.com');
delete from blusers_blocklogicuser_images where blocklogicuser_id = (select id from blusers_blocklogicuser where email = 'rjaklic@gmail.com');
delete from blusers_userimage where created_by_id = (select id from blusers_blocklogicuser where email = 'rjaklic@gmail.com');
delete from blusers_blocklogicuser where email = 'rjaklic@gmail.com';