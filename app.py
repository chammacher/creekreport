from flask import Flask, flash, render_template, request, redirect, url_for
import sqlite3 as sql
from sqlite3 import Error
import os
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = './uploads/'
ALLOWED_EXTENSIONS_COUNTY = set(['txt'])
ALLOWED_EXTENSIONS_PHOTOS = set(['png', 'jpg', 'gif', 'jpeg'])

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


@app.route('/')
def home():
    con = sql.connect("CreekList.db")
    con.row_factory = sql.Row
    cur = con.cursor()

    q = request.args.get('q', type=str)
    print(q)

    if q is not None:
        q = '%' + q + '%'
        cur.execute("SELECT COUNT(*) from CREEKLIST where name like ?", (q,))
        count = cur.fetchone()[0]
        cur.execute("select * from CREEKLIST where name like ? limit 1000", (q,))

    else:
        cur.execute("SELECT COUNT(*) from CREEKLIST")
        count = cur.fetchone()[0]
        cur.execute("select * from CREEKLIST limit 1000")

    rows = cur.fetchall()
    return render_template('home.html', rows=rows, count=count, q=q)


@app.route('/county/<int:ID>')
def county(name):
    con = sql.connect("CreekList.db")
    con.row_factory = sql.Row
    cur = con.cursor()

    cur.execute("select * from CREEKLIST where NAME = ?", (name,))
    row = cur.fetchone()
    return render_template('county.html', row=row)


@app.route('/add/photo')
def add_comic():
    return render_template('add_comic.html')


@app.route('/add/county')
def add_county():
    return render_template('add_county.html')


def allowed_file_county(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS_COUNTY


def allowed_file_photo(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS_PHOTOS


@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also
        # submit a empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file_county(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            try:
                print('made it this far')
                with sql.connect("CreekList.db") as con:
                    cur = con.cursor()
                    with open(os.path.join(app.config['UPLOAD_FOLDER'], filename)) as f:
                        for index, line in enumerate(f):
                            value_array = line.split('\t')
                            name = value_array[0]
                            start_mile = value_array[2]
                            end_mile = value_array[3]
                            cr_class = value_array[4]
                            county = value_array[5]

                            cur.execute("INSERT INTO CREEKLIST VALUES (?,?,?,?,?,?)", (None, name, start_mile, end_mile, cr_class, county))

                    con.commit()
                con.close()
                return redirect(url_for("home"))
            except Error as e:
                print(e)
                return redirect(url_for("add_county"))

    return redirect(url_for("add_county"))


@app.route('/submit', methods=['POST'])
def submit_add_comic():
    try:
        name = request.form['name']
        creek_id = request.form['creek_id']
        picture = request.form['picture']
        date = request.form['date']
        county = request.form['county']
        description = request.form['description']

        with sql.connect("CreekList.db") as con:
            cur = con.cursor()
            cur.execute("INSERT INTO INFO VALUES (?,?,?,?,?)", (None, creek_id, name, picture, date, county, description))
        con.commit()
        con.close()
        return redirect(url_for("home"))
    except:
        return redirect(url_for("add_comic"))


@app.route('/search')
def advanced_search():
    return render_template('advanced_search.html')


if __name__ == '__main__':
    app.run(debug=True)
