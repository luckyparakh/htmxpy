from sqlite3 import Connection
from typing import List
from htmxpy.models import Post, Posts, UserHashed, UserHashedIndex, Like
import logging

logger = logging.getLogger("logger")


def get_posts(connection: Connection, user_id: int | None = None, limit: int = 10, page: int = 0) -> Posts:
    offset = limit*page
    with connection as c:
        cur = c.cursor()
        q = '''
                WITH post_page AS (
                    SELECT post_id, post_title, post_text,user_id from posts
                    LIMIT :limit
                    OFFSET :offset
                ),
                like_count AS(
                    SELECT post_id, count(*) num_likes
                    FROM likes
                    WHERE post_id IN (Select post_id from post_page)
                    GROUP BY post_id
                ),
                user_liked AS (
                    SELECT post_id, user_id
                    FROM likes
                    WHERE user_id = :user_id AND post_id IN (SELECT post_id FROM post_page)
                )
                SELECT p.post_id post_id,post_title, post_text,p.user_id user_id,num_likes, u.user_id user_liked
                FROM post_page p
                LEFT JOIN like_count l
                USING (post_id)
                LEFT JOIN user_liked u
                USING (post_id)
                ;
            '''
        q = '''
        WITH post_page AS (
    SELECT post_id, post_title, post_text, user_id
    FROM posts
    LIMIT :limit
    OFFSET :offset
),
like_count AS (
    SELECT post_id, COUNT(*) AS num_likes
    FROM likes
    WHERE post_id IN (SELECT post_id FROM post_page)
    GROUP BY post_id
),
user_liked AS (
    SELECT post_id, user_id
    FROM likes
    WHERE user_id = :user_id AND post_id IN (SELECT post_id FROM post_page)
)
SELECT p.post_id, p.post_title, p.post_text, p.user_id AS user_id,
       COALESCE(l.num_likes, 0) AS num_likes,
       CASE WHEN u.user_id IS NOT NULL THEN TRUE ELSE FALSE END AS user_liked
FROM post_page p
LEFT JOIN like_count l ON p.post_id = l.post_id
LEFT JOIN user_liked u ON p.post_id = u.post_id;

        '''
        cur = cur.execute(
            q, {"limit": limit, "offset": offset, "user_id": user_id})
        # for c in cur.fetchall():
        #     print(Post.model_validate(dict(c)))
        return Posts(posts=[Post.model_validate(dict(c)) for c in cur])


def get_post(connection: Connection, post_id: int, user_id: int) -> Post:
    with connection as c:
        cur = c.cursor()
        q = '''
                WITH post_page AS (
                    SELECT post_id, post_title, post_text,user_id from posts
                    where post_id=:post_id
                ),
                like_count AS(
                    SELECT post_id, count(*) num_likes
                    FROM likes
                    WHERE post_id =:post_id
                ),
                user_liked AS
                (SELECT post_id, user_id
                FROM likes
                WHERE user_id = :user_id AND post_id = :post_id
                )
                SELECT p.user_id AS user_id,p.post_id post_id,post_title, post_text,num_likes,
                CASE WHEN u.user_id IS NOT NULL THEN TRUE ELSE FALSE END AS user_liked
                FROM post_page p
                LEFT JOIN like_count l
                USING (post_id)
                LEFT JOIN user_liked u
                USING (post_id)
                ;
            '''
        cur = cur.execute(q, {"post_id": post_id, "user_id": user_id})
        return Post.model_validate(dict(cur.fetchone()))


def insert_post(connection: Connection, post: Post):
    with connection as c:
        cur = c.cursor()
        q = '''
                INSERT INTO posts 
                (post_title, post_text,user_id) VALUES 
                (:post_title,:post_text,:user_id)
            '''
        cur.execute(q, post.model_dump())
        c.commit()


def create_user(connection: Connection, user: UserHashed):
    try:
        with connection as c:
            cur = c.cursor()
            q = '''
                    INSERT INTO users 
                    (username, salt, hash_password) VALUES 
                    (:username,:salt,:hash_password)
                '''
            cur.execute(q, user.model_dump())
            c.commit()
            return None
    except Exception as e:
        logger.error(e)
        return e


def get_user(connection: Connection, username: str):
    with connection as c:
        cur = c.cursor()
        q = '''
                SELECT * from users 
                WHERE username = ?
            '''
        cur.execute(q, (username,))
        user = cur.fetchone()
        if user is None:
            return None
        return UserHashedIndex(**dict(user))


def add_like(connection: Connection, like: Like):
    try:
        with connection as c:
            cur = c.cursor()
            q = '''
            INSERT INTO likes (user_id,post_id)
            VALUES (:user_id,:post_id)
            '''
            cur.execute(q, like.model_dump())
            c.commit()
            return None
    except Exception as e:
        logger.error(e)
        return e


def get_like(connection: Connection, like: Like):
    with connection as c:
        cur = c.cursor()
        q = '''
            SELECT * from likes
            WHERE user_id=:user_id AND post_id=:post_id
            '''
        cur.execute(q, like.model_dump())
        return True if cur.fetchone() is not None else False

def delete_like(connection: Connection, like: Like):
    try:
        with connection as c:
            cur = c.cursor()
            q = '''
                DELETE from likes
                WHERE user_id=:user_id AND post_id=:post_id
                '''
            cur.execute(q, like.model_dump())
            c.commit()
            return None
    except Exception as e:
        logger.error(e)
        return e

    # if __name__ == "__main__":
    #     test_post = Post(text="This is just for test", title="Test", user_id=3)
    #     insert_post(connection, test_post)
    #     print(get_posts(connection))
