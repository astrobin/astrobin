#!/bin/bash

sudo -u postgres psql -d astrobin <<"EOF"
COPY auth_group (id, name) FROM stdin;
1	Producers
2	Retailers
3	Paying
4	affiliate-1
5	affiliate-10
6	affiliate-50
7	affiliate-100
8	affiliate-inf
9	retailer-affiliate-1
11	retailer-affiliate-10
12	retailer-affiliate-50
13	retailer-affiliate-100
14	retailer-affiliate-inf
100	everyone
1000	rawdata-meteor
1001	rawdata-luna
1002	rawdata-sol
1003	rawdata-galaxia
2000	astrobin-donor-coffee-monthly
2001	astrobin-donor-snack-monthly
2002	astrobin-donor-pizza-monthly
2003	astrobin-donor-movie-monthly
2004	astrobin-donor-dinner-monthly
2005	astrobin-donor-coffee-yearly
2006	astrobin-donor-snack-yearly
2007	astrobin-donor-pizza-yearly
2008	astrobin-donor-movie-yearly
2009	astrobin-donor-dinner-yearly
3000	IOTD_Staff
\.

COPY subscription_subscription (id, name, description, price, recurrence_period, recurrence_unit, group_id, trial_period, trial_unit) FROM stdin;
1	Meteor	5 GB	2.95	1	M	1000	7	D
2	Luna	100 GB	9.95	1	M	1001	7	D
3	Sol	250 GB	19.95	1	M	1002	7	D
4	Galaxia	500 GB	49.95	1	M	1003	7	D
5	AstroBin Donor Coffee Monthly		2.50	1	M	2000	0	D
6	AstroBin Donor Snack Monthly		3.50	1	M	2001	0	D
7	AstroBin Donor Movie Monthly		10.00	1	M	2002	0	D
8	AstroBin Donor Dinner Monthly		25.00	1	M	2003	0	D
9	AstroBin Donor Coffee Yearly		24.00	1	Y	2004	0	D
10	AstroBin Donor Snack Yearly		34.00	1	Y	2005	0	D
11	AstroBin Donor Pizza Yearly		60.00	1	Y	2006	0	D
12	AstroBin Donor Movie Yearly		100.00	1	Y	2007	0	D
13	AstroBin Donor Dinner Yearly		250.00	1	Y	2008	0	D
14	AstroBin Donor Pizza Monthly		6.00	1	M	2009	0	D
\.
EOF
