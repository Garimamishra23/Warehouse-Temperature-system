from flask import Flask, render_template, jsonify, request
import sqlite3
from datetime import datetime, timedelta
import json

app = Flask(__name__)

def get_db_connection():
    conn = sqlite3.connect('warehouse_temperature.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def dashboard():
    return render_template('dashboard.html')

@app.route('/api/temperature/current')
def get_current_temperatures():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get latest reading for each sensor
    cursor.execute('''
        SELECT tr.sensor_id, tr.temperature, tr.location, tr.timestamp
        FROM temperature_readings tr
        INNER JOIN (
            SELECT sensor_id, MAX(timestamp) as max_timestamp
            FROM temperature_readings
            GROUP BY sensor_id
        ) latest ON tr.sensor_id = latest.sensor_id AND tr.timestamp = latest.max_timestamp
    ''')
    
    sensors = []
    for row in cursor.fetchall():
        sensors.append({
            'sensor_id': row['sensor_id'],
            'temperature': row['temperature'],
            'location': row['location'],
            'timestamp': row['timestamp']
        })
    
    conn.close()
    return jsonify(sensors)

@app.route('/api/temperature/history/<sensor_id>')
def get_temperature_history(sensor_id):
    hours = request.args.get('hours', 24, type=int)
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT temperature, timestamp
        FROM temperature_readings
        WHERE sensor_id = ? AND timestamp >= datetime('now', ?)
        ORDER BY timestamp
    ''', (sensor_id, f'-{hours} hours'))
    
    history = []
    for row in cursor.fetchall():
        history.append({
            'temperature': row['temperature'],
            'timestamp': row['timestamp']
        })
    
    conn.close()
    return jsonify(history)

@app.route('/api/alerts/active')
def get_active_alerts():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT sensor_id, alert_type, temperature, timestamp
        FROM alerts
        WHERE resolved = FALSE
        ORDER BY timestamp DESC
    ''')
    
    alerts = []
    for row in cursor.fetchall():
        alerts.append({
            'sensor_id': row['sensor_id'],
            'alert_type': row['alert_type'],
            'temperature': row['temperature'],
            'timestamp': row['timestamp']
        })
    
    conn.close()
    return jsonify(alerts)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)