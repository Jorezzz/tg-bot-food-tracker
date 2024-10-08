CREATE TABLE IF NOT EXISTS messages
(
    message_dttm TIMESTAMP NOT NULL,
    user_id BIGINT NOT NULL,
    message_id BIGINT NOT NULL,
    input_text TEXT,
    image TEXT,
    resonse_raw TEXT,
    PRIMARY KEY(user_id, message_id)
);

CREATE TABLE IF NOT EXISTS users
(
    registered_dttm TIMESTAMP NOT NULL DEFAULT current_timestamp,
    user_id BIGINT NOT NULL UNIQUE,
    username VARCHAR(255),
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    current_energy BIGINT NOT NULL DEFAULT 0,
    current_proteins BIGINT NOT NULL DEFAULT 0,
    current_carbohydrates BIGINT NOT NULL DEFAULT 0,
    current_fats BIGINT NOT NULL DEFAULT 0,
    proteins_limit BIGINT NOT NULL DEFAULT 0,
    carbohydrates_limit BIGINT NOT NULL DEFAULT 0,
    fats_limit BIGINT NOT NULL DEFAULT 0,
    energy_limit BIGINT NOT NULL DEFAULT 0,
    role_id INTEGER NOT NULL DEFAULT 1,
    dttm_started_dttm TIMESTAMP NOT NULL DEFAULT current_timestamp,
    end_hour BIGINT NOT NULL DEFAULT 0,
    end_minute BIGINT NOT NULL DEFAULT 0,
    balance BIGINT NOT NULL DEFAULT 0,
    PRIMARY KEY(user_id)
);

CREATE TABLE IF NOT EXISTS dishes
(
    user_id BIGINT NOT NULL,
    message_id BIGINT NOT NULL,
    name VARCHAR(255),
    dish_id BIGINT,
    quantity INTEGER,
    callories INTEGER,
    proteins INTEGER,
    carbohydrates INTEGER,
    fats INTEGER,
    included BOOLEAN DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS daily_energy
(
    dttm_started_dttm TIMESTAMP NOT NULL,
    dttm_finished_dttm TIMESTAMP NOT NULL,
    user_id BIGINT NOT NULL,
    current_energy INTEGER DEFAULT 0,
    energy_limit INTEGER DEFAULT 0,
    current_proteins INTEGER DEFAULT 0,
    proteins_limit INTEGER DEFAULT 0,
    current_carbohydrates INTEGER DEFAULT 0,
    carbohydrates_limit INTEGER DEFAULT 0,
    current_fats INTEGER DEFAULT 0,
    fats_limit INTEGER DEFAULT 0,
    PRIMARY KEY(dttm_started_dttm, user_id)
);

CREATE TABLE IF NOT EXISTS promocodes
(
    dttm_started TIMESTAMP NOT NULL DEFAULT current_timestamp,
    name VARCHAR(255) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    quantity BIGINT NOT NULL,
    remaining_quantity BIGINT NOT NULL,
    balance_boost BIGINT NOT NULL,
    aux_property VARCHAR(255),
    PRIMARY KEY(name)
);