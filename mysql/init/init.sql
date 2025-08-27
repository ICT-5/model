-- ========================
-- 👤 User (사용자 정보)
-- 회원가입/로그인한 사람의 정보 저장
-- ========================
CREATE TABLE `user` (
`id` INT NOT NULL AUTO_INCREMENT, -- 유저 번호 (자동 증가, PK)
`email` VARCHAR(255), -- 이메일
`username` VARCHAR(255), -- 닉네임
`provider` VARCHAR(255), -- 로그인 제공자 (google, kakao 등)
`providerId` VARCHAR(255), -- 소셜 로그인 ID
`createDate` DATETIME, -- 가입 날짜
`job_title` VARCHAR(255), -- 직무 (예: 백엔드 개발자)
`education_career` TEXT, -- 학력/경력 요약
`tech_stack` TEXT, -- 기술 스택 (예: Java, Spring)
`Field` VARCHAR(255), -- 관심 분야
PRIMARY KEY (`id`), -- PK: 유저 고유 번호
KEY `idx_user_email` (`email`), -- 이메일 검색 인덱스
UNIQUE KEY `uq_provider_providerId` (`provider`,`providerId`) -- 소셜로그인 중복 방지
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ========================
-- 📄 Resume (이력서 / 채용공고)
-- 유저가 업로드한 파일 관리
-- ========================
CREATE TABLE `resume` (
`resume_id` INT NOT NULL AUTO_INCREMENT, -- 이력서 번호 (PK)
`id` INT, -- [User.id](http://user.id/) (FK)
`file_name` VARCHAR(255), -- 이력서 파일 이름
`file_path` VARCHAR(255), -- 이력서 파일 경로
`updated_at` DATETIME, -- 수정 시간
`jobfile_name` VARCHAR(255), -- 채용공고 파일 이름
`jobfile_path` VARCHAR(255), -- 채용공고 파일 경로
PRIMARY KEY (`resume_id`),
KEY `idx_resume_user` (`id`),
CONSTRAINT `fk_resume_user` FOREIGN KEY (`id`)
REFERENCES `User`(`id`) -- User 테이블과 연결
ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ========================
-- 🎭 Persona (면접관 스타일)
-- 면접관의 말투/성격 저장
-- ========================
CREATE TABLE `persona` (
`persona_id` INT NOT NULL AUTO_INCREMENT, -- PK
`category` VARCHAR(255), -- 카테고리 (예: 인성, 기술)
`style` VARCHAR(255), -- 스타일 (예: 친절, 압박, 냉철)
`prompt_text` TEXT, -- AI가 이 스타일을 따라하도록 하는 지침 문장
PRIMARY KEY (`persona_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ========================
-- 📚 RAG Chunk (검색용 문장 조각)
-- 이력서/채용공고 내용을 문장 단위로 저장
-- ========================
CREATE TABLE `rag_chunk` (
`rag_id` INT NOT NULL AUTO_INCREMENT PRIMARY KEY, -- PK
`user_id` INT NOT NULL, -- [User.id](http://user.id/) (FK)
`source` VARCHAR(32) NOT NULL, -- 데이터 출처 (RESUME / POSTING)
`file_path` VARCHAR(255), -- 원본 파일 경로
`content` TEXT NOT NULL, -- 문장 내용
`embedding_json` JSON NOT NULL, -- AI 벡터 데이터
`created_at` DATETIME DEFAULT CURRENT_TIMESTAMP, -- 저장된 시간
`content_hash` CHAR(32) GENERATED ALWAYS AS (MD5(`content`)) VIRTUAL, -- 중복 방지용 해시
KEY `idx_rag_user` (`user_id`),
CONSTRAINT `fk_rag_user` FOREIGN KEY (`user_id`)
REFERENCES `User`(`id`) -- User와 연결
ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ========================
-- ⚙️ RAG Settings (전역 프롬프트)
-- AI한테 줄 기본 지침 저장
-- ========================
CREATE TABLE `rag_settings` (
`id` INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
`name` VARCHAR(255) NOT NULL, -- 설정 이름 (고유값)
`prompt_text` TEXT NULL, -- 프롬프트 내용
`updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP
ON UPDATE CURRENT_TIMESTAMP, -- 수정 시 자동 갱신
UNIQUE KEY `uq_rag_settings_name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ========================
-- ❓ Question (질문 목록)
-- 면접 질문들을 저장하는 테이블
-- ========================

CREATE TABLE question (
question_id BIGINT AUTO_INCREMENT PRIMARY KEY,
content VARCHAR(700) NOT NULL,
category VARCHAR(50),
interview_type VARCHAR(20),
keywords VARCHAR(255),
parent_id BIGINT,
source VARCHAR(20) NOT NULL,
CONSTRAINT uq_question UNIQUE (content(255), interview_type, category),
CONSTRAINT fk_parent_question FOREIGN KEY (parent_id)
REFERENCES question(question_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ========================
-- 🗂️ Simulation Session (면접 세션)
-- "한 판"의 면접 기록
-- ========================
CREATE TABLE `simulation_session` (
`session_id` BIGINT AUTO_INCREMENT PRIMARY KEY,
`user_id` INT NOT NULL, -- [User.id](http://user.id/) (FK)
`persona_id` INT NULL, -- [Persona.id](http://persona.id/) (FK)
`created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, -- 시작 시간
`status` VARCHAR(20) NOT NULL, -- 상태 (진행중/완료/중단)
`total_questions` INT NOT NULL, -- 총 질문 수
`current_step` INT DEFAULT 0, -- 현재 진행된 질문 번호
`end_reason` VARCHAR(30), -- 종료 이유 (limit_reached / user_stop)
`ended_at` TIMESTAMP, -- 종료 시간
CONSTRAINT `fk_sim_user` FOREIGN KEY (`user_id`)
REFERENCES `User`(`id`),
CONSTRAINT `fk_sim_persona` FOREIGN KEY (`persona_id`)
REFERENCES `persona`(`persona_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ========================
-- 💬 Simulation Question (세션별 질문)
-- 실제 면접에서 나온 질문 로그
-- ========================

CREATE TABLE simulation_question (
sim_question_id BIGINT AUTO_INCREMENT PRIMARY KEY,
session_id BIGINT NOT NULL,
question_id BIGINT NOT NULL,
asked_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
CONSTRAINT fk_sq_session FOREIGN KEY (session_id)
REFERENCES simulation_session(session_id),
CONSTRAINT fk_sq_question FOREIGN KEY (question_id)
REFERENCES question(question_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ========================
-- ✍️ Simulation Answer (세션별 답변)
-- 질문에 대한 유저의 답변 저장
-- ========================

CREATE TABLE simulation_answer (
answer_id BIGINT AUTO_INCREMENT PRIMARY KEY,
sim_question_id BIGINT NOT NULL,
content TEXT NOT NULL,
created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
CONSTRAINT fk_sa_sim_question FOREIGN KEY (sim_question_id)
REFERENCES simulation_question(sim_question_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 여기까지 복붙 후 번개
INSERT INTO question (content, category, interview_type, keywords, source) VALUES
-- [인성]
('자기소개를 해주세요.', '자기소개', '인성', '자기소개, 기본', 'common'),
('우리 회사(지원 직무)에 지원한 이유는 무엇인가요?', '지원동기', '인성', '지원동기, 회사', 'common'),
('본인의 장점과 단점을 말씀해주세요.', '성격', '인성', '장점, 단점', 'common'),
('가장 기억에 남는 성공 경험과 실패 경험은 무엇인가요?', '경험', '인성', '성공, 실패, 경험', 'common'),
('최근에 가장 도전적이었던 경험은 무엇인가요?', '도전', '인성', '도전, 경험', 'common'),
('스트레스를 받을 때 어떻게 대처하시나요?', '스트레스', '인성', '스트레스, 대처', 'common'),
('팀 내 갈등이 생겼을 때 어떻게 해결했나요?', '갈등해결', '인성', '팀, 갈등, 해결', 'common'),
('5년 후 / 10년 후 본인의 모습은 어떻게 그리고 있나요?', '비전', '인성', '미래, 목표', 'common'),
('이 직무를 수행하는 데 필요한 핵심 역량은 무엇이라고 생각하나요?', '역량', '인성', '핵심역량', 'common'),
('마지막으로 하고 싶은 말이 있나요?', '마무리', '인성', '마지막, 하고싶은말', 'common'),

-- [직무]
('지금까지 경험한 활동(학업, 프로젝트, 인턴, 아르바이트 등) 중에서 본인이 맡은 역할과 성과를 소개해 주세요.', '경험', '직무', '역할, 성과, 활동', 'common'),
('본인이 가장 도전적이었던 프로젝트나 과제는 무엇이며, 어떻게 해결했나요?', '프로젝트', '직무', '도전, 프로젝트, 해결', 'common'),
('실패 경험이 있다면, 그 상황과 극복 과정을 설명해 주세요.', '실패', '직무', '실패, 극복', 'common'),
('이 직무를 수행하는 데 필요한 핵심 역량은 무엇이라 생각하며, 본인은 어떻게 갖추고 있나요?', '역량', '직무', '핵심역량, 준비', 'common'),
('직무와 관련된 지식이나 기술을 어떻게 습득했고, 어떻게 활용했나요?', '학습', '직무', '지식, 기술, 활용', 'common'),
('협업 과정에서 본인이 맡은 구체적인 역할과 기여를 말해 주세요.', '협업', '직무', '협업, 역할, 기여', 'common'),
('최근에 학습하거나 익힌 새로운 기술/지식을 실제 경험에 어떻게 적용했나요?', '학습', '직무', '신기술, 적용', 'common'),
('여러 과제를 동시에 수행할 때, 우선순위를 정하고 관리했던 경험을 말해 주세요.', '과제관리', '직무', '우선순위, 관리', 'common'),
('본인의 강점이 직무 수행이나 팀의 성과에 어떻게 기여할 수 있다고 생각하나요?', '강점', '직무', '강점, 기여', 'common'),
('앞으로 이 직무에서 어떤 전문성을 더 발전시키고 싶나요?', '전문성', '직무', '전문성, 성장', 'common'),

-- [가치관]
('팀 내 갈등이 생겼을 때 어떻게 해결하셨나요?', '가치관', '가치관', '팀, 갈등, 해결', 'common'),
('예상치 못한 문제가 발생했을 때 어떻게 대처하나요?', '가치관', '가치관', '문제, 대처', 'common'),
('압박감이 큰 상황에서 성과를 낸 경험을 말해주세요.', '가치관', '가치관', '압박, 성과', 'common'),
('상사의 지시가 본인의 생각과 다를 때 어떻게 행동하시나요?', '가치관', '가치관', '상사, 지시, 대응', 'common'),
('업무와 개인 생활의 균형을 어떻게 유지하시나요?', '가치관', '가치관', '워크라이프밸런스', 'common'),
('새로운 환경이나 변화에 적응했던 경험이 있나요?', '가치관', '가치관', '환경, 변화, 적응', 'common'),
('직장에서 가장 중요한 가치(예: 신뢰, 책임, 성과)는 무엇이라 생각하나요?', '가치관', '가치관', '신뢰, 책임, 성과', 'common'),
('동료의 성과가 본인보다 뛰어날 때 어떻게 반응하나요?', '가치관', '가치관', '동료, 성과, 반응', 'common'),
('어려운 목표를 달성하기 위해 어떤 전략을 사용했나요?', '가치관', '가치관', '목표, 전략', 'common'),
('본인이 조직에 기여할 수 있는 가장 큰 가치는 무엇이라 생각하시나요?', '가치관', '가치관', '조직, 기여, 가치', 'common');