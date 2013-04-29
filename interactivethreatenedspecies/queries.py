#STATS = "SELECT Species.id, Species.red_list, IF(Species.red_list='EX', 7, SUM(IF(Species.red_list='EW', 6, IF(Species.red_list='CR', 5, IF(Species.red_list='EN', 4, IF(Species.red_list='VU', 3, IF(Species.red_list='NT', 2, IF(Species.red_list='LC', 1, IF(Species.red_list='LR/nt', 2, IF(Species.red_list='LR/cd', 1, IF(Species.red_list='LR/lc', 1, 0))))))))))) as Stat FROM Species, Country WHERE Species.id=Country.id AND Species.id IN ('3', '4', '5', '6', '7', '8', '9', '167005', '42641', '106001862') GROUP BY Species.id"
#COUNTRIES = "SELECT DISTINCT Country.name FROM Country"
SPECIES_SEARCH = "SELECT DISTINCT id FROM Name WHERE LOWER(name) LIKE LOWER('%{0}%')"
COUNTRY_BY_SPECIE = "SELECT name from Country WHERE id='{0}'"
COUNTRY_STATS = "SELECT SUM(IF(Species.red_list='CR', 5, IF(Species.red_list='EN', 4, IF(Species.red_list='VU', 3, IF(Species.red_list='NT', 2, IF(Species.red_list='LC', 1, IF(Species.red_list='LR/nt', 2, IF(Species.red_list='LR/cd', 1, IF(Species.red_list='LR/lc', 1, 0))))))))) as Stat, Country.name FROM Species,Country WHERE Species.id=Country.id AND Country.id IN ('{0}') GROUP BY Country.name"