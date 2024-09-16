from sqlite3 import Connection
from typing import List
from htmxpy.models import Post, Posts, UserHashed, UserHashedIndex, Like
import logging

logger = logging.getLogger("logger")


def get_posts(connection: Connection, limit: int = 10, page: int = 0) -> Posts:
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
                )
                SELECT p.post_id post_id,post_title, post_text,user_id,num_likes
                FROM post_page p
                LEFT JOIN like_count l
                USING (post_id);
            '''
        cur = cur.execute(q, {"limit": limit, "offset": offset})
        # for c in cur.fetchall():
        #     print(Post.model_validate(dict(c)))
        return Posts(posts=[Post.model_validate(dict(c)) for c in cur])


def get_post(connection: Connection, post_id: int) -> Post:
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
                )
                SELECT p.post_id post_id,post_title, post_text,user_id,num_likes
                FROM post_page p
                LEFT JOIN like_count l
                USING (post_id);
            '''
        cur = cur.execute(q, {"post_id": post_id})
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

    # if __name__ == "__main__":
    #     test_post = Post(text="This is just for test", title="Test", user_id=3)
    #     insert_post(connection, test_post)
    #     print(get_posts(connection))
