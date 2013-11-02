alter table notification_notice rename column user_id to recipient_id;
alter table notification_notice add column sender_id integer;
drop index notification_notice_user_id;
create index notification_notice_recipient_id on notification_notice using btree (recipient_id);

