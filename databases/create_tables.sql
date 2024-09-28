CREATE TABLE IF NOT EXISTS messages
(
    message_dttm TIMESTAMP NOT NULL,
    user_id BIGINT NOT NULL,
    message_id BIGINT NOT NULL,
    image TEXT,
    resonse_raw TEXT,
    PRIMARY KEY(user_id, message_id)
);

CREATE TABLE IF NOT EXISTS dishes
(
    user_id BIGINT NOT NULL,
    message_id BIGINT NOT NULL,
    dish_name VARCHAR(255),
    ingridient_name VARCHAR(255),
    ingridient_mass INTEGER,
    ingridient_energy INTEGER
);

CREATE TABLE IF NOT EXISTS daily_energy
(
    dttm_started_dttm TIMESTAMP NOT NULL,
    dttm_finished_dttm TIMESTAMP NOT NULL,
    user_id BIGINT NOT NULL,
    current_energy INTEGER DEFAULT 0,
    energy_limit INTEGER DEFAULT 0,
    PRIMARY KEY(dttm_started_dttm, user_id)
);