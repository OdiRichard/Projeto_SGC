import os

from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# Chave secreta: lida de variável de ambiente.
# O valor padrão serve apenas para desenvolvimento local.
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "chave-apenas-para-desenvolvimento")

# Banco SQLite salvo na pasta "instance" (sgc.db)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///sgc.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


@app.route("/")
def index():
    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True)
