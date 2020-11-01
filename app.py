from flask import Flask, render_template, url_for, request, redirect
from flask import session
from flask_mysqldb import MySQL

app = Flask(__name__)

app.secret_key = "DBMS"

# Configure DB
app.config['MYSQL_HOST'] = "localhost"
app.config['MYSQL_USER'] = "jobportal_admin"
app.config['MYSQL_PASSWORD'] = "Rishabh@123"
app.config['MYSQL_DB'] = "jobportal"

mysql = MySQL(app)

@app.route('/', methods = ['GET', 'POST'])
def login():
    find = 0
    if request.method == 'POST':
        loginDetails = request.form
        email = loginDetails['email']
        password = loginDetails['password']
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO users(email, password) VALUES (%s, %s)", (email, password))
        mysql.connection.commit()
        find = cur.execute("SELECT * FROM jobseeker WHERE (email, password) = (%s, %s) ", (email, password))
        details = cur.fetchall()
        cur.close()
    if find != 0:
        user = details[0][0]
        session["user"] = user
        print(user)
        return redirect('/home')
    else: 
        if "user" in session:
            return redirect(url_for("home"))
        return render_template('login.html', find = find)

@app.route('/signup', methods = ['GET', 'POST'])
def signup():
    if request.method == 'POST':
        userDetails = request.form
        fname = userDetails['fname']
        lname = userDetails['lname']
        phone_num = userDetails['phone_num']
        address = userDetails['address']
        email = userDetails['email']
        password = userDetails['password']
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO jobseeker(first_name, last_name, phone_number, address, email, password) VALUES (%s, %s, %s, %s, %s, %s)",
        (fname, lname, phone_num, address, email, password))
        mysql.connection.commit()
        cur.close()
        return redirect('/')
    return render_template('signup.html')

@app.route('/home', methods = ['GET', 'POST'])
def home():
    if "user" in session:
        user = session["user"]
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM jobseeker WHERE jobseeker_id = {}".format(user))
        userdet = cur.fetchall()
        name = userdet[0][1]
        return render_template('home.html', name = name)
    else:
        return redirect(url_for('login'))

@app.route('/profile', methods = ['GET', 'POST'])
def profile():
    if "user" in session:
        user = session['user']
        cur = mysql.connection.cursor()
        cur.execute("SELECT job.job_title, job.job_type, company.name, company.location, job.job_salary, \
        job.job_id FROM job INNER JOIN company ON job.company_id = company.company_id WHERE job.job_id in (SELECT job_id FROM apply WHERE \
        jobseeker_id = {})".format(user))
        applied_jobs = cur.fetchall()
        cur.close()
        cur2 = mysql.connection.cursor()
        cur2.execute("SELECT * FROM profile WHERE jobseeker_id = {}".format(user))
        profile_details = cur2.fetchall()
        cur2.execute("SELECT * FROM resume WHERE jobseeker_id = {}".format(user))
        resume_details = cur2.fetchall()
        cur2.close()
        return render_template('profile.html', applied_jobs = applied_jobs, profile_details = profile_details[-1], resume_details = resume_details[-1])
    else:
        return redirect(url_for('login'))

@app.route('/manageprofile', methods = ['GET', 'POST'])
def manageprofile():
    if "user" in session:
        user = session['user']

        cur = mysql.connection.cursor()
        exist = cur.execute("SELECT * FROM profile WHERE jobseeker_id = {}".format(user))
        profile_data = cur.fetchall()

        if request.method == 'POST':
            profile = request.form
            college = profile['college']
            dept = profile['dept']
            education = profile['education']
            filename = profile['resume']
            cur = mysql.connection.cursor()
            exist = cur.execute("SELECT * FROM profile WHERE jobseeker_id = {}".format(user))
            if exist > 0:
                cur.execute("UPDATE profile SET college = (%s), department = (%s), education = (%s) WHERE jobseeker_id = (%s)", (college, dept, education, user))
                mysql.connection.commit()
            else:
                cur.execute("INSERT INTO profile(college, department, education, jobseeker_id) VALUES (%s, %s, %s, %s)", (college, dept, education, user))
                mysql.connection.commit()
            cur.close()

            cur2 = mysql.connection.cursor()
            res = cur2.execute("SELECT * FROM resume WHERE resume_id = {}".format(user))
            if res > 0:
                cur2.execute("UPDATE resume SET filename = (%s) WHERE resume_id = (%s)", (filename, user))
                mysql.connection.commit()
            else:
                cur2.execute("INSERT INTO resume(filename, jobseeker_id) VALUES (%s, %s)", (filename, user))
                mysql.connection.commit()
            cur2.close()
            return redirect(url_for('profile'))
        return render_template('manageprofile.html', profile_data = profile_data[-1])
    else:
        return redirect(url_for('login'))

@app.route('/jobs', methods = ['GET', 'POST'])
def jobs():
    if "user" in session:
        if request.method == 'POST':
            searchjob = request.form
            keyword = searchjob['keyword']
            location = searchjob['location']
            cur = mysql.connection.cursor() 
            if keyword and (not location):
                count_search = cur.execute("SELECT job.job_title, job.job_type, company.name, company.location, job.job_salary, job.job_description, job.job_id FROM job INNER JOIN company ON job.company_id = company.company_id WHERE (job.job_title LIKE '%{}%') OR (job.job_type LIKE '%{}%') OR (job.job_description LIKE '%{}%')".format(keyword, keyword, keyword))
            elif location and (not keyword):
                count_search = cur.execute("SELECT job.job_title, job.job_type, company.name, company.location, job.job_salary, job.job_description, job.job_id FROM job INNER JOIN company ON job.company_id = company.company_id WHERE (company.location LIKE '%{}%')".format(location))
            elif location and keyword:
                count_search = cur.execute("SELECT job.job_title, job.job_type, company.name, company.location, job.job_salary, job.job_description, job.job_id FROM job INNER JOIN company ON job.company_id = company.company_id WHERE ((job.job_title LIKE '%{}%') OR (job.job_type LIKE '%{}%') OR (job.job_description LIKE '%{}%')) AND (company.location LIKE '%{}%')".format(keyword, keyword, keyword, location))
            else:
                count_search = 0

            jobsearch = cur.fetchall()
            return render_template('jobsearch.html', jobsearch = jobsearch)

        cur = mysql.connection.cursor()
        count_jobs = cur.execute("SELECT job.job_title, job.job_type, company.name, company.location, job.job_salary, job.job_description, job.job_id FROM job INNER JOIN company ON job.company_id = company.company_id")
        if count_jobs > 0:
            alljobs = cur.fetchall()
            return render_template('jobs.html', alljobs = alljobs)
    else:
        return redirect(url_for('login'))


@app.route('/jobsearch')
def jobsearch():
    if "user" in session:
        return render_template('jobsearch.html')
    else:
        return redirect(url_for('login'))

@app.route('/apply', methods = ['GET', 'POST'])
def apply():
    if "user" in session:
        user = session['user']
        if request.method == 'POST':
            apply = request.form
            jobid = apply['j_id']
            cur = mysql.connection.cursor()
            applied = cur.execute("SELECT * FROM apply WHERE (jobseeker_id, job_id) = ({}, {})".format(user, jobid))
            if applied == 0:
                cur.execute("INSERT INTO apply VALUES ({}, {})".format(user, jobid))
                mysql.connection.commit()
        return redirect(url_for('home'))
    else:
        return redirect(url_for('login'))

@app.route('/results')
def results():
    if "user" in session:
        user = session['user']
        return render_template('results.html')
    else:
        return redirect(url_for('login'))

@app.route('/users')
def logins():
    cur = mysql.connection.cursor()
    count_users = cur.execute("SELECT * FROM users")
    if count_users > 0:
        loginDetails = cur.fetchall()
        return render_template('users.html', loginDetails = loginDetails)   

@app.route('/jobseekers')
def seekers():
    cur = mysql.connection.cursor()
    count_users = cur.execute("SELECT * FROM jobseeker")
    if count_users > 0:
        seekerDetails = cur.fetchall()
        return render_template('jobseekers.html', seekerDetails = seekerDetails)  

@app.route('/account')
def account():
    if "user" in session:
        user = session["user"]
        cur = mysql.connection.cursor()
        cur.execute('SELECT * FROM jobseeker WHERE jobseeker.jobseeker_id = {}'.format(user))
        acc = cur.fetchall()
        return render_template('account.html', acc = acc)
    else:
        return redirect(url_for("login"))
@app.route('/logout')
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug = True)