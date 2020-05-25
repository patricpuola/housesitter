CREATE TABLE IF NOT EXISTS `geocodes` (
  `id` int NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `query` varchar(100),
  `lat` DOUBLE DEFAULT 0,
  `lng` DOUBLE DEFAULT 0,
  `confidence` float,
  `city` varchar(50),
  `suburb` varchar(50),
  `date_updated` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP() ON UPDATE CURRENT_TIMESTAMP()
) ENGINE=INNODB;
