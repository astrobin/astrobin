alter table astrobin.astrobin_location convert to character set utf8;
alter table astrobin.astrobin_location modify name varchar(255) character set utf8 collate utf8_general_ci not null;
