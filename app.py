from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from sqlite3 import Connection, Row
from htmxpy.db import get_posts, insert_post
from htmxpy.models import Post, Posts, UserPost
from fastapi.templating import Jinja2Templates

app = FastAPI()
connection = Connection('social.db', check_same_thread=False)
connection.row_factory = Row
templates = Jinja2Templates(directory="templates")
uid = 1


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    # posts = get_posts(connection=connection)
    return templates.TemplateResponse(
        request=request, name="index.html", context={}
    )


@app.get("/posts")
async def get_all_posts(request: Request) -> HTMLResponse:
    posts = get_posts(connection=connection)
    return templates.TemplateResponse(
        request=request, name="posts.html", context=posts.model_dump()
    )


@app.post("/posts")
async def add_post(post: UserPost, request: Request) -> HTMLResponse:
    post_dict = post.model_dump()
    print(post_dict)
    post = Post(user_id=uid, **post_dict)
    insert_post(connection, post)
    posts = get_posts(connection=connection)
    return templates.TemplateResponse(
        request=request, name="posts.html", context=posts.model_dump()
    )
