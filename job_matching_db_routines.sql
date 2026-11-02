-- MySQL dump 10.13  Distrib 8.0.33, for Win64 (x86_64)
--
-- Host: localhost    Database: job_matching_db
-- ------------------------------------------------------
-- Server version	8.0.46

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Temporary view structure for view `candidate_job_match`
--

DROP TABLE IF EXISTS `candidate_job_match`;
/*!50001 DROP VIEW IF EXISTS `candidate_job_match`*/;
SET @saved_cs_client     = @@character_set_client;
/*!50503 SET character_set_client = utf8mb4 */;
/*!50001 CREATE VIEW `candidate_job_match` AS SELECT 
 1 AS `candidate_id`,
 1 AS `candidate_name`,
 1 AS `job_id`,
 1 AS `job_title`,
 1 AS `total_required_skills`,
 1 AS `matched_skills`,
 1 AS `match_percentage`*/;
SET character_set_client = @saved_cs_client;

--
-- Final view structure for view `candidate_job_match`
--

/*!50001 DROP VIEW IF EXISTS `candidate_job_match`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb4 */;
/*!50001 SET character_set_results     = utf8mb4 */;
/*!50001 SET collation_connection      = utf8mb4_0900_ai_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`localhost` SQL SECURITY DEFINER */
/*!50001 VIEW `candidate_job_match` AS select `c`.`candidate_id` AS `candidate_id`,`c`.`name` AS `candidate_name`,`j`.`job_id` AS `job_id`,`j`.`title` AS `job_title`,count(`js`.`skill_id`) AS `total_required_skills`,count(`cs`.`skill_id`) AS `matched_skills`,round(((count(`cs`.`skill_id`) * 100.0) / nullif(count(`js`.`skill_id`),0)),2) AS `match_percentage` from (((`candidate` `c` join `job` `j`) join `job_skill` `js` on((`js`.`job_id` = `j`.`job_id`))) left join `candidate_skill` `cs` on(((`cs`.`candidate_id` = `c`.`candidate_id`) and (`cs`.`skill_id` = `js`.`skill_id`)))) where (`j`.`expiry_date` >= curdate()) group by `c`.`candidate_id`,`c`.`name`,`j`.`job_id`,`j`.`title` */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Dumping events for database 'job_matching_db'
--
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-11-02 22:31:41
