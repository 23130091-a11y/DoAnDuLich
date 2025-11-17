from flask import Flask, render_template, request

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')  # Gọi HTML giao diện chính

@app.route('/result', methods=['POST'])
def result():
    name = request.form['name']
    return render_template('result.html', name=name)

if __name__ == '__main__':
    app.run(debug=True)