-- Run this script to create neccesary tables
CREATE TYPE dept_mode_t as    ENUM ('Auto', 'Manual')

CREATE TYPE course_unit_t as  ENUM ('to', 'or', 'n')
CREATE TYPE course_type_t as  ENUM ('Laboratory','Lecture','Seminar','Tutorial')
CREATE TYPE course_grade_t as ENUM ('Letter', 'P/NP', 'S/U')


CREATE TABLE "departments"
(
    "dept_mode"     dept_mode_t,
    "dept_id"       varchar(10),
    "dept_name"     varchar(100)
);

CREATE TABLE "courses"
(
    "dept_id"       varchar(10),
    "course_order"  int,
    "course_num"    varchar(16),
    "course_title"  varchar(200),
    "course_unit_t" course_unit_t
    "course_unit_s" smallint,
    "course_unit_e" smallint,
    "course_type"   course_type_t,
    "course_req"    json,
    "course_grade"  course_grade_t,
    "course_desc"   varchar(1500)
);

CREATE TABLE "lectures"
(
    "dept_id"       varchar(10),
    "course_num"    varchar(16),
    "course_id"     smallint,
    "lec_term"      varchar(4),     
    "lec_name"      varchar(16),    -- opt all below
    "lec_status"    varchar(32),    
    "lec_capacity"  json,
    "lec_w_status"  char(32),
    "lec_w_capacity"json,
    "lec_day"       varchar(16),
    "lec_time_s"    varchar(16),
    "lec_time_e"    varchar(16),
    "lec_location"  varchar(64),
    "lec_inst"      varchar(64)

);

CREATE TABLE "discussions"
(
    "lec_id"        char(9),
    "course_id"     char(9),
    "term"          char(4),     
    "dis_name"      char(16),
    "dis_status"    char(32),
    "dis_capacity"  json,
    "dis_w_status"  char(32),
    "dis_w_capacity"json,
    "dis_day"       char(8),
    "dis_time_s"    char(16),
    "dis_time_e"    char(16),
    "dis_location"  char(64),
    "dis_inst"      char(64)
);