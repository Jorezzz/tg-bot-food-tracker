CREATE TABLE IF NOT EXISTS messages
(
    message_dttm TIMESTAMP NOT NULL,
    user_id BIGINT NOT NULL,
    message_id BIGINT NOT NULL,
    image TEXT,
    PRIMARY KEY(user_id, message_id)
);

CREATE TABLE IF NOT EXISTS dishes
(
    user_id BIGINT NOT NULL,
    message_id BIGINT NOT NULL,
    dish_name VARCHAR(255),
    ingridient_name VARCHAR(255),
    ingridient_mass INTEGER,
    ingridient_energy INTEGER,
    PRIMARY KEY(user_id, message_id)
);

-- CREATE TABLE IF NOT EXISTS users
-- (
--     registered_dttm TIMESTAMP NOT NULL DEFAULT current_timestamp,
--     user_id BIGINT NOT NULL UNIQUE,
--     username VARCHAR(255) NOT NULL,
--     first_name VARCHAR(255),
--     last_name VARCHAR(255),
--     current_energy INTEGER DEFAULT 0,
--     energy_limit INTEGER DEFAULT 0,
--     role VARCHAR(255) DEFAULT 'user',
--     dttm_started_dttm TIMESTAMP NOT NULL DEFAULT current_timestamp,
--     end_hour INTEGER DEFAULT 0,
--     end_minute INTEGER DEFAULT 0,
--     last_image_message_id BIGINT,
--     PRIMARY KEY(user_id)
-- );

CREATE TABLE IF NOT EXISTS daily_energy
(
    day_id VARCHAR(255) NOT NULL UNIQUE,
    dttm_started_dttm TIMESTAMP NOT NULL,
    dttm_finished_dttm TIMESTAMP NOT NULL,
    user_id BIGINT NOT NULL,
    current_energy INTEGER DEFAULT 0,
    energy_limit INTEGER DEFAULT 0,
    PRIMARY KEY(day_id)
);