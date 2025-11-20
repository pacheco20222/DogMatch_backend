-- MySQL dump 10.13  Distrib 8.0.44, for Linux (x86_64)
--
-- Host: localhost    Database: dogmatch_db
-- ------------------------------------------------------
-- Server version	8.0.44

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `alembic_version`
--

DROP TABLE IF EXISTS `alembic_version`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `alembic_version` (
  `version_num` varchar(32) NOT NULL,
  PRIMARY KEY (`version_num`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `alembic_version`
--

LOCK TABLES `alembic_version` WRITE;
/*!40000 ALTER TABLE `alembic_version` DISABLE KEYS */;
INSERT INTO `alembic_version` VALUES ('add_message_indexes');
/*!40000 ALTER TABLE `alembic_version` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `blacklisted_tokens`
--

DROP TABLE IF EXISTS `blacklisted_tokens`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `blacklisted_tokens` (
  `id` int NOT NULL AUTO_INCREMENT,
  `jti` varchar(36) NOT NULL,
  `user_id` int NOT NULL,
  `token_type` enum('access','refresh') NOT NULL,
  `blacklisted_at` datetime NOT NULL,
  `expires_at` datetime NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `ix_blacklisted_tokens_jti` (`jti`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `blacklisted_tokens_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `blacklisted_tokens`
--

LOCK TABLES `blacklisted_tokens` WRITE;
/*!40000 ALTER TABLE `blacklisted_tokens` DISABLE KEYS */;
/*!40000 ALTER TABLE `blacklisted_tokens` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `dogs`
--

DROP TABLE IF EXISTS `dogs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `dogs` (
  `id` int NOT NULL AUTO_INCREMENT,
  `owner_id` int NOT NULL,
  `name` varchar(100) NOT NULL,
  `age_years` int DEFAULT NULL,
  `breed` varchar(100) DEFAULT NULL,
  `gender` enum('male','female') NOT NULL,
  `size` enum('small','medium','large','extra_large') NOT NULL,
  `weight` float DEFAULT NULL,
  `color` varchar(50) DEFAULT NULL,
  `personality` text,
  `energy_level` enum('low','moderate','high','very_high') DEFAULT NULL,
  `good_with_kids` enum('yes','no','not_sure') DEFAULT NULL,
  `good_with_dogs` enum('yes','no','not_sure') DEFAULT NULL,
  `good_with_cats` enum('yes','no','not_sure') DEFAULT NULL,
  `is_vaccinated` tinyint(1) NOT NULL,
  `is_neutered` tinyint(1) DEFAULT NULL,
  `health_notes` text,
  `special_needs` text,
  `description` text,
  `location` varchar(200) DEFAULT NULL,
  `is_available` tinyint(1) NOT NULL,
  `availability_type` enum('playdate','adoption','both') NOT NULL,
  `adoption_fee` float DEFAULT NULL,
  `is_adopted` tinyint(1) NOT NULL,
  `adopted_at` datetime DEFAULT NULL,
  `view_count` int NOT NULL,
  `like_count` int NOT NULL,
  `created_at` datetime NOT NULL,
  `updated_at` datetime NOT NULL,
  `last_active` datetime NOT NULL,
  PRIMARY KEY (`id`),
  KEY `owner_id` (`owner_id`),
  CONSTRAINT `dogs_ibfk_1` FOREIGN KEY (`owner_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=15 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `dogs`
--

LOCK TABLES `dogs` WRITE;
/*!40000 ALTER TABLE `dogs` DISABLE KEYS */;
INSERT INTO `dogs` VALUES (2,2,'Boster',3,'Golden Retriever ','male','large',25,NULL,'[\"Playful\", \"energetic\"]','high','yes','yes','yes',1,1,NULL,NULL,'He is playful and cool','Merida, Yuctana',1,'playdate',NULL,0,NULL,0,0,'2025-11-11 06:53:56','2025-11-11 06:53:56','2025-11-11 06:53:56'),(3,2,'Emily',3,'Labrador','female','large',25,NULL,'[\"Great\", \"energetic\"]','high','yes','yes','yes',1,1,NULL,NULL,'Helpful, joyful','Merida, Yucatan ',1,'playdate',NULL,0,NULL,0,0,'2025-11-11 06:54:55','2025-11-11 06:54:55','2025-11-11 06:54:55'),(4,3,'Andy',5,'Salchicha','male','medium',13,NULL,'[\"Energetic\", \"playful\"]','high','yes','yes','yes',1,1,NULL,NULL,'He is amazing and caring','Merida, Yucatan',1,'playdate',NULL,0,NULL,0,0,'2025-11-11 06:58:20','2025-11-11 06:58:20','2025-11-11 06:58:20'),(5,3,'Ben',4,'Husky','male','large',25,NULL,'[\"Energetic\", \"lovable\"]','high','yes','yes','yes',1,1,NULL,NULL,'Likes to play and have fun','Merida, Yucatan',1,'playdate',NULL,0,NULL,0,0,'2025-11-11 06:59:44','2025-11-11 06:59:44','2025-11-11 06:59:44'),(6,4,'Douglas',3,'Golden Retriever ','male','large',25,NULL,'[\"Energetic\", \"playful\", \"joyful\"]','high','yes','yes','yes',1,1,NULL,NULL,'Very playful and energetic','Merida, Yucatan ',1,'playdate',NULL,0,NULL,0,0,'2025-11-11 07:02:13','2025-11-11 07:02:13','2025-11-11 07:02:13'),(8,4,'Lily',5,'Golden retriever ','female','large',25,NULL,'[\"Energetic\", \"friendly\"]','high','yes','yes','yes',1,1,NULL,NULL,'Super funny, respectful, friendly ','Merida, Yucatan',1,'playdate',NULL,0,NULL,0,0,'2025-11-11 07:04:37','2025-11-11 07:04:37','2025-11-11 07:04:37'),(9,5,'Maluma',4,'Salchicha','male','large',24,NULL,'[\"Energetic\", \"playful\", \"intelligent\"]','high','yes','yes','yes',1,1,NULL,NULL,'Likes to play and very happy','Merida, Yucatan',1,'playdate',NULL,0,NULL,0,0,'2025-11-11 07:07:32','2025-11-11 07:07:32','2025-11-11 07:07:32'),(10,5,'Luna',6,'Husky','female','large',18,NULL,'[\"Friendly\", \"energetic\"]','high','yes','yes','yes',1,1,NULL,NULL,'Very playful and loyal','Merida, Yucatan',1,'playdate',NULL,0,NULL,0,0,'2025-11-11 07:08:47','2025-11-11 07:08:47','2025-11-11 07:08:47'),(11,6,'Leo',5,'Golden Retriever ','male','medium',15,NULL,'[\"Social\", \"joyful\"]','high','yes','yes','yes',1,1,NULL,NULL,'Joyful and playful','Merida, Yucatan ',1,'playdate',NULL,0,NULL,0,1,'2025-11-11 07:10:55','2025-11-11 07:16:12','2025-11-11 07:10:55'),(12,6,'Bonita',5,'Coker','female','small',5,NULL,'[\"Calm\", \"relax\", \"friendly\", \"playful\"]','high','yes','yes','yes',1,1,NULL,NULL,'Playful but calm','Merida, Yucatan ',1,'playdate',NULL,0,NULL,0,0,'2025-11-11 07:11:59','2025-11-11 07:11:59','2025-11-11 07:11:59'),(13,7,'Sparky',3,'Husky','male','large',25,NULL,'[\"Joyful\", \"playful\"]','high','yes','yes','yes',1,1,NULL,NULL,'He loves to play he is very energetic ','Merida, Yucatan',1,'playdate',NULL,0,NULL,0,0,'2025-11-11 07:14:05','2025-11-11 07:14:05','2025-11-11 07:14:05'),(14,7,'Jiggly',5,'Golden Retriever ','male','large',20,NULL,'[\"Energetic\", \"joyful\"]','high','yes','yes','yes',1,1,NULL,NULL,'Very joyful and playful ','Merida, Yucatan ',1,'playdate',NULL,0,NULL,0,0,'2025-11-11 07:15:02','2025-11-11 07:15:02','2025-11-11 07:15:02');
/*!40000 ALTER TABLE `dogs` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `event_registrations`
--

DROP TABLE IF EXISTS `event_registrations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `event_registrations` (
  `id` int NOT NULL AUTO_INCREMENT,
  `event_id` int NOT NULL,
  `user_id` int NOT NULL,
  `dog_id` int DEFAULT NULL,
  `status` enum('pending','confirmed','rejected','cancelled','waitlisted') NOT NULL,
  `registration_code` varchar(20) NOT NULL,
  `notes` text,
  `special_requests` text,
  `payment_status` enum('pending','completed','failed','refunded') NOT NULL,
  `payment_amount` float DEFAULT NULL,
  `payment_method` varchar(50) DEFAULT NULL,
  `payment_reference` varchar(100) DEFAULT NULL,
  `payment_date` datetime DEFAULT NULL,
  `discount_code` varchar(50) DEFAULT NULL,
  `discount_amount` float NOT NULL,
  `discount_percentage` float NOT NULL,
  `checked_in` tinyint(1) NOT NULL,
  `check_in_time` datetime DEFAULT NULL,
  `checked_out` tinyint(1) NOT NULL,
  `check_out_time` datetime DEFAULT NULL,
  `attended` tinyint(1) NOT NULL,
  `approved_by_user_id` int DEFAULT NULL,
  `approved_at` datetime DEFAULT NULL,
  `rejection_reason` text,
  `emergency_contact_name` varchar(100) DEFAULT NULL,
  `emergency_contact_phone` varchar(20) DEFAULT NULL,
  `registered_at` datetime NOT NULL,
  `updated_at` datetime NOT NULL,
  `cancelled_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_user_event_registration` (`event_id`,`user_id`),
  UNIQUE KEY `registration_code` (`registration_code`),
  KEY `approved_by_user_id` (`approved_by_user_id`),
  KEY `dog_id` (`dog_id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `event_registrations_ibfk_1` FOREIGN KEY (`approved_by_user_id`) REFERENCES `users` (`id`),
  CONSTRAINT `event_registrations_ibfk_2` FOREIGN KEY (`dog_id`) REFERENCES `dogs` (`id`),
  CONSTRAINT `event_registrations_ibfk_3` FOREIGN KEY (`event_id`) REFERENCES `events` (`id`),
  CONSTRAINT `event_registrations_ibfk_4` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `event_registrations`
--

LOCK TABLES `event_registrations` WRITE;
/*!40000 ALTER TABLE `event_registrations` DISABLE KEYS */;
/*!40000 ALTER TABLE `event_registrations` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `events`
--

DROP TABLE IF EXISTS `events`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `events` (
  `id` int NOT NULL AUTO_INCREMENT,
  `organizer_id` int NOT NULL,
  `title` varchar(200) NOT NULL,
  `description` text,
  `category` enum('meetup','training','adoption','competition','social','educational') NOT NULL,
  `event_date` datetime NOT NULL,
  `duration_hours` float DEFAULT NULL,
  `registration_deadline` datetime DEFAULT NULL,
  `location` varchar(300) NOT NULL,
  `city` varchar(100) DEFAULT NULL,
  `country` varchar(100) DEFAULT NULL,
  `venue_details` text,
  `max_participants` int DEFAULT NULL,
  `current_participants` int NOT NULL,
  `price` float NOT NULL,
  `currency` varchar(3) NOT NULL,
  `min_age_requirement` int DEFAULT NULL,
  `max_age_requirement` int DEFAULT NULL,
  `size_requirements` text,
  `breed_restrictions` text,
  `vaccination_required` tinyint(1) NOT NULL,
  `special_requirements` text,
  `status` enum('draft','published','cancelled','completed') NOT NULL,
  `is_recurring` tinyint(1) NOT NULL,
  `recurrence_pattern` varchar(50) DEFAULT NULL,
  `requires_approval` tinyint(1) NOT NULL,
  `image_url` varchar(500) DEFAULT NULL,
  `image_filename` varchar(255) DEFAULT NULL,
  `contact_email` varchar(255) DEFAULT NULL,
  `contact_phone` varchar(20) DEFAULT NULL,
  `additional_info` text,
  `rules_and_guidelines` text,
  `view_count` int NOT NULL,
  `interest_count` int NOT NULL,
  `created_at` datetime NOT NULL,
  `updated_at` datetime NOT NULL,
  `published_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `organizer_id` (`organizer_id`),
  CONSTRAINT `events_ibfk_1` FOREIGN KEY (`organizer_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `events`
--

LOCK TABLES `events` WRITE;
/*!40000 ALTER TABLE `events` DISABLE KEYS */;
/*!40000 ALTER TABLE `events` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `matches`
--

DROP TABLE IF EXISTS `matches`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `matches` (
  `id` int NOT NULL AUTO_INCREMENT,
  `dog_one_id` int NOT NULL,
  `dog_two_id` int NOT NULL,
  `status` enum('pending','matched','declined','expired') NOT NULL,
  `initiated_by_dog_id` int NOT NULL,
  `dog_one_action` enum('like','pass','super_like','pending') NOT NULL,
  `dog_two_action` enum('like','pass','super_like','pending') NOT NULL,
  `match_type` enum('playdate','adoption','general') NOT NULL,
  `created_at` datetime NOT NULL,
  `matched_at` datetime DEFAULT NULL,
  `expires_at` datetime DEFAULT NULL,
  `updated_at` datetime NOT NULL,
  `last_message_at` datetime DEFAULT NULL,
  `message_count` int NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `is_archived` tinyint(1) NOT NULL,
  `archived_by_user_id` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_match_pair` (`dog_one_id`,`dog_two_id`),
  KEY `archived_by_user_id` (`archived_by_user_id`),
  KEY `dog_two_id` (`dog_two_id`),
  KEY `initiated_by_dog_id` (`initiated_by_dog_id`),
  CONSTRAINT `matches_ibfk_1` FOREIGN KEY (`archived_by_user_id`) REFERENCES `users` (`id`),
  CONSTRAINT `matches_ibfk_2` FOREIGN KEY (`dog_one_id`) REFERENCES `dogs` (`id`),
  CONSTRAINT `matches_ibfk_3` FOREIGN KEY (`dog_two_id`) REFERENCES `dogs` (`id`),
  CONSTRAINT `matches_ibfk_4` FOREIGN KEY (`initiated_by_dog_id`) REFERENCES `dogs` (`id`),
  CONSTRAINT `no_self_match` CHECK ((`dog_one_id` <> `dog_two_id`)),
  CONSTRAINT `ordered_match_pair` CHECK ((`dog_one_id` < `dog_two_id`))
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `matches`
--

LOCK TABLES `matches` WRITE;
/*!40000 ALTER TABLE `matches` DISABLE KEYS */;
INSERT INTO `matches` VALUES (1,11,13,'matched',13,'like','like','general','2025-11-11 07:16:12','2025-11-11 07:24:01',NULL,'2025-11-19 07:51:49','2025-11-19 07:51:49',27,1,0,NULL);
/*!40000 ALTER TABLE `matches` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `messages`
--

DROP TABLE IF EXISTS `messages`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `messages` (
  `id` int NOT NULL AUTO_INCREMENT,
  `match_id` int NOT NULL,
  `sender_user_id` int NOT NULL,
  `content` text NOT NULL,
  `message_type` enum('text','image','location','system') NOT NULL,
  `is_read` tinyint(1) NOT NULL,
  `is_edited` tinyint(1) NOT NULL,
  `edited_at` datetime DEFAULT NULL,
  `image_url` varchar(500) DEFAULT NULL,
  `image_filename` varchar(255) DEFAULT NULL,
  `latitude` float DEFAULT NULL,
  `longitude` float DEFAULT NULL,
  `location_name` varchar(200) DEFAULT NULL,
  `system_data` text,
  `sent_at` datetime NOT NULL,
  `delivered_at` datetime DEFAULT NULL,
  `read_at` datetime DEFAULT NULL,
  `is_deleted` tinyint(1) NOT NULL,
  `deleted_at` datetime DEFAULT NULL,
  `deleted_by_user_id` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `deleted_by_user_id` (`deleted_by_user_id`),
  KEY `match_id` (`match_id`),
  KEY `sender_user_id` (`sender_user_id`),
  KEY `idx_messages_match_sent_at` (`match_id`,`sent_at`),
  KEY `idx_messages_match_deleted_sent` (`match_id`,`is_deleted`,`sent_at`),
  KEY `idx_messages_match_sender_read_deleted` (`match_id`,`sender_user_id`,`is_read`,`is_deleted`),
  CONSTRAINT `messages_ibfk_1` FOREIGN KEY (`deleted_by_user_id`) REFERENCES `users` (`id`),
  CONSTRAINT `messages_ibfk_2` FOREIGN KEY (`match_id`) REFERENCES `matches` (`id`),
  CONSTRAINT `messages_ibfk_3` FOREIGN KEY (`sender_user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=28 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `messages`
--

LOCK TABLES `messages` WRITE;
/*!40000 ALTER TABLE `messages` DISABLE KEYS */;
INSERT INTO `messages` VALUES (1,1,6,'Hello','text',1,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-11-11 07:24:16',NULL,'2025-11-11 07:25:36',0,NULL,NULL),(2,1,7,'Hello bro','text',1,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-11-11 07:26:08',NULL,'2025-11-11 07:26:17',0,NULL,NULL),(3,1,7,'Como estas','text',1,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-11-11 07:26:27',NULL,'2025-11-11 07:26:31',0,NULL,NULL),(4,1,6,'Bien y tu?','text',1,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-11-11 07:26:38',NULL,'2025-11-11 07:26:41',0,NULL,NULL),(5,1,6,'Hola buenas noches','text',1,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-11-11 07:54:45',NULL,'2025-11-11 07:54:54',0,NULL,NULL),(6,1,7,'Hola buenas noches todo bien gracias','text',1,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-11-11 07:57:50',NULL,'2025-11-11 08:02:30',0,NULL,NULL),(7,1,7,'Y como te va','text',1,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-11-11 07:58:22',NULL,'2025-11-11 08:02:30',0,NULL,NULL),(8,1,7,'Prueba 1','text',1,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-11-11 08:02:07',NULL,'2025-11-11 08:02:30',0,NULL,NULL),(9,1,6,'Bien ahí vamos','text',1,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-11-11 08:02:50',NULL,'2025-11-11 08:13:38',0,NULL,NULL),(10,1,7,'Prueba 2','text',1,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-11-11 08:07:42',NULL,'2025-11-11 08:11:33',0,NULL,NULL),(11,1,7,'Prueba 3','text',1,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-11-11 08:07:51',NULL,'2025-11-11 08:11:33',0,NULL,NULL),(12,1,7,'Another time','text',1,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-11-11 08:08:05',NULL,'2025-11-11 08:11:33',0,NULL,NULL),(13,1,7,'Prueba 4','text',1,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-11-11 08:09:44',NULL,'2025-11-11 08:11:33',0,NULL,NULL),(14,1,7,'Prueba','text',1,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-11-11 08:13:50',NULL,'2025-11-11 08:14:48',0,NULL,NULL),(15,1,7,'Hello','text',1,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-11-11 08:14:57',NULL,'2025-11-11 08:18:30',0,NULL,NULL),(16,1,7,'Prueba','text',1,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-11-11 08:15:02',NULL,'2025-11-11 08:18:30',0,NULL,NULL),(17,1,7,'Hello','text',1,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-11-11 08:16:54',NULL,'2025-11-11 08:18:30',0,NULL,NULL),(18,1,6,'Hello','text',1,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-11-11 08:17:00',NULL,'2025-11-11 08:18:20',0,NULL,NULL),(19,1,6,'Prueba','text',1,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-11-11 08:18:40',NULL,'2025-11-11 08:30:54',0,NULL,NULL),(20,1,6,'Que onda','text',1,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-11-11 08:32:04',NULL,'2025-11-11 08:32:12',0,NULL,NULL),(21,1,6,'Hola cómo estas','text',1,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-11-11 08:40:07',NULL,'2025-11-11 08:40:44',0,NULL,NULL),(22,1,6,'Prueba','text',1,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-11-11 08:40:23',NULL,'2025-11-11 08:40:44',0,NULL,NULL),(23,1,6,'Hola bro','text',1,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-11-11 08:46:09',NULL,'2025-11-11 08:46:23',0,NULL,NULL),(24,1,6,'Hola cómo estas','text',1,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-11-19 07:35:01',NULL,'2025-11-19 07:36:31',0,NULL,NULL),(25,1,6,'Bien y tu','text',1,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-11-19 07:35:08',NULL,'2025-11-19 07:36:31',0,NULL,NULL),(26,1,7,'Bien','text',1,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-11-19 07:35:20',NULL,'2025-11-19 07:35:26',0,NULL,NULL),(27,1,7,'Hola','text',0,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-11-19 07:51:49',NULL,NULL,0,NULL,NULL);
/*!40000 ALTER TABLE `messages` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `photos`
--

DROP TABLE IF EXISTS `photos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `photos` (
  `id` int NOT NULL AUTO_INCREMENT,
  `dog_id` int NOT NULL,
  `url` varchar(500) NOT NULL,
  `filename` varchar(255) DEFAULT NULL,
  `s3_key` varchar(500) DEFAULT NULL,
  `is_primary` tinyint(1) NOT NULL,
  `file_size` int DEFAULT NULL,
  `width` int DEFAULT NULL,
  `height` int DEFAULT NULL,
  `content_type` varchar(100) DEFAULT NULL,
  `created_at` datetime NOT NULL,
  PRIMARY KEY (`id`),
  KEY `dog_id` (`dog_id`),
  CONSTRAINT `photos_ibfk_1` FOREIGN KEY (`dog_id`) REFERENCES `dogs` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=13 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `photos`
--

LOCK TABLES `photos` WRITE;
/*!40000 ALTER TABLE `photos` DISABLE KEYS */;
INSERT INTO `photos` VALUES (1,2,'https://dogmatch-bucker-dev.s3.us-east-2.amazonaws.com/dog-photos/2/photo_43f11e97a4de44c08d50ff3231677132.jpg','43f11e97a4de44c08d50ff3231677132.jpg','dog-photos/2/photo_43f11e97a4de44c08d50ff3231677132.jpg',0,NULL,NULL,NULL,NULL,'2025-11-11 06:53:57'),(2,3,'https://dogmatch-bucker-dev.s3.us-east-2.amazonaws.com/dog-photos/3/photo_02f3975b0ff44d549958ba6ab4a18c32.jpg','02f3975b0ff44d549958ba6ab4a18c32.jpg','dog-photos/3/photo_02f3975b0ff44d549958ba6ab4a18c32.jpg',0,NULL,NULL,NULL,NULL,'2025-11-11 06:54:56'),(3,4,'https://dogmatch-bucker-dev.s3.us-east-2.amazonaws.com/dog-photos/4/photo_a6737d4024a2408f8e916aa51ebf85f0.png','a6737d4024a2408f8e916aa51ebf85f0.png','dog-photos/4/photo_a6737d4024a2408f8e916aa51ebf85f0.png',0,NULL,NULL,NULL,NULL,'2025-11-11 06:58:21'),(4,5,'https://dogmatch-bucker-dev.s3.us-east-2.amazonaws.com/dog-photos/5/photo_da48aacf713546b1875b6fa2e1e32bd7.jpg','da48aacf713546b1875b6fa2e1e32bd7.jpg','dog-photos/5/photo_da48aacf713546b1875b6fa2e1e32bd7.jpg',0,NULL,NULL,NULL,NULL,'2025-11-11 06:59:45'),(5,6,'https://dogmatch-bucker-dev.s3.us-east-2.amazonaws.com/dog-photos/6/photo_fc4aed8d83f648eaa1242e68c93c2493.jpg','fc4aed8d83f648eaa1242e68c93c2493.jpg','dog-photos/6/photo_fc4aed8d83f648eaa1242e68c93c2493.jpg',0,NULL,NULL,NULL,NULL,'2025-11-11 07:02:14'),(6,8,'https://dogmatch-bucker-dev.s3.us-east-2.amazonaws.com/dog-photos/8/photo_ae52347cdb5f46b381943f37a6d85fdc.png','ae52347cdb5f46b381943f37a6d85fdc.png','dog-photos/8/photo_ae52347cdb5f46b381943f37a6d85fdc.png',0,NULL,NULL,NULL,NULL,'2025-11-11 07:04:38'),(7,9,'https://dogmatch-bucker-dev.s3.us-east-2.amazonaws.com/dog-photos/9/photo_19a5e7d1e922404fb425769446d97891.png','19a5e7d1e922404fb425769446d97891.png','dog-photos/9/photo_19a5e7d1e922404fb425769446d97891.png',0,NULL,NULL,NULL,NULL,'2025-11-11 07:07:33'),(8,10,'https://dogmatch-bucker-dev.s3.us-east-2.amazonaws.com/dog-photos/10/photo_1cea71a08e1e4115938caee5f88bcca9.jpg','1cea71a08e1e4115938caee5f88bcca9.jpg','dog-photos/10/photo_1cea71a08e1e4115938caee5f88bcca9.jpg',0,NULL,NULL,NULL,NULL,'2025-11-11 07:08:47'),(9,11,'https://dogmatch-bucker-dev.s3.us-east-2.amazonaws.com/dog-photos/11/photo_f017ee2516d5449aa36d67b4ac777866.jpg','f017ee2516d5449aa36d67b4ac777866.jpg','dog-photos/11/photo_f017ee2516d5449aa36d67b4ac777866.jpg',0,NULL,NULL,NULL,NULL,'2025-11-11 07:10:56'),(10,12,'https://dogmatch-bucker-dev.s3.us-east-2.amazonaws.com/dog-photos/12/photo_94bad8a5ece4475099864b1097877c6c.png','94bad8a5ece4475099864b1097877c6c.png','dog-photos/12/photo_94bad8a5ece4475099864b1097877c6c.png',0,NULL,NULL,NULL,NULL,'2025-11-11 07:12:01'),(11,13,'https://dogmatch-bucker-dev.s3.us-east-2.amazonaws.com/dog-photos/13/photo_b24769c5808146aeb5548ca4bb08b733.png','b24769c5808146aeb5548ca4bb08b733.png','dog-photos/13/photo_b24769c5808146aeb5548ca4bb08b733.png',0,NULL,NULL,NULL,NULL,'2025-11-11 07:14:07'),(12,14,'https://dogmatch-bucker-dev.s3.us-east-2.amazonaws.com/dog-photos/14/photo_c2a1ab188ad9493d9b9534466019ea0c.jpg','c2a1ab188ad9493d9b9534466019ea0c.jpg','dog-photos/14/photo_c2a1ab188ad9493d9b9534466019ea0c.jpg',0,NULL,NULL,NULL,NULL,'2025-11-11 07:15:04');
/*!40000 ALTER TABLE `photos` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `users` (
  `id` int NOT NULL AUTO_INCREMENT,
  `email` varchar(255) NOT NULL,
  `password_hash` varchar(255) NOT NULL,
  `totp_secret` varchar(32) DEFAULT NULL,
  `is_2fa_enabled` tinyint(1) NOT NULL,
  `backup_codes` text,
  `last_totp_used` int DEFAULT NULL,
  `username` varchar(50) NOT NULL,
  `first_name` varchar(50) DEFAULT NULL,
  `last_name` varchar(50) DEFAULT NULL,
  `phone` varchar(20) DEFAULT NULL,
  `user_type` enum('owner','shelter','admin') NOT NULL,
  `city` varchar(100) DEFAULT NULL,
  `state` varchar(100) DEFAULT NULL,
  `country` varchar(100) DEFAULT NULL,
  `profile_photo_url` varchar(500) DEFAULT NULL,
  `profile_photo_filename` varchar(255) DEFAULT NULL,
  `is_active` tinyint(1) NOT NULL,
  `is_verified` tinyint(1) NOT NULL,
  `failed_login_attempts` int NOT NULL,
  `locked_until` datetime DEFAULT NULL,
  `created_at` datetime NOT NULL,
  `updated_at` datetime NOT NULL,
  `last_login` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `ix_users_email` (`email`),
  UNIQUE KEY `ix_users_username` (`username`)
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `users`
--

LOCK TABLES `users` WRITE;
/*!40000 ALTER TABLE `users` DISABLE KEYS */;
INSERT INTO `users` VALUES (1,'admin@dogmatch.com','pbkdf2:sha256:1000000$iQ69XO0wgbmeXNFe$3ab7cdcc929fd28645e8bfcf2797879cca653c53050b5b847912e03ed9cc965f',NULL,0,NULL,NULL,'admin','Admin','DogMatch','+1234567890','admin','San Francisco','California','USA',NULL,NULL,1,1,0,NULL,'2025-11-11 06:41:00','2025-11-11 06:41:00',NULL),(2,'sarah.johnson@email.com','pbkdf2:sha256:1000000$5AnCJL3pu6wpWHLN$167c9a691f5f0b0eadc2d7d4a64289c3594b4e966c2af06e1fd7a7238aed5392',NULL,0,NULL,NULL,'sarahjohnson','Sarah','Johnson','51979580','owner','Merida','Yucatan','Mexico',NULL,NULL,1,0,0,NULL,'2025-11-11 06:48:14','2025-11-11 07:16:55','2025-11-11 07:16:55'),(3,'mike.chen@email.com','pbkdf2:sha256:1000000$L8s6EJgIb8Ph3AAW$a288cd3ce4b154ad4f7a153288c149785e1fd740b2f3431de4f0c8b75cbb0a41',NULL,0,NULL,NULL,'mikechen','Mike','Chen','214864658','owner','Merida','Yucatan ','Mexico',NULL,NULL,1,0,0,NULL,'2025-11-11 06:57:22','2025-11-11 07:17:27','2025-11-11 07:17:27'),(4,'emma.rodriguez@email.com','pbkdf2:sha256:1000000$lbQ2OJWPX1S7ik5V$178fa5697a87ee1c4be18761a365c4c3fd1a31e66592dc7bc5376182be29057c',NULL,0,NULL,NULL,'emmarodriguez','Emma','Rodriguez','548781888','owner','Merida','Yucatan ','Mexico',NULL,NULL,1,0,0,NULL,'2025-11-11 07:01:00','2025-11-11 07:17:54','2025-11-11 07:17:54'),(5,'james.wilson@email.com','pbkdf2:sha256:1000000$sgao7CdGWksr0jOk$f7a0487620c8729f294e9d5f8a2b38d49efa82d4d27dbf3b40f119b8a45f4ad4',NULL,0,NULL,NULL,'jameswilson','James','Wilson','5185010846648','owner','Merida','Yucatan','Mexico',NULL,NULL,1,0,0,NULL,'2025-11-11 07:05:49','2025-11-11 07:18:25','2025-11-11 07:18:25'),(6,'lisa.martinez@email.com','pbkdf2:sha256:1000000$JpLHKJU0OrESPkJ4$a3ea5c58e11cdf4c2abe75375ef05037eeb6c0d7f725fc101e30d335d9828589',NULL,0,NULL,NULL,'lisamartinez','Lisa','Martinez','6167948484','owner','Merida','Yucatan ','Mexico','user-photos/6/profile_4b65b305899246bbae290136f1adeaf8.jpg','4b65b305899246bbae290136f1adeaf8.jpg',1,0,0,NULL,'2025-11-11 07:10:04','2025-11-19 07:36:24','2025-11-19 07:34:21'),(7,'jrp2022@gmail.com','pbkdf2:sha256:1000000$hW4YrOqw2sSwoATj$d43442cccd1fca95012a9fa741129e6cf49925ea551b34952f79853daf8bd5aa',NULL,0,NULL,NULL,'jrp2022','Jose ','Pacheco','9997002072','owner','Merida','Yucatan','Mexico','user-photos/7/profile_7f51d9b84d194d47b9a4190872ca6e88.jpg','7f51d9b84d194d47b9a4190872ca6e88.jpg',1,0,0,NULL,'2025-11-11 07:13:14','2025-11-19 07:35:50','2025-11-19 07:32:20');
/*!40000 ALTER TABLE `users` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping events for database 'dogmatch_db'
--

--
-- Dumping routines for database 'dogmatch_db'
--
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2025-11-19  8:03:01
