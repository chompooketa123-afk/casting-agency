-- =====================================================================
-- schema.sql : สร้างฐานข้อมูล Casting Agency ตาม ER Diagram (9 ตาราง)
-- รันไฟล์นี้ = ลบฐานข้อมูลเก่าทิ้งแล้วสร้างใหม่ทั้งหมด (ใช้ตอนเริ่มต้น/รีเซ็ต)
-- ชื่อตารางและชื่อคอลัมน์ตรงกับ "ตารางที่แปลงจาก ER Diagram" ในสไลด์ทุกตัว
-- =====================================================================

DROP DATABASE IF EXISTS casting_agency;
CREATE DATABASE casting_agency CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE casting_agency;

-- 1) PROJECT -----------------------------------------------------------
CREATE TABLE PROJECT (
    project_id      INT AUTO_INCREMENT PRIMARY KEY,
    project_name    VARCHAR(150) NOT NULL,
    project_type    VARCHAR(50)  NOT NULL,
    project_status  VARCHAR(20)  NOT NULL DEFAULT 'Open',
    client_name     VARCHAR(150) NOT NULL,
    CONSTRAINT ck_project_status
        CHECK (project_status IN ('Open','In_Progress','Completed','Cancelled'))
) ENGINE=InnoDB;

-- 2) ACTOR -------------------------------------------------------------
--   คอลัมน์ชุดแรก (full_name .. appearance_detail) มาจาก ER เดิม
--   คอลัมน์ชุดหลัง "คุณลักษณะภายนอก" เพิ่มเข้ามาเพื่อให้ค้นหา/จับคู่ตามรูปลักษณ์ได้จริง
--   (ทุกคอลัมน์ชุดหลังเป็นข้อมูลของนักแสดง 1 คน ต่อ 1 ค่า จึงอยู่ในตาราง ACTOR ได้โดยไม่ผิด 3NF)
CREATE TABLE ACTOR (
    actor_id           INT AUTO_INCREMENT PRIMARY KEY,
    full_name          VARCHAR(120) NOT NULL,
    gender             VARCHAR(10)  NOT NULL,
    actor_status       VARCHAR(10)  NOT NULL DEFAULT 'Active',
    appearance_detail  VARCHAR(500) NULL,
    -- ข้อมูลร่างกาย
    birth_date         DATE          NULL,      -- อายุคำนวณตอน query ด้วย TIMESTAMPDIFF ไม่เก็บเป็นคอลัมน์
    height_cm          SMALLINT      NULL,
    weight_kg          DECIMAL(5,1)  NULL,
    bust_chest_cm      SMALLINT      NULL,      -- รอบอก (ชาย) / รอบอก-บัสต์ (หญิง)
    waist_cm           SMALLINT      NULL,
    hip_cm             SMALLINT      NULL,
    shoe_size_eu       DECIMAL(3,1)  NULL,
    clothing_size      VARCHAR(4)    NULL,
    body_type          VARCHAR(12)   NULL,
    -- รูปลักษณ์
    skin_tone          VARCHAR(10)   NULL,
    hair_color         VARCHAR(12)   NULL,
    hair_length        VARCHAR(8)    NULL,
    hair_texture       VARCHAR(8)    NULL,
    eye_color          VARCHAR(12)   NULL,
    has_tattoo         BOOLEAN       NOT NULL DEFAULT FALSE,
    has_piercing       BOOLEAN       NOT NULL DEFAULT FALSE,
    -- การทำงาน
    experience_level   VARCHAR(14)   NOT NULL DEFAULT 'Beginner',
    province           VARCHAR(40)   NULL,
    can_travel         BOOLEAN       NOT NULL DEFAULT FALSE,
    -- โปรไฟล์สาธารณะ : คนอื่น (ผู้จัดงาน) จะเห็นนักแสดงก็ต่อเมื่อ is_public = 1
    --   ตั้งเป็น 1 ได้เมื่อนักแสดงใส่ข้อมูลแล้ว (มีแท็กทักษะหรือผลงานอย่างน้อย 1 อย่าง) ตรวจใน queries.py
    --   ถ้าลบทักษะ/ผลงานจนหมด ระบบจะตั้งกลับเป็น 0 เอง
    bio                VARCHAR(500)  NULL,
    is_public          BOOLEAN       NOT NULL DEFAULT FALSE,
    CONSTRAINT ck_actor_gender CHECK (gender IN ('Male','Female','Other')),
    CONSTRAINT ck_actor_status CHECK (actor_status IN ('Active','Inactive')),
    CONSTRAINT ck_actor_height CHECK (height_cm BETWEEN 100 AND 230),
    CONSTRAINT ck_actor_weight CHECK (weight_kg BETWEEN 25 AND 250),
    CONSTRAINT ck_actor_bust   CHECK (bust_chest_cm BETWEEN 40 AND 200),
    CONSTRAINT ck_actor_waist  CHECK (waist_cm BETWEEN 40 AND 200),
    CONSTRAINT ck_actor_hip    CHECK (hip_cm BETWEEN 40 AND 200),
    CONSTRAINT ck_actor_shoe   CHECK (shoe_size_eu BETWEEN 30 AND 50),
    CONSTRAINT ck_actor_cloth  CHECK (clothing_size IN ('XS','S','M','L','XL','XXL')),
    CONSTRAINT ck_actor_body   CHECK (body_type IN ('Slim','Athletic','Average','Curvy','Plus_Size','Muscular')),
    CONSTRAINT ck_actor_skin   CHECK (skin_tone IN ('Fair','Light','Medium','Tan','Deep')),
    CONSTRAINT ck_actor_hcolor CHECK (hair_color IN ('Black','Dark_Brown','Brown','Light_Brown','Blonde','Red','Gray','Dyed')),
    CONSTRAINT ck_actor_hlen   CHECK (hair_length IN ('Shaved','Short','Medium','Long')),
    CONSTRAINT ck_actor_htex   CHECK (hair_texture IN ('Straight','Wavy','Curly')),
    CONSTRAINT ck_actor_eye    CHECK (eye_color IN ('Black','Dark_Brown','Brown','Hazel','Green','Blue','Gray')),
    CONSTRAINT ck_actor_exp    CHECK (experience_level IN ('Beginner','Intermediate','Professional'))
) ENGINE=InnoDB;

-- 3) SKILL -------------------------------------------------------------
CREATE TABLE SKILL (
    skill_id    INT AUTO_INCREMENT PRIMARY KEY,
    skill_name  VARCHAR(80) NOT NULL,
    skill_type  VARCHAR(30) NOT NULL,   -- Language / Performance / Modeling / Physical / Other
    CONSTRAINT ck_skill_type CHECK (skill_type IN ('Language','Performance','Modeling','Physical','Other'))
) ENGINE=InnoDB;

-- 4) ACTOR_SKILL (ตารางกลางของ HAS_SKILL : Actor M:N Skill) ------------
CREATE TABLE ACTOR_SKILL (
    actor_id  INT NOT NULL,
    skill_id  INT NOT NULL,
    PRIMARY KEY (actor_id, skill_id),
    CONSTRAINT fk_as_actor FOREIGN KEY (actor_id) REFERENCES ACTOR(actor_id),
    CONSTRAINT fk_as_skill FOREIGN KEY (skill_id) REFERENCES SKILL(skill_id)
) ENGINE=InnoDB;

-- 5) ROLE (บทบาท) ------------------------------------------------------
--   CASTING   : PROJECT (0,N) --- ROLE (1,1)  => ROLE มี project_id (NOT NULL)
--   ACTED_BY  : ROLE (1,1) --- ACTOR (0,N)    => ROLE มี actor_id   (NOT NULL)
CREATE TABLE `ROLE` (
    role_id      INT AUTO_INCREMENT PRIMARY KEY,
    role_name    VARCHAR(120) NOT NULL,
    agreed_fee   DECIMAL(10,2) NOT NULL,
    role_status  VARCHAR(30)  NOT NULL DEFAULT 'Selected',
    actor_id     INT NOT NULL,
    project_id   INT NOT NULL,
    CONSTRAINT ck_role_fee CHECK (agreed_fee > 0),
    CONSTRAINT ck_role_status
        CHECK (role_status IN ('Selected','Confirmed','Rejected_by_Actor','Cancelled_by_Organizer')),
    CONSTRAINT fk_role_actor   FOREIGN KEY (actor_id)   REFERENCES ACTOR(actor_id),
    CONSTRAINT fk_role_project FOREIGN KEY (project_id) REFERENCES PROJECT(project_id)
) ENGINE=InnoDB;

-- 6) ROLE_SKILL (ตารางกลางของ REQUIRES_SKILL : Role M:N Skill) ----------
CREATE TABLE ROLE_SKILL (
    role_id   INT NOT NULL,
    skill_id  INT NOT NULL,
    PRIMARY KEY (role_id, skill_id),
    CONSTRAINT fk_rs_role  FOREIGN KEY (role_id)  REFERENCES `ROLE`(role_id),
    CONSTRAINT fk_rs_skill FOREIGN KEY (skill_id) REFERENCES SKILL(skill_id)
) ENGINE=InnoDB;

-- 7) SCHEDULE   HAS_SCHEDULE : ROLE (0,N) --- SCHEDULE (1,1) ------------
CREATE TABLE SCHEDULE (
    schedule_id  INT AUTO_INCREMENT PRIMARY KEY,
    event_type   VARCHAR(20) NOT NULL,   -- Shoot(ถ่ายทำ) / Fitting(ฟิตติ้ง) / Rehearsal(ซ้อม)
    event_date   DATE NOT NULL,
    start_time   TIME NOT NULL,
    end_time     TIME NOT NULL,
    role_id      INT  NOT NULL,
    CONSTRAINT ck_sched_type CHECK (event_type IN ('Shoot','Fitting','Rehearsal')),
    CONSTRAINT ck_sched_time CHECK (end_time > start_time),
    CONSTRAINT fk_sched_role FOREIGN KEY (role_id) REFERENCES `ROLE`(role_id),
    INDEX idx_sched_date (event_date)
) ENGINE=InnoDB;

-- 8) PAYMENT_INSTALLMENT   HAS_PAYMENT : ROLE (1,N) --- PAYMENT (1,1) ----
CREATE TABLE PAYMENT_INSTALLMENT (
    payment_id      INT AUTO_INCREMENT PRIMARY KEY,
    amount          DECIMAL(10,2) NOT NULL,
    payment_status  VARCHAR(10)   NOT NULL DEFAULT 'Pending',
    due_date        DATE NOT NULL,
    role_id         INT  NOT NULL,
    CONSTRAINT ck_pay_amount CHECK (amount > 0),
    CONSTRAINT ck_pay_status CHECK (payment_status IN ('Pending','Paid','Cancelled')),
    CONSTRAINT fk_pay_role FOREIGN KEY (role_id) REFERENCES `ROLE`(role_id)
) ENGINE=InnoDB;

-- 9) PORTFOLIO (ผลงานของนักแสดง)   HAS_WORK : ACTOR (1,1) --- PORTFOLIO (0,N) ------
--   นักแสดงเพิ่ม/ลบเองได้ ลบนักแสดงแล้วผลงานหายตาม (ON DELETE CASCADE)
--   ใช้ตาราง (ไม่ใช่เก็บเป็นข้อความก้อนเดียวใน ACTOR) เพราะนักแสดง 1 คนมีผลงานได้หลายชิ้น (1NF)
CREATE TABLE PORTFOLIO (
    work_id      INT AUTO_INCREMENT PRIMARY KEY,
    title        VARCHAR(150) NOT NULL,
    work_type    VARCHAR(12)  NOT NULL,   -- Film / Series / Commercial / Runway / Photoshoot / Music_Video / Stage / Online / Other
    role_played  VARCHAR(100) NULL,
    work_year    SMALLINT     NOT NULL,
    description  VARCHAR(500) NULL,
    link_url     VARCHAR(300) NULL,       -- ลิงก์ผลงาน (ต้องขึ้นต้น http:// หรือ https://)
    actor_id     INT NOT NULL,
    CONSTRAINT ck_work_type CHECK (work_type IN
        ('Film','Series','Commercial','Runway','Photoshoot','Music_Video','Stage','Online','Other')),
    CONSTRAINT ck_work_year CHECK (work_year BETWEEN 1980 AND 2100),
    CONSTRAINT fk_work_actor FOREIGN KEY (actor_id) REFERENCES ACTOR(actor_id) ON DELETE CASCADE,
    INDEX idx_work_actor (actor_id)
) ENGINE=InnoDB;
