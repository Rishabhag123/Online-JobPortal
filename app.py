from flask import Flask, render_template, url_for, request, redirect
from flask import session
from flask_mysqldb import MySQL

app = Flask(__name__)

app.secret_key = "DBMS"

# Configure Database
app.config['MYSQL_HOST'] = "localhost"
app.config['MYSQL_USER'] = "jobportal_admin"
app.config['MYSQL_PASSWORD'] = "Rishabh@123"
app.config['MYSQL_DB'] = "jobportal"

mysql = MySQL(app)

@app.route('/', methods = ['GET', 'POST'])
def login():
    find = 0
    if request.method == 'POST':
        # retrieving the entries made in the login form
        loginDetails = request.form
        email = loginDetails['email']
        password = loginDetails['password']
        cur = mysql.connection.cursor()
        # selecting email and password attributes from jobseeker entity to check if the email and its password exists in the entity
        find = cur.execute("SELECT * FROM jobseeker WHERE (email, password) = (%s, %s) ", (email, password))
        details = cur.fetchall()
        cur.close()
    # login to home page if we find such an entry in the table or redirect to the same page
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
        # retrieving the entries made in the signup form
        userDetails = request.form
        fname = userDetails['fname']
        lname = userDetails['lname']
        phone_num = userDetails['phone_num']
        address = userDetails['address']
        email = userDetails['email']
        password = userDetails['password']
        cpassword = userDetails['cpassword']
        # checking if the password entered in both the fields are same
        if password == cpassword:
            cur = mysql.connection.cursor()
            # creating a record by inserting the jobseeker details in jobseeker entity
            cur.execute("INSERT INTO jobseeker(first_name, last_name, phone_number, address, email, password) VALUES (%s, %s, %s, %s, %s, %s)",
            (fname, lname, phone_num, address, email, password))
            mysql.connection.commit()
            cur.close()
            # go to login page on submit
            return redirect('/')
        else:
            return redirect('signup')
    return render_template('signup.html')

@app.route('/home', methods = ['GET', 'POST'])
def home():
    if "user" in session:
        user = session["user"]
        cur = mysql.connection.cursor()
        # selecting jobseeker details to display the name of the jobseeker on the home page who is currently logged in
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
        # displaying the job details and corresponding company details of the jobs the user has applied for by using INNER JOIN on 
        # job and company tables and using subquery for selecting jobs user has applied for from the apply table 
        cur.execute("SELECT job.job_title, job.job_type, company.name, company.location, job.job_salary, \
        job.job_id FROM job INNER JOIN company ON job.company_id = company.company_id WHERE job.job_id in (SELECT job_id FROM apply WHERE \
        jobseeker_id = {})".format(user))
        applied_jobs = cur.fetchall()
        cur.close()
        cur2 = mysql.connection.cursor()
        # selecting all the profile details of the user from profile table to display in the My Profile section
        cur2.execute("SELECT * FROM profile WHERE jobseeker_id = {}".format(user))
        profile_details = cur2.fetchall()
        if profile_details:
            profile_details = profile_details[-1]
        # selecting the resume details of the user from resume table
        cur2.execute("SELECT * FROM resume WHERE jobseeker_id = {}".format(user))
        resume_details = cur2.fetchall()
        if resume_details:
            resume_details = resume_details[-1]
        cur2.close()
        return render_template('profile.html', applied_jobs = applied_jobs, profile_details = profile_details, resume_details = resume_details)
    else:
        return redirect(url_for('login'))

@app.route('/manageprofile', methods = ['GET', 'POST'])
def manageprofile():
    if "user" in session:
        user = session['user']

        cur = mysql.connection.cursor()
        # selecting all profile details for the logged in user
        exist = cur.execute("SELECT * FROM profile WHERE jobseeker_id = {}".format(user))
        profile_data = cur.fetchall()

        if request.method == 'POST':
            profile = request.form
            college = profile['college']
            dept = profile['dept']
            education = profile['education']
            filename = profile['resume']
            cur = mysql.connection.cursor()
            # selecting all profile details for the logged in user
            exist = cur.execute("SELECT * FROM profile WHERE jobseeker_id = {}".format(user))
            if exist > 0:
                # If the profile entry for user exists, then update the profile details in the profile table for that entry using UPDATE clause
                cur.execute("UPDATE profile SET college = (%s), department = (%s), education = (%s) WHERE jobseeker_id = (%s)", (college, dept, education, user))
                mysql.connection.commit()
            else:
                # If the profile entry for that user doesnt exist in the profile table, then insert a record for profile details of that user
                cur.execute("INSERT INTO profile(college, department, education, jobseeker_id) VALUES (%s, %s, %s, %s)", (college, dept, education, user))
                mysql.connection.commit()
            cur.close()

            cur2 = mysql.connection.cursor()
            # selecting resume details of the user that is logged in
            res = cur2.execute("SELECT * FROM resume WHERE resume_id = {}".format(user))
            if res > 0:
                # if the resume entry exists for that user, then update the resume filename for the entry
                cur2.execute("UPDATE resume SET filename = (%s) WHERE resume_id = (%s)", (filename, user))
                mysql.connection.commit()
            else:
                # if the resume entry doesnt exist, then insert a new entry in resume table for that user with the filename
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
            # if only keyword is entered in the job search, then select those jobs where the keyword matches the job details
            # by using LIKE clause and inner join on jobs and corresponding companies 
            if keyword and (not location):
                count_search = cur.execute("SELECT job.job_title, job.job_type, company.name, company.location, job.job_salary, job.job_description, job.job_id FROM job INNER JOIN company ON job.company_id = company.company_id WHERE (job.job_title LIKE '%{}%') OR (job.job_type LIKE '%{}%') OR (job.job_description LIKE '%{}%')".format(keyword, keyword, keyword))
            # if only location is entered in the job search, then select those jobs where the keyword matches the company location
            # by using LIKE clause and inner join on jobs and corresponding companies
            elif location and (not keyword):
                count_search = cur.execute("SELECT job.job_title, job.job_type, company.name, company.location, job.job_salary, job.job_description, job.job_id FROM job INNER JOIN company ON job.company_id = company.company_id WHERE (company.location LIKE '%{}%')".format(location))
            # if keyword and location are entered in the job search, then select those jobs where the keyword matches the job details
            # and company location by using LIKE clause and inner join on jobs and corresponding companies
            elif location and keyword:
                count_search = cur.execute("SELECT job.job_title, job.job_type, company.name, company.location, job.job_salary, job.job_description, job.job_id FROM job INNER JOIN company ON job.company_id = company.company_id WHERE ((job.job_title LIKE '%{}%') OR (job.job_type LIKE '%{}%') OR (job.job_description LIKE '%{}%')) AND (company.location LIKE '%{}%')".format(keyword, keyword, keyword, location))
            else:
                count_search = 0

            jobsearch = cur.fetchall()
            return render_template('jobsearch.html', jobsearch = jobsearch)

        cur = mysql.connection.cursor()
        # display all jobs and their details by selecting all jobs of companies using inner join on job and company
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
            # select all the jobs the user has applied by using the apply relation table
            applied = cur.execute("SELECT * FROM apply WHERE (jobseeker_id, job_id) = ({}, {})".format(user, jobid))
            if applied == 0:
                # if the user has not applied for that job, then insert a record for the user in the apply table for that job
                cur.execute("INSERT INTO apply VALUES ({}, {})".format(user, jobid))
                mysql.connection.commit()
        return redirect(url_for('home'))
    else:
        return redirect(url_for('login'))

@app.route('/interviews')
def interviews():
    
    if "user" in session:
        user = session['user']
        cur = mysql.connection.cursor()
        # select all the interview details for those jobs that the user has applied for by using inner join on apply and interview's job_id
        check_apply = cur.execute('SELECT * FROM apply INNER JOIN interview ON (apply.jobseeker_id, apply.job_id) = (interview.jobseeker_id, interview.job_id) WHERE interview.jobseeker_id = {};'.format(user))
        if check_apply > 0:
            # select the interview details, its corresponding job and company details by using inner join on job, company and interview
            # and using subquery to show interview schedules for only those jobs that the jobseeker has applied for
            interview = cur.execute("SELECT interview.jobseeker_id, job.job_title, company.name, interview.date, interview.time FROM \
            job INNER JOIN company ON job.company_id = company.company_id INNER JOIN interview ON interview.job_id = job.job_id WHERE interview.jobseeker_id = {} AND \
            interview.job_id IN (SELECT apply.job_id FROM apply INNER JOIN interview ON (apply.jobseeker_id, apply.job_id) = (interview.jobseeker_id, interview.job_id) WHERE interview.jobseeker_id = {});".format(user, user))
            if interview > 0:
                schedule = cur.fetchall()
            else:
                schedule = None
        else:
            schedule = None
        return render_template('interview.html', schedule=schedule)
    else:
        return redirect(url_for('login'))

@app.route('/results')
def results():
    if "user" in session:
        user = session['user']
        cur = mysql.connection.cursor()
        # select all the results for those jobs that the user has applied for by using inner join on apply and result's job_id
        chk_apply = cur.execute('SELECT * FROM apply INNER JOIN result ON (apply.jobseeker_id, apply.job_id) = (result.jobseeker_id, result.job_id) WHERE result.jobseeker_id = {};'.format(user))
        if chk_apply > 0:
            # select the result status of the job of a company  by using inner join on job, company and result
            # and using subquery to show results for only those jobs that the jobseeker has applied for 
            r = cur.execute("SELECT result.jobseeker_id, job.job_title, company.name, company.location, result.status FROM \
            job INNER JOIN company ON job.company_id = company.company_id INNER JOIN result ON result.job_id = job.job_id WHERE result.jobseeker_id = {} AND \
            result.job_id IN (SELECT apply.job_id FROM apply INNER JOIN result ON (apply.jobseeker_id, apply.job_id) = (result.jobseeker_id, result.job_id) WHERE result.jobseeker_id = {});".format(user, user))
            if r > 0:   
                res = cur.fetchall()
            else:
                res = None
        else:
            res = None
        return render_template('results.html', res = res)
    else:
        return redirect(url_for('login'))     

@app.route('/account')
def account():
    if "user" in session:
        user = session["user"]
        cur = mysql.connection.cursor()
        # displaying all jobseeker details by selecting it from jobseeker table
        cur.execute('SELECT * FROM jobseeker WHERE jobseeker.jobseeker_id = {}'.format(user))
        acc = cur.fetchall()
        # displaying the number of jobs the jobseeker has applied for by using GROUP BY and HAVING clause 
        # along with aggregate function count()
        a = cur.execute('SELECT count(job_id) FROM apply GROUP BY jobseeker_id HAVING jobseeker_id  = {};'.format(user))
        if a > 0:
            apply = cur.fetchall()
            apply = apply[0][0]
        else:
            apply = 0
        # displaying the number of results declared for jobs that the jobseeker has applied for by using GROUP BY and HAVING clause 
        # along with aggregate function count()
        r = cur.execute('SELECT count(job_id) FROM result GROUP BY jobseeker_id HAVING jobseeker_id = {};'.format(user))
        if r > 0:
            res = cur.fetchall()
            res = res[0][0]
        else:
            res = 0
        # displaying the number of interviews scheduled for jobs that the jobseeker has applied for by using GROUP BY and HAVING clause 
        # along with aggregate function count()
        i = cur.execute('SELECT count(job_id) FROM interview GROUP BY jobseeker_id HAVING jobseeker_id = {};'.format(user))
        if i > 0:
            interview = cur.fetchall()
            interview = interview[0][0]
        else:
            interview = 0
        return render_template('account.html', acc = acc, apply = apply, res = res, interview = interview)
    else:
        return redirect(url_for("login"))

@app.route('/logout')
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug = True)