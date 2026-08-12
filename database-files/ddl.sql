DROP DATABASE IF EXISTS encore;
CREATE DATABASE IF NOT EXISTS encore;
USE encore;

DROP TABLE IF EXISTS app_admin;
CREATE TABLE IF NOT EXISTS app_admin
(
   first_name    VARCHAR(50),
   last_name     VARCHAR(50),
   email_address VARCHAR(75) NOT NULL,
   admin_id      INT         NOT NULL,
   PRIMARY KEY (admin_id)
);


DROP TABLE IF EXISTS user;
CREATE TABLE IF NOT EXISTS user
(
   first_name      VARCHAR(50),
   last_name       VARCHAR(50),
   email_address   VARCHAR(75)                        NOT NULL,
   username        VARCHAR(30)                        NOT NULL,
   created_at      DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
   last_login      DATETIME,
   account_status  BOOL     DEFAULT true              NOT NULL,
   suspended_by_id INT,
   sus_start_date  DATETIME,
   sus_end_date    DATETIME,
   user_id         INT AUTO_INCREMENT                 NOT NULL,
   PRIMARY KEY (user_id),
   FOREIGN KEY (suspended_by_id) REFERENCES app_admin (admin_id)
);


DROP TABLE IF EXISTS follows;
CREATE TABLE IF NOT EXISTS follows
(
   follower_id INT                                NOT NULL,
   followee_id INT                                NOT NULL,
   followed_on DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
   PRIMARY KEY (follower_id, followee_id),
   FOREIGN KEY (follower_id) REFERENCES user (user_id) ON UPDATE CASCADE ON DELETE CASCADE,
   FOREIGN KEY (followee_id) REFERENCES user (user_id) ON UPDATE CASCADE ON DELETE CASCADE
);

DROP TABLE IF EXISTS artist;
CREATE TABLE IF NOT EXISTS artist
(
   artist_id   INT AUTO_INCREMENT NOT NULL,
   artist_name VARCHAR(100)       NOT NULL,
   genre       VARCHAR(50),
   PRIMARY KEY (artist_id)
);


DROP TABLE IF EXISTS venue_manager;
CREATE TABLE IF NOT EXISTS venue_manager
(
   vm_id         INT AUTO_INCREMENT NOT NULL,
   first_name    VARCHAR(50),
   last_name     VARCHAR(50),
   email_address VARCHAR(75)        NOT NULL,
   PRIMARY KEY (vm_id)
);


DROP TABLE IF EXISTS tour_manager;
CREATE TABLE IF NOT EXISTS tour_manager
(
   tm_id         INT         NOT NULL,
   first_name    VARCHAR(50),
   last_name     VARCHAR(50),
   email_address VARCHAR(75) NOT NULL,
   PRIMARY KEY (tm_id)
);

DROP TABLE IF EXISTS tag;
CREATE TABLE IF NOT EXISTS tag
(
   tag_id   INT         NOT NULL,
   tag_name VARCHAR(50) NOT NULL,
   PRIMARY KEY (tag_id)
);
DROP TABLE IF EXISTS venue;
CREATE TABLE IF NOT EXISTS venue
(
   venue_id      INT          NOT NULL,
   venue_name    VARCHAR(100) NOT NULL,
   street        VARCHAR(100),
   city          VARCHAR(50),
   state         VARCHAR(2),
   zip           VARCHAR(10),
   accessibility VARCHAR(100),
   capacity      INT          NOT NULL,
   managed_by_id INT          NOT NULL,
   PRIMARY KEY (venue_id),
   FOREIGN KEY (managed_by_id) REFERENCES venue_manager (vm_id)
);



DROP TABLE IF EXISTS section;
CREATE TABLE IF NOT EXISTS section
(
   section_id   INT         NOT NULL,
   section_name VARCHAR(50) NOT NULL,
   venue_id     INT         NOT NULL,
   PRIMARY KEY (venue_id, section_id),
   FOREIGN KEY (venue_id) REFERENCES venue (venue_id)
);


DROP TABLE IF EXISTS transportation;
CREATE TABLE IF NOT EXISTS transportation
(
   transport_id   INT NOT NULL,
   estimated_cost DECIMAL(6, 2),
   transport_type VARCHAR(50),
   instructions   TEXT,
   venue_id       INT NOT NULL,
   PRIMARY KEY (transport_id),
   FOREIGN KEY (venue_id) REFERENCES venue (venue_id)
);


DROP TABLE IF EXISTS tour;
CREATE TABLE IF NOT EXISTS tour
(
   tour_id        INT          NOT NULL,
   tour_name      VARCHAR(100) NOT NULL,
   start_date     DATE,
   end_date       DATE,
   main_artist_id INT          NOT NULL,
   managed_by_id  INT          NOT NULL,
   PRIMARY KEY (tour_id),
   FOREIGN KEY (main_artist_id) REFERENCES artist (artist_id),
   FOREIGN KEY (managed_by_id) REFERENCES tour_manager (tm_id)
);


DROP TABLE IF EXISTS `show`;
CREATE TABLE IF NOT EXISTS `show`
(
   show_id           INT  NOT NULL,
   show_date         DATE NOT NULL,
   start_time        TIME,
   expected_end_time TIME,
   total_attendees   INT,
   avg_ticket_price  DECIMAL(6, 2),
   venue_id          INT  NOT NULL,
   tour_id           INT  NOT NULL,
   PRIMARY KEY (show_id),
   FOREIGN KEY (venue_id) REFERENCES venue (venue_id),
   FOREIGN KEY (tour_id) REFERENCES tour (tour_id)
);


DROP TABLE IF EXISTS diary_entry;
CREATE TABLE IF NOT EXISTS diary_entry
(
   entry_id    INT                                NOT NULL,
   upload_date DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
   entry_text  TEXT,
   author_id   INT                                NOT NULL,
   PRIMARY KEY (entry_id),
   FOREIGN KEY (author_id) REFERENCES user (user_id) ON UPDATE CASCADE ON DELETE RESTRICT
);


DROP TABLE IF EXISTS review;
CREATE TABLE IF NOT EXISTS review
(
   review_id        INT AUTO_INCREMENT                 NOT NULL,
   author_user_id   INT                                NOT NULL,
   about_show_id    INT                                NULL,
   about_venue_id   INT                                NULL,
   about_artist_id  INT                                NULL,
   rating           INT                                NULL,
   review_text      TEXT,
   upload_date      DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
   last_updated     DATETIME,
   responding_tm_id INT,
   tm_response      TEXT,
   responding_vm_id INT,
   vm_response      TEXT,
   PRIMARY KEY (review_id),
   FOREIGN KEY (author_user_id) REFERENCES user (user_id) ON UPDATE CASCADE ON DELETE RESTRICT,
   FOREIGN KEY (about_show_id) REFERENCES `show` (show_id),
   FOREIGN KEY (about_venue_id) REFERENCES venue (venue_id),
   FOREIGN KEY (about_artist_id) REFERENCES artist (artist_id),
   FOREIGN KEY (responding_tm_id) REFERENCES tour_manager (tm_id),
   FOREIGN KEY (responding_vm_id) REFERENCES venue_manager (vm_id)
);


DROP TABLE IF EXISTS review_tag;
CREATE TABLE IF NOT EXISTS review_tag
(
   review_id INT NOT NULL,
   tag_id    INT NOT NULL,
   PRIMARY KEY (review_id, tag_id),
   FOREIGN KEY (review_id) REFERENCES review (review_id) ON UPDATE CASCADE ON DELETE RESTRICT,
   FOREIGN KEY (tag_id) REFERENCES tag (tag_id) ON UPDATE CASCADE ON DELETE RESTRICT
);


DROP TABLE IF EXISTS report;
CREATE TABLE IF NOT EXISTS report
(
   report_id        INT AUTO_INCREMENT NOT NULL,
   reporter_id      INT                NOT NULL,
   target_user_id   INT                NULL,
   target_review_id INT                NULL,
   report_type      VARCHAR(20)        NOT NULL,
   reason           TEXT,
   is_resolved      BOOL DEFAULT false NOT NULL,
   PRIMARY KEY (report_id),
   FOREIGN KEY (reporter_id) REFERENCES user (user_id),
   FOREIGN KEY (target_user_id) REFERENCES user (user_id),
   FOREIGN KEY (target_review_id) REFERENCES review (review_id)
);


DROP TABLE IF EXISTS report_admin;
CREATE TABLE IF NOT EXISTS report_admin
(
   report_id INT NOT NULL,
   admin_id  INT NOT NULL,
   PRIMARY KEY (report_id, admin_id),
   FOREIGN KEY (report_id) REFERENCES report (report_id),
   FOREIGN KEY (admin_id) REFERENCES app_admin (admin_id)
);


DROP TABLE IF EXISTS admin_venue;
CREATE TABLE IF NOT EXISTS admin_venue
(
   admin_id INT NOT NULL,
   venue_id INT NOT NULL,
   PRIMARY KEY (admin_id, venue_id),
   FOREIGN KEY (admin_id) REFERENCES app_admin (admin_id),
   FOREIGN KEY (venue_id) REFERENCES venue (venue_id)
);


DROP TABLE IF EXISTS admin_artist;
CREATE TABLE IF NOT EXISTS admin_artist
(
   admin_id  INT NOT NULL,
   artist_id INT NOT NULL,
   PRIMARY KEY (admin_id, artist_id),
   FOREIGN KEY (admin_id) REFERENCES app_admin (admin_id),
   FOREIGN KEY (artist_id) REFERENCES artist (artist_id)
);


DROP TABLE IF EXISTS user_show;
CREATE TABLE IF NOT EXISTS user_show
(
   user_id INT NOT NULL,
   show_id INT NOT NULL,
   PRIMARY KEY (user_id, show_id),
   FOREIGN KEY (user_id) REFERENCES user (user_id) ON UPDATE CASCADE ON DELETE RESTRICT,
   FOREIGN KEY (show_id) REFERENCES `show` (show_id) ON UPDATE CASCADE ON DELETE RESTRICT
);


INSERT INTO app_admin (admin_id, first_name, last_name, email_address)
VALUES (1, 'Andy', 'Chen', 'andy.chen@encoreapp.com'),
      (2, 'Priya', 'Nair', 'priya.nair@encoreapp.com'),
      (3, 'Marcus', 'Webb', 'marcus.webb@encoreapp.com'),
      (4, 'Sofia', 'Reyes', 'sofia.reyes@encoreapp.com');


INSERT INTO user (first_name, last_name, email_address, username, last_login, account_status, suspended_by_id,
                 sus_start_date, sus_end_date, user_id)
VALUES ('Maya', 'Ortiz', 'maya.ortiz@gmail.com', 'maya_streams', '2026-08-05 10:12:00', true, NULL, NULL, NULL, 1),
      ('Teddy', 'Ruiz', 'teddy.ruiz@gmail.com', 'teddyfrmtheblock', '2026-08-06 18:45:00', true, NULL, NULL, NULL, 2),
      ('Enrica', 'Osei', 'enrica.osei@gmail.com', 'enrica_o', '2026-08-07 09:00:00', true, NULL, NULL, NULL, 3),
      ('Devon', 'Park', 'devon.park@gmail.com', 'devpark22', '2026-07-20 22:15:00', false, 1, '2026-07-21 00:00:00',
       '2026-08-04 00:00:00', 4);


INSERT INTO follows (follower_id, followee_id, followed_on)
VALUES (1, 2, '2026-06-01 08:00:00'),
      (1, 3, '2026-06-03 08:00:00'),
      (2, 3, '2026-06-10 14:20:00'),
      (3, 1, '2026-06-15 19:30:00');


INSERT INTO artist (artist_id, artist_name, genre)
VALUES (1, 'Aurora Nightingale', 'Pop'),
      (2, 'Neon Skies', 'Synth-pop'),
      (3, 'The Rustbelt', 'Indie Rock'),
      (4, 'Glass Animals', 'Alternative');


INSERT INTO venue_manager (vm_id, first_name, last_name, email_address)
VALUES (1, 'Teddy', 'Sullivan', 'teddy.sullivan@fenwaypark.com'),
      (2, 'Nina', 'Alvarez', 'nina.alvarez@tdgarden.com'),
      (3, 'Owen', 'Brooks', 'owen.brooks@rogersarena.ca'),
      (4, 'Lena', 'Kowalski', 'lena.kowalski@kiaforum.com');


INSERT INTO tour_manager (tm_id, first_name, last_name, email_address)
VALUES (1, 'Enrica', 'Costa', 'enrica.costa@touring.com'),
      (2, 'Jamal', 'Freeman', 'jamal.freeman@touring.com'),
      (3, 'Bianca', 'Silva', 'bianca.silva@touring.com'),
      (4, 'Rhys', 'Callahan', 'rhys.callahan@touring.com');


INSERT INTO tag (tag_id, tag_name)
VALUES (1, 'Sound Quality'),
      (2, 'Entry/Security'),
      (3, 'Merch Lines'),
      (4, 'Sightlines');


INSERT INTO venue (venue_id, venue_name, street, city, state, zip, accessibility, capacity, managed_by_id)
VALUES (1, 'Fenway Park', '4 Jersey St', 'Boston', 'MA', '02215', 'Wheelchair accessible', 37755, 1),
      (2, 'TD Garden', '100 Legends Way', 'Boston', 'MA', '02114', 'Wheelchair accessible', 19600, 2),
      (3, 'Rogers Arena', '800 Griffiths Way', 'Vancouver', 'BC', 'V6B6G1', 'Wheelchair accessible', 18910, 3),
      (4, 'Kia Forum', '3900 W Manchester Blvd', 'Inglewood', 'CA', '90305', 'Wheelchair accessible', 17505, 4);


INSERT INTO section (section_id, section_name, venue_id)
VALUES (1, 'Green Monster', 1),
      (2, 'Floor Section A', 2),
      (3, 'Lower Bowl 100', 3),
      (4, 'Upper Deck 300', 4);


INSERT INTO transportation (transport_id, estimated_cost, transport_type, instructions, venue_id)
VALUES (1, 3.50, 'MBTA Green Line', 'Take the Green Line to Kenmore station, 5 min walk.', 1),
      (2, 15.00, 'Rideshare', 'Drop-off at Causeway St entrance.', 2),
      (3, 5.00, 'SkyTrain', 'Take the Expo Line to Stadium-Chinatown station.', 3),
      (4, 12.00, 'Rideshare', 'Drop-off at Manchester Blvd main gate.', 4);


INSERT INTO tour (tour_id, tour_name, start_date, end_date, main_artist_id, managed_by_id)
VALUES (1, 'Neon Skies Tour', '2026-06-01', '2026-09-30', 1, 1),
      (2, 'Static & Stars Tour', '2026-05-15', '2026-08-20', 2, 2),
      (3, 'Rustbelt Revival Tour', '2026-07-01', '2026-10-15', 3, 3),
      (4, 'Heat Waves Tour', '2026-04-10', '2026-08-30', 4, 4);


INSERT INTO `show` (show_id, show_date, start_time, expected_end_time, total_attendees, avg_ticket_price, venue_id,
                   tour_id)
VALUES (1, '2026-08-01', '19:30:00', '22:15:00', 36200, 145.00, 1, 1),
      (2, '2026-08-03', '20:00:00', '22:45:00', 18900, 165.50, 2, 2),
      (3, '2026-08-05', '19:00:00', '21:50:00', 17600, 98.00, 3, 3),
      (4, '2026-08-09', '20:15:00', '23:00:00', 16800, 120.75, 4, 4);


INSERT INTO diary_entry (entry_id, upload_date, entry_text, author_id)
VALUES (1, '2026-08-02 09:00:00', 'First time at Fenway for a concert, sound was incredible off the Monster.', 1),
      (2, '2026-08-04 11:30:00', 'TD Garden floor seats were worth every penny tonight.', 2),
      (3, '2026-08-06 08:15:00', 'Rogers Arena show was a bit chaotic getting in but the setlist made up for it.', 3),
      (4, '2026-08-10 07:45:00', 'Kia Forum acoustics are underrated, best show I have been to all year.', 4);


INSERT INTO review (author_user_id, about_show_id, about_venue_id, about_artist_id, rating, review_text,
                   responding_tm_id, tm_response, responding_vm_id, vm_response)
VALUES (1, 1, NULL, NULL, 4,
       'Took 40 minutes to get through the west gate. Only 2 bag checks open for a sold-out show.', NULL, NULL, 1,
       'We hear you, we are adding more entry staff for the next show.'),
      (2, 2, NULL, NULL, 5, 'Merch line wrapped around the concourse and moved so slowly I missed the opener.', 2,
       'Thanks for flagging this, we are working with the venue on merch flow.', NULL, NULL),
      (3, NULL, 3, NULL, 3, 'Sound was bouncing weird off the upper deck, hard to hear vocals clearly.', NULL, NULL,
       NULL, NULL),
      (4, NULL, NULL, 4, 5,
       'Glass Animals put on an unbelievable show, tight setlist and great energy the whole night.', NULL, NULL, NULL,
       NULL);


INSERT INTO review_tag (review_id, tag_id)
VALUES (1, 2),
      (2, 3),
      (3, 1),
      (3, 4);


INSERT INTO report (reporter_id, target_user_id, target_review_id, report_type, reason, is_resolved)
VALUES (1, 4, NULL, 'user', 'Posting spam links in diary entries.', true),
      (2, NULL, 3, 'review', 'Review seems fake, account has no attendance record for that show.', false),
      (3, 4, NULL, 'user', 'Repeatedly harassing other users in comments.', true),
      (4, NULL, 2, 'review', 'Review contains inappropriate language.', false);


INSERT INTO report_admin (report_id, admin_id)
VALUES (1, 1),
      (2, 2),
      (3, 1),
      (4, 3);


INSERT INTO admin_venue (admin_id, venue_id)
VALUES (1, 1),
      (2, 2),
      (3, 3),
      (4, 4);


INSERT INTO admin_artist (admin_id, artist_id)
VALUES (1, 1),
      (2, 2),
      (3, 3),
      (4, 4);


INSERT INTO user_show (user_id, show_id)
VALUES (1, 1),
      (2, 2),
      (3, 3),
      (4, 4);
