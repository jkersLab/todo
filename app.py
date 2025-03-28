from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)

DATABASE = 'todos.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS todos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task TEXT NOT NULL,
            description TEXT,
            status TEXT DEFAULT 'Not Started',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS subtasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            todo_id INTEGER,
            subtask TEXT,
            is_completed BOOLEAN DEFAULT 0,
            FOREIGN KEY (todo_id) REFERENCES todos(id)
        )
    ''')
    conn.commit()
    conn.close()

@app.route('/')
def index():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM todos")
    todos = cursor.fetchall()
    
    todos_list = []
    for todo in todos:
        todos_list.append(dict(todo))
    for todo in todos_list:
        cursor.execute("SELECT * FROM subtasks WHERE todo_id = ?", (todo['id'],))
        todo['subtasks'] = [dict(subtask) for subtask in cursor.fetchall()]
    cursor.execute("SELECT status, COUNT(*) FROM todos GROUP BY status")
    status_counts = cursor.fetchall()
    status_count_dict = {status: count for status, count in status_counts}
    conn.close()

    return render_template('index.html', todos=todos_list, status_counts=status_count_dict)



@app.route('/add', methods=['POST'])
def add_todo():
    task = request.form['task']
    description = request.form['description']
    status = request.form['status']

    conn = get_db()
    conn.execute("INSERT INTO todos (task, description, status) VALUES (?, ?, ?)", (task, description, status))
    conn.commit()
    conn.close()

    return redirect(url_for('index'))

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_todo(id):
    conn = get_db()
    if request.method == 'POST':
        task = request.form['task']
        description = request.form['description']
        status = request.form['status']
        conn.execute("UPDATE todos SET task = ?, description = ?, status = ? WHERE id = ?", 
                     (task, description, status, id))
        conn.commit()
        conn.close()
        return redirect(url_for('index'))
    
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM todos WHERE id = ?", (id,))
    todo = cursor.fetchone()
    cursor.execute("SELECT * FROM subtasks WHERE todo_id = ?", (id,))
    todo = dict(todo)
    todo['subtasks'] = [dict(subtask) for subtask in cursor.fetchall()]
    conn.close()
    return render_template('edit.html', todo=todo,)

@app.route('/delete/<int:id>', methods=['GET'])
def delete_todo(id):
    conn = get_db()
    conn.execute("DELETE FROM todos WHERE id = ?", (id,))
    cursor = conn.cursor()
    cursor.execute("SELECT todo_id FROM subtasks WHERE id = ?", (id,))
    todo_id = cursor.fetchone()
    
    if todo_id:
        todo_id = todo_id['todo_id'] 
    conn.execute("DELETE FROM subtasks WHERE id = ?", (id,))
    
    conn.execute("DELETE FROM subtasks WHERE todo_id = ?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/add_subtask/<int:todo_id>', methods=['POST'])
def add_subtask(todo_id):
    subtask = request.form['subtask']
    conn = get_db()
    conn.execute("INSERT INTO subtasks (todo_id, subtask) VALUES (?, ?)", (todo_id, subtask))
    conn.commit()
    conn.close()
    return redirect(url_for('edit_todo', id=todo_id))

@app.route('/toggle_subtask/<int:id>', methods=['GET'])
def toggle_subtask(id):
    conn = get_db()
    conn.execute("UPDATE subtasks SET is_completed = NOT is_completed WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/delete_subtask/<int:id>', methods=['GET'])
def delete_subtask(id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT todo_id FROM subtasks WHERE id = ?", (id,))
    todo_id = cursor.fetchone()
    
    if todo_id:
        todo_id = todo_id['todo_id'] 
    conn.execute("DELETE FROM subtasks WHERE id = ?", (id,))
    conn.commit()
    conn.close()

    return redirect(url_for('edit_todo', id=todo_id))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
