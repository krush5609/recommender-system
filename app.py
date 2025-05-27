from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import pickle
import numpy as np

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Dummy user storage
users = {'admin': 'password'}

# Load models
movies_df = pickle.load(open('model/movies_list.pkl', 'rb'))
movie_similarity = pickle.load(open('model/similarity.pkl', 'rb'))
pt = pickle.load(open('model/pt.pkl', 'rb'))
book_similarity = pickle.load(open('model/book_similarity.pkl', 'rb'))

# Login required decorator
def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if users.get(username) == password:
            session['username'] = username
            return redirect(url_for('index'))
        return render_template('login.html', error="Invalid credentials")
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in users:
            return render_template('register.html', error="Username already exists")
        users[username] = password
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/recommend_movie', methods=['POST'])
@login_required
def recommend_movie():
    data = request.json
    movie = data['movie']
    try:
        index = movies_df[movies_df['title'] == movie].index[0]
        distances = movie_similarity[index]
        movie_list = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[1:6]
        results = [movies_df.iloc[i[0]].title for i in movie_list]
        return jsonify(results)
    except:
        return jsonify(['Movie not found'])

@app.route('/recommend_book', methods=['POST'])
@login_required
def recommend_book():
    data = request.json
    book = data['book']
    try:
        index = np.where(pt.index == book)[0][0]
        similar = sorted(list(enumerate(book_similarity[index])), key=lambda x: x[1], reverse=True)[1:6]
        results = [pt.index[i[0]] for i in similar]
        return jsonify(results)
    except:
        return jsonify(['Book not found'])

@app.route('/suggest_movie')
@login_required
def suggest_movie():
    query = request.args.get('q', '').lower()
    suggestions = movies_df[movies_df['title'].str.lower().str.startswith(query)]['title'].unique().tolist()
    return jsonify(suggestions[:5])

@app.route('/suggest_book')
@login_required
def suggest_book():
    query = request.args.get('q', '').lower()
    suggestions = [title for title in pt.index if title.lower().startswith(query)]
    return jsonify(suggestions[:5])

if __name__ == '__main__':
    app.run(debug=True)
