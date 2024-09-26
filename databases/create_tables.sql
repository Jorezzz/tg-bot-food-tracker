CREATE TABLE IF NOT EXISTS messages
(
    message_dttm TIMESTAMP NOT NULL,
    user_id BIGINT NOT NULL,
    message_id VARCHAR(32) NOT NULL,
    dish_name VARCHAR(255),
    dish_mass INTEGER,
    dish_energy INTEGER
)
PARTITION BY RANGE (EXTRACT(YEAR FROM message_dttm), EXTRACT(MONTH FROM message_dttm));

CREATE TABLE IF NOT EXISTS users
(
    registered_dttm TIMESTAMP NOT NULL DEFAULT current_timestamp,
    user_id BIGINT NOT NULL UNIQUE,
    username VARCHAR(255) NOT NULL,
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    current_energy INTEGER DEFAULT 0,
    energy_limit INTEGER DEFAULT 0,
    role VARCHAR(255) DEFAULT 'user',
    PRIMARY KEY(user_id)
);

-- CREATE TABLE IF NOT EXISTS actions
-- (
--     dttm TIMESTAMP NOT NULL DEFAULT current_timestamp,
--     user_id BIGINT NOT NULL,
--     action VARCHAR(255),
--     result VARCHAR(255),
-- );