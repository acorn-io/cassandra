import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
from cassandra.query import SimpleStatement
from uuid import uuid4

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

DB_HOST = os.environ.get('DB_HOST')
DB_PORT = os.environ.get('DB_PORT')
DB_USER = os.environ.get('DB_USER')
DB_PASS = os.environ.get('DB_PASS')
DB_KEYSPACE = os.environ.get('DB_KEYSPACE')

# Adjusted the Cluster initialization with authentication
auth_provider = PlainTextAuthProvider(username=DB_USER, password=DB_PASS)
cluster = Cluster([f"{DB_HOST}"], auth_provider=auth_provider, port=9042)
session = cluster.connect()

# Use the specified keyspace
session.set_keyspace(DB_KEYSPACE)

# Ensure the table exists in the keyspace
create_table_query = """
    CREATE TABLE IF NOT EXISTS hits_counter (
        id TEXT PRIMARY KEY,
        count COUNTER
    )
"""
session.execute(SimpleStatement(create_table_query))

@app.get('/', response_class=HTMLResponse)
async def hello(request: Request):
    # If the counter does not exist, initialize it with a value of 0
    counter_data = session.execute("SELECT * FROM hits_counter WHERE id = %s", ("page_counter",)).one()

    if not counter_data:
        session.execute("UPDATE hits_counter SET count = count + 0 WHERE id = %s", ("page_counter",))
        counter = 0
    else:
        counter = counter_data.count

    # Increment the counter
    session.execute("UPDATE hits_counter SET count = count + 1 WHERE id = %s", ("page_counter",))
    counter += 1
    
    return templates.TemplateResponse("index.html", {"request": request, "counter": counter})
