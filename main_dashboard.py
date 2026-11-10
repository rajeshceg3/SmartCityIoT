import os

from flask import Flask, render_template, url_for
from traffic_management.api import traffic_bp
from energy_management.api import energy_bp
from citizen_reporting.api import citizen_bp
from waste_management.api import waste_bp

app = Flask(__name__)

# Register the blueprints
app.register_blueprint(traffic_bp, url_prefix='/traffic')
app.register_blueprint(energy_bp, url_prefix='/energy')
app.register_blueprint(citizen_bp)
app.register_blueprint(waste_bp)

@app.route('/')
def home():
    return render_template('home.html')

if __name__ == '__main__':
    app.run(debug=True, port=int(os.environ.get('PORT', 5005)))
