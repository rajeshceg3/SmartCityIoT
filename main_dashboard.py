from flask import Flask, render_template, url_for
from traffic_management.api import traffic_bp
from energy_management.api import energy_bp

app = Flask(__name__)

# Register the blueprints
app.register_blueprint(traffic_bp, url_prefix='/traffic')
app.register_blueprint(energy_bp, url_prefix='/energy')

@app.route('/')
def home():
    return render_template('home.html')

if __name__ == '__main__':
    app.run(debug=True, port=5005)
