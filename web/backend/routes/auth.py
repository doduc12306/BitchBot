import functools
import os
from quart import session, redirect, request, jsonify
from requests_oauthlib import OAuth2Session
import asyncio
import util
import keys

OAUTH2_CLIENT_ID = keys.client_id
OAUTH2_CLIENT_SECRET = keys.client_secret
OAUTH2_REDIRECT_URI = keys.redirect_uri

API_BASE_URL = 'https://discordapp.com/api'
AUTHORIZATION_BASE_URL = API_BASE_URL + '/oauth2/authorize'
TOKEN_URL = API_BASE_URL + '/oauth2/token'

app = util.BlueprintWithBot('discord_oauth_login', __name__, url_prefix='/api/auth')

if 'http://' in OAUTH2_REDIRECT_URI:
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = 'true'


def token_updater(token):
    session['oauth2_token'] = token


def make_session(token=None, state=None, scopes=None):
    return OAuth2Session(
        client_id=OAUTH2_CLIENT_ID,
        token=token,
        state=state,
        scope=scopes,
        redirect_uri=OAUTH2_REDIRECT_URI,
        auto_refresh_kwargs={
            'client_id': OAUTH2_CLIENT_ID,
            'client_secret': OAUTH2_CLIENT_SECRET,
        },
        auto_refresh_url=TOKEN_URL,
        token_updater=token_updater,
    )


@app.route('/login')
async def index():
    discord = make_session(scopes='identify guilds')
    authorization_url, state = discord.authorization_url(AUTHORIZATION_BASE_URL)
    session['oauth2_state'] = state
    url = authorization_url + '&prompt=none'
    print(url)
    return jsonify(url=url)


async def run_in_executor(partial_func):
    return await asyncio.get_event_loop().run_in_executor(None, partial_func)


@app.route('/callback')
async def callback():
    if (await request.values).get('error'):
        return request.values['error']
    discord = make_session(state=session.get('oauth2_state'))

    token = await run_in_executor(
        functools.partial(
            discord.fetch_token,
            TOKEN_URL,
            client_secret=OAUTH2_CLIENT_SECRET,
            authorization_response=request.url
        )
    )
    session['oauth2_token'] = token
    return redirect(keys.redirect_after_login_url)


@app.route('/me')
async def me():
    discord = make_session(token=session.get('oauth2_token'))
    user = (await run_in_executor(functools.partial(discord.get, API_BASE_URL + '/users/@me'))).json()
    app.bot.get_user(int(user['id']))
    return jsonify(user=user)


@app.route('/guilds')
async def guilds():
    discord = make_session(token=session.get('oauth2_token'))
    guilds_ = (await run_in_executor(functools.partial(discord.get, API_BASE_URL + '/users/@me/guilds'))).json()
    return jsonify(guilds=guilds_)


def setup(bot):
    bot.quart_app.register_blueprint_with_bot(app, bot)