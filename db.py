from sqlite3 import Connection
from typing import List
from htmxpy.models import Post, Posts


def get_posts(connection: Connection) -> Posts:
    with connection as c:
        cur = c.cursor()
        q = '''
                SELECT post_title, post_text,user_id from posts;
            '''
        cur = cur.execute(q)
        # for c in cur.fetchall():
        #     print(Post.model_validate(dict(c)))
        return Posts(posts=[Post.model_validate(dict(c)) for c in cur])


def insert_post(connection: Connection, post: Post):
    with connection as c:
        cur = c.cursor()
        q = '''
                INSERT INTO posts 
                (post_title, post_text,user_id) VALUES 
                (:post_title,:post_text,:user_id)
            '''
        cur.execute(q, post.model_dump())


# if __name__ == "__main__":
#     test_post = Post(text="This is just for test", title="Test", user_id=3)
#     insert_post(connection, test_post)
#     print(get_posts(connection))
