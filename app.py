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

app.secret_key = b'chance'


@app.route('/')
def home():
    con = sql.connect("CreekList.db")
    con.row_factory = sql.Row
    cur = con.cursor()

    q = request.args.get('q', type=str)

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
def add_info():
    return render_template('add_info.html')


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
            flash('No file Selected')
            return redirect(url_for("add_county"))
        file = request.files['file']
        # if user does not select file, browser also
        # submit a empty part without filename
        if file.filename == '':
            flash('No file selected')
            return redirect(url_for("add_county"))
        if file and allowed_file_county(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            try:
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
                flash('Text file of wrong format')
                return redirect(url_for("add_county"))

    return redirect(url_for("add_county"))


@app.route('/submit', methods=['POST', 'GET'])
def submit_add_info():
    if request.method == 'POST':
        try:
            name = request.form['name']

            creek_id = request.form['creek_id']
            picture = ""
            date = request.form['date']
            description = request.form['description']

            with sql.connect("CreekList.db") as con:
                cur = con.cursor()
                cur.execute("Select ID from CREEKLIST WHERE name like ?", (name,))
                key = cur.fetchone()[0]
                if creek_id is '':
                    creek_id = key

                cur.execute("INSERT INTO INFO VALUES (?,?,?,?,?,?)", (None, creek_id, name, picture, date, description,))
            con.commit()
            con.close()
            return redirect(url_for("home"))
        except:
            flash('Not all fields selected')
            return redirect(url_for("add_info"))


@app.route('/search', methods=['POST', 'GET'])
def advanced_search():
    if request.method == 'POST':
        try:
            name = request.form['name']
            creek_id = request.form['creek_id']
            date = request.form['date']
            description = request.form['description']

            with sql.connect("CreekList.db") as con:
                cur = con.cursor()
                #print(cur.execute("PRAGMA table_info(INFO)").fetchall())
                cur.execute(
                    "SELECT COUNT(*) from INFO WHERE NAME like ? or DATE like ? or DESCRIPTION like ? or ID like ?",
                    (name, date, description, creek_id))
                count = cur.fetchone()[0]
                cur.execute("SELECT ID, NAME, DATE, DESCRIPTION, PICTURE from INFO WHERE NAME like ? or DATE like ? or DESCRIPTION like ? or ID like ? LIMIT 1000",
                            (name, date, description, creek_id))
            rows = cur.fetchall()
            #print(rows)
            con.commit()
            con.close()

            return render_template('info.html', rows=rows, count=count, q=None)
        except:
            flash('No such item found')
            return redirect(url_for("advanced_search"))
    return render_template('advanced_search.html')


@app.route('/search1', methods=['GET'])
def advanced_search_home():
    name = request.args.get('name')
    creek_id = request.args.get('creek_id')
    try:
        with sql.connect("CreekList.db") as con:
            cur = con.cursor()
            #print(cur.execute("PRAGMA table_info(INFO)").fetchall())
            cur.execute("SELECT COUNT(*) from INFO WHERE NAME like ? or ID like ?", (name, creek_id))
            count = cur.fetchone()[0]
            cur.execute("SELECT ID, NAME, DATE, DESCRIPTION, PICTURE from INFO WHERE NAME like ? or ID like ? LIMIT 1000",
                            (name, creek_id))
        rows = cur.fetchall()
        #print(rows)
        con.commit()
        con.close()

        return render_template('info.html', rows=rows, count=count, q=None)
    except:
        flash('No such item found')
        return redirect(url_for("home"))


if __name__ == '__main__':
    app.run(debug=True)
