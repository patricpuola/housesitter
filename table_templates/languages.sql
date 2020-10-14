CREATE TABLE IF NOT EXISTS `languages` (
	`id` int NOT NULL AUTO_INCREMENT PRIMARY KEY,
	`key` varchar(50),
	`language_ISO` varchar(2),
	`value` varchar(50),
	`date_updated` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP() ON UPDATE CURRENT_TIMESTAMP()
) ENGINE = INNODB;