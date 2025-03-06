from flask import Flask
import aiosqlite
import asyncio

def create_app():
    app = Flask(__name__)

    # Initialize database
    async def init_db():
        async with aiosqlite.connect('requests.db') as conn:
            await conn.execute('''CREATE TABLE IF NOT EXISTS requests
                         (id INTEGER PRIMARY KEY, type TEXT, input TEXT, output TEXT, timestamp DATETIME)''')
            await conn.commit()

    # Run the async init_db function
    asyncio.run(init_db())
    return app

# from flask import Flask
# from app.config import Config
# from app.routes import api_blueprint

# def create_app():
#     app = Flask(__name__)
#     app.config.from_object(Config)
#     app.register_blueprint(api_blueprint)
#     return app
