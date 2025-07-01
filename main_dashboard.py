from flask import Flask, render_template, url_for # Add url_for if not already there
from traffic_management.api import traffic_bp # Import the blueprint
from energy_management.api import app as energy_api_blueprint # Import the energy blueprint

app = Flask(__name__)

# Register the traffic management blueprint
app.register_blueprint(traffic_bp) # url_prefix='/traffic' is already defined in traffic_bp
# Register the energy management blueprint
app.register_blueprint(energy_api_blueprint, url_prefix='/energy', name='energy')

@app.route('/')
def home():
    return render_template('home.html')

if __name__ == '__main__':
    app.run(debug=True, port=5005)
