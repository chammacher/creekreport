from flask import Flask, flash, render_template, request, redirect, url_for
import sqlite3 as sql
import os
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = '/uploads/'
ALLOWED_EXTENSIONS = set(['txt'])

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


@app.route('/')
def home():
    con = sql.connect("CreekList")
    con.row_factory = sql.Row
    cur = con.cursor()

    q = request.args.get('q', type=str)

    if q is not None:
        q = '%' + q + '%'
        cur.execute("SELECT COUNT(*) from CREEKLIST where NAME like ?", (q,))
        count = cur.fetchone()[0]
        cur.execute("select * from CREEKLIST where NAME like ? limit 1000", (q,))

    else:
        cur.execute("SELECT COUNT(*) from CREEKLIST")
        count = cur.fetchone()[0]
        cur.execute("select * from CREEKLIST limit 1000")

    rows = cur.fetchall()
    return render_template('home.html', rows=rows, count=count, q=q)


@app.route('/comic/<int:cid>')
def comic(name):
    con = sql.connect("CreekList")
    con.row_factory = sql.Row
    cur = con.cursor()

    cur.execute("select * from CREEKLIST where NAME = ?", (name,))
    row = cur.fetchone()
    return render_template('comic.html', row=row)


@app.route('/add')
def add_comic():
    return render_template('add_comic.html')


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


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
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return redirect(url_for('uploaded_file',
                                    filename=filename))
    return

@app.route('/submit', methods=['POST'])
def submit_add_comic():
    try:
        name = request.form['name']
        creek_id = request.form['creek_id']
        picture = request.form['picture']
        date = request.form['date']

        with sql.connect("CreekList") as con:
            cur = con.cursor()
            cur.execute("INSERT INTO INFO VALUES (?,?,?,?,?)", (None, name, creek_id, picture, date))
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
