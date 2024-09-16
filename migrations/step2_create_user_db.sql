CREATE TABLE users(
    user_id INTEGER PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    salt TEXT NOT NULL,
    hash_password TEXT NOT NULL
)