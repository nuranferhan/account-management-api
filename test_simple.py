from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "HELLO WORLD - Flask is working!"

@app.route('/test')
def test():
    return "Test endpoint works!"

if __name__ == '__main__':
    print("=== Starting Flask app ===")
    app.run(debug=True, host='127.0.0.1', port=5000)

