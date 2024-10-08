CREATE TABLE IF NOT EXISTS likes (
    user_id INTEGER,
    post_id INTEGER,
    PRIMARY KEY (user_id, post_id),
    FOREIGN KEY (user_id) REFERENCES users (user_id)
    ON DELETE CASCADE
    ON UPDATE CASCADE,
    FOREIGN KEY (post_id) REFERENCES posts (post_id)
    ON DELETE CASCADE
    ON UPDATE CASCADE
);