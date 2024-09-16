from fastapi import FastAPI, Request, HTTPException, status, Form, Depends, Cookie
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import OAuth2, OAuth2PasswordBearer
from sqlite3 import Connection, Row
from htmxpy.db import get_posts, insert_post, create_user, get_user, add_like, get_post
from htmxpy.models import Post, UserPost, UserHashed, Like, PostID
from fastapi.templating import Jinja2Templates
from secrets import token_hex
from passlib.hash import pbkdf2_sha256
from typing import Annotated, Union
import jwt

app = FastAPI()
connection = Connection('social.db', check_same_thread=False)
connection.row_factory = Row
templates = Jinja2Templates(directory="templates")

JWT_KEY = "123456789"
EXPIRATION_TIME = 3600
ALGORITHM = "HS256"


def decrypt_access_token(access_token: str | None) -> dict[str, str | int] | None:
    if access_token is None:
        return None
    _, token = access_token.split()
    data = jwt.decode(token, JWT_KEY, [ALGORITHM])
    return data


class OAuthCookie(OAuth2):
    def __call__(self, request: Request) -> int | str | None:
        data = decrypt_access_token(request.cookies.get("access_token"))
        if data is None:
            return None
        return data["user_id"]


oauth_cookie = OAuthCookie()


@app.get("/", response_class=HTMLResponse)
async def home(request: Request, access_token: Annotated[Union[str, None], Cookie()] = None):
    # posts = get_posts(connection=connection)
    context = {}
    if access_token:
        context = {"login": True}
    return templates.TemplateResponse(
        request=request, name="index.html", context=context
    )


@app.get("/logout")
async def logout(response: RedirectResponse, access_token: Annotated[Union[str, None], Cookie()] = None) -> RedirectResponse:
    response = RedirectResponse("/login")
    response.delete_cookie("access_token")
    return response


@ app.get("/posts")
async def get_all_posts(request: Request, access_token: Annotated[Union[str, None], Cookie()] = None) -> HTMLResponse:
    user_id = None
    if access_token:
        user_id = decrypt_access_token(access_token)['user_id']
    posts = get_posts(connection=connection, user_id=user_id)
    # breakpoint()
    context = posts.model_dump()
    if access_token:
        context['login'] = True
    print(context)
    return templates.TemplateResponse(
        request=request, name="posts.html", context=context
    )


@ app.post("/posts")
async def add_post(post: UserPost, request: Request, uid: int = Depends(oauth_cookie)) -> HTMLResponse:
    post_dict = post.model_dump()
    # print(post_dict)
    post = Post(user_id=uid, **post_dict)
    insert_post(connection, post)
    context = {"post_added": True}
    return templates.TemplateResponse(
        request=request, name="add_posts.html", context=context
    )


@ app.get("/signup")
async def signup(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request=request, name="signup.html", context={})


@ app.post("/signup")
async def add_user(username: Annotated[str, Form()], password: Annotated[str, Form()], confirm_password: Annotated[str, Form()], request: Request) -> HTMLResponse:
    if password != confirm_password:
        message = "Password mismatch"
        return templates.TemplateResponse(request=request, name="signup.html", context={"message": message})
    salt = token_hex(15)
    hashed_password = pbkdf2_sha256.hash(password + salt)
    user = UserHashed(username=username, salt=salt,
                      hash_password=hashed_password)
    message = create_user(connection, user)
    if message is None:
        message = "Sign Up is successful"
        # return RedirectResponse("./login", status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse(request=request, name="signup.html", context={"message": message})


@ app.get("/login")
async def signup(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request=request, name="login.html", context={})


@ app.post("/login")
async def login(username: Annotated[str, Form()], password: Annotated[str, Form()], request: Request) -> HTMLResponse:
    user = get_user(connection, username)
    if user is None:
        return templates.TemplateResponse(request=request, name="login.html", context={"message": "User not found"})
    correct_password = pbkdf2_sha256.verify(
        password+user.salt, user.hash_password)
    if not correct_password:
        return templates.TemplateResponse(request=request, name="login.html", context={"message": "User or password not correct"})
    token = jwt.encode(
        {"username": username, "user_id": user.user_id},
        JWT_KEY,
        ALGORITHM,
    )
    response = RedirectResponse("./", status.HTTP_303_SEE_OTHER)
    response.set_cookie(
        "access_token",
        f"Bearer {token}",
        samesite="lax",
        expires=EXPIRATION_TIME,
        httponly=True,
        # set this True in production
        # secure=True,
    )
    return response


@ app.post("/like")
async def create_like(post_id: PostID, request: Request, uid: int = Depends(oauth_cookie)) -> HTMLResponse:
    like = Like(user_id=uid, post_id=post_id.post_id)
    err = add_like(connection, like)
    post = get_post(connection, post_id.post_id, uid).model_dump()
    # print(post)
    context = {"post": post, "login": True}
    return templates.TemplateResponse(request=request, name="post.html", context=context)
