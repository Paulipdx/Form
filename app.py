from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm             
import wtforms                   

# Initialize your app
app = Flask(__name__)

@app.get("/healthz")
def healthz():
 return "ok", 200


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        # Assume theat form was submitted
        return render_template("greet.html", name=request.form.get("name", "World"))
    else: 
        # Assume that no form was submitted, so show form
         return render_template("index.html")   
    


@app.route("/about")
def about():
    return render_template('about.html')

@app.route("/services")
def services():
    return render_template('services.html')

@app.route("/shop")
def shop():
    return render_template('shop.html')

@app.route("/contact")
def contact():
    return render_template('contact.html')



if __name__ == "__main__":
 app.run(host="0.0.0.0", port=8000, debug=True)

