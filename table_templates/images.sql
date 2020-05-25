CREATE TABLE IF NOT EXISTS `images` (
  `id` int NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `listing_id` int,
  `uuid` varchar(36),
  `hash_MD5` varchar(32),
  `extension` varchar(10),
  `mime_type` varchar(50),
  `original_filename` varchar(190) NOT NULL DEFAULT "",
  `date_added` timestamp NOT NULL DEFAULT "0000-00-00 00:00:00",
  `date_updated` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP() ON UPDATE CURRENT_TIMESTAMP()
) ENGINE=INNODB;
