import script
import auth

from os import access
from django.shortcuts import redirect
from fastapi import FastAPI, Request, status
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from fastapi.encoders import jsonable_encoder
from config import config
from starlette.middleware.sessions import SessionMiddleware

app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")
app.add_middleware(SessionMiddleware, secret_key=config['session_middleware_key'])

@app.get("/")
def home(request: Request):
    return templates.TemplateResponse('index.html', {'request': request})

@app.get("/login")
def login(request: Request):
    access_token = request.session.get("access_token")
    #refresh_token = request.session.get("refresh_token")
    callback_url = auth.spotify_auth(config)
    if access_token is None:
        return RedirectResponse(callback_url, status_code=status.HTTP_303_SEE_OTHER)    
    else:
        return templates.TemplateResponse('query.html', {'request': request})
    
@app.get("/callback")
def callback(request: Request, code: str):
    access_token = str(auth.get_token(config, code)['access_token'])
    refresh_token = str(auth.get_token(config, code)['refresh_token'])
    request.session['access_token'] = access_token
    request.session['refresh_token'] = refresh_token

    return templates.TemplateResponse('query.html', {'request': request})


@app.get("/query")
def query(request: Request):
    access_token = request.session.get("access_token")
    refresh_token = request.session.get("refresh_token")

    if access_token is None:
        return templates.TemplateResponse('index.html', {'request': request})
    if auth.check_if_token_is_expired:
        access_token = auth.refresh_token(config, refresh_token)
        request.session['access_token'] = access_token

    return templates.TemplateResponse('query.html', {'request': request})

@app.post("/query")
async def query(request: Request):
    data = await request.form()
    data = jsonable_encoder(data)
    url = str(data['nts_url'])

    access_token = request.session.get("access_token")
    refresh_token = request.session.get("refresh_token")
    
    if access_token is None:
        return templates.TemplateResponse('index.html', {'request': request})
    
    if auth.check_if_token_is_expired:
        access_token = auth.refresh_token(config, refresh_token)
        request.session['access_token'] = access_token

    access_token = request.session.get("access_token")['access_token']

    status_message = script.create_new_spotify_playlist_and_add_tracks(url, access_token)

    return templates.TemplateResponse('query.html', {'request': request, 'message': status_message})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)