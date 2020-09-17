CREATE TABLE IF NOT EXISTS `costs` (
  `id` int NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `listing_id` int,
	`type` int,
	`description` text,
	`amount_EUR` float,
	`period` int,
	`period_multiplier` float,
	`flags` bit(8) NOT NULL DEFAULT 0,
  `date_updated` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP() ON UPDATE CURRENT_TIMESTAMP()
) ENGINE=INNODB;
