from flask import Flask, render_template, redirect, request, session, flash
from flask_bcrypt import Bcrypt
from mysqlconnection import connectToMySQL
import re
app = Flask(__name__)
app.secret_key = "98hf8egiuewbiewu9fbue9"
mysql = connectToMySQL('wall-db')
bcrypt = Bcrypt(app)
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')
print('\n= = = = = server start = = = = =')


@app.route('/')
def index():
    return render_template('index.html')


# ####################### LOG IN ##############################
@app.route('/login', methods=['post'])
def login():
    debugHelp("LOGIN")
    # email valid
    if len(request.form['email']) < 1:
        flash("Email cannot be blank!", 'login')
    elif not EMAIL_REGEX.match(request.form['email']):
        flash("Invalid Email Address!", 'login')    

    data = {
        'email': request.form['email']
    } # check if email exists
    query = "SELECT * FROM users WHERE email=%(email)s;"
    result = mysql.query_db(query, data)
    # that ^ ^ ^ checks to see if email is in db
    print('@@@@@@@@@@@@ result ===> ', result)
    # If results from query comes back is true then match passwords and continue
    if result and bcrypt.check_password_hash(result[0]['password'], request.form['password']):
        session['user_id'] = result[0]['id']
        session['name'] = result[0]['name']
        return redirect('/wall')
    else:
        flash('invalid credentials', 'login')

    if '_flashes' in session.keys():
        return redirect('/')


# ####################### REGISTER #########################
@app.route('/register', methods=['post'])
def register():
    debugHelp("REGISTER")
    # email valid
    if len(request.form['name']) < 3 :
        flash('name must have at least 3 characters', 'register')
    if request.form['name'].isalpha() == False:
        flash('name must have letters only', 'register')

    if len(request.form['email']) < 1:
        flash("Email cannot be blank!", 'register')
    elif not EMAIL_REGEX.match(request.form['email']):
        flash("Invalid Email Address!", 'register')    

    data = {
        'email': request.form['email']
    }
    query = "SELECT email FROM users WHERE email=%(email)s;"
    result = mysql.query_db(query, data)
    if result:
        flash('cannot use this email', 'register')
    print('=========== print result query ==> ', result)
    
    if len(request.form['password']) < 3:
        flash('password must have at least 3 characters', 'register')
    if request.form['password'] != request.form['password_confirm']:
        flash('passwords must match', 'register')
    
    # final validations
    if '_flashes' in session.keys():
        return redirect('/')
    else:
        pw_hash = bcrypt.generate_password_hash(request.form['password'])
        data_insert = {
            'name': request.form['name'],
            'email': request.form['email'],
            'password': pw_hash
        }
        query_insert = "INSERT INTO users(name, email, password, created_at, updated_at) VALUES(%(name)s, %(email)s, %(password)s, NOW(), NOW());"
        mysql.query_db(query_insert, data_insert)

        session['name'] = request.form['name']
        session['email'] = request.form['email']

        data_retreive_id ={
            'email': request.form['email']
        }
        query_retreive_id = "SELECT id FROM users WHERE email=%(email)s;"
        result_retreive_id = mysql.query_db(query_retreive_id, data_retreive_id)
        # print('\n\n========= result_retreive_id ==>', result_retreive_id)
        session['user_id'] = result_retreive_id[0]['id']
        # print('@@@@@@@@@@@@@@ session id=====>', session['user_id'])

        return redirect('/wall')

# ##################### WALL ###########################
@app.route('/wall')
def wall():
    debugHelp("WALL")

    query_messages = "SELECT messages.id AS msg_id, users.name AS name, messages.user_id AS user_id, messages.content AS content, messages.created_at AS message_created_at FROM messages LEFT JOIN users ON users.id = messages.user_id;"
    messages = mysql.query_db(query_messages)
    print('\nMESSAGES ==========>\n', messages)

    query_comments = "SELECT comments.message_id AS comments_message_id, comments.content AS comment_content, comments.created_at AS comment_created_at FROM comments LEFT JOIN messages ON messages.id = comments.message_id;"
    comments = mysql.query_db(query_comments)
    print('\nCOMMENTS ==========>\n', comments)

    
    if 'user_id' in session:
        return render_template('wall.html', messages = messages, comments = comments)
    else:
        return redirect('/')

# ##################### POST MESSAGE ######################
@app.route('/message', methods=['post'])
def message():
    debugHelp("message")
    data = {
        'user_id': session['user_id'],
        'content': request.form['content']
    }
    query = "INSERT INTO messages(user_id, content, created_at, updated_at) VALUES(%(user_id)s, %(content)s, NOW(), NOW());"
    post_result = mysql.query_db(query,data)
    print('@@@@@@@@@@@@ post_result ====>', post_result)
    return redirect('/wall')

# ##################### COMMENT ########################
@app.route('/comment', methods=['post'])
def comment():

    data = {
        'user_id': session['user_id'],
        'message_id': request.form['msg_id'],
        'content': request.form['content']
    }
    query = "INSERT INTO comments(user_id, message_id, content, created_at, updated_at) VALUES(%(user_id)s, %(message_id)s, %(content)s, NOW(), NOW());"
    reply_result = mysql.query_db(query, data)
    print('@@@@@@@@@@@@ reply_result ====>', reply_result)

    return redirect('/wall')
    

# ##################### LOG OUT ########################
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')
   

# ############################################

def debugHelp(message=""):
    print("\n\n-------", message, "-------")
    print("REQUEST.FORM: ", request.form)
    print('SESSION: ', session)
# ############################################

if __name__ == "__main__":
    app.run(debug=True)