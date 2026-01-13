import random
import time
import sqlite3
import logging
from datetime import datetime
import threading

class WarehouseTemperatureMonitor:
    def __init__(self, db_path="warehouse_temperature.db"):
        self.db_path = db_path
        self.sensors = {}
        self.is_running = False
        self.alert_threshold_high = 25.0
        self.alert_threshold_low = 2.0
        
        # SETUP LOGGING FIRST
        self.setup_logging()   # Creates warehouse_monitor.log FIRST
        self.setup_database()  # Then creates warehouse_temperature.db
        self.setup_default_sensors()
        
    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('warehouse_monitor.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        self.logger.info("Logging system initialized - warehouse_monitor.log created")
    
    def setup_database(self):
        """Creates warehouse_temperature.db file"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS temperature_readings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sensor_id TEXT NOT NULL,
                    temperature REAL NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    location TEXT
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sensor_id TEXT NOT NULL,
                    alert_type TEXT NOT NULL,
                    temperature REAL NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    resolved BOOLEAN DEFAULT FALSE
                )
            ''')
            
            conn.commit()
            conn.close()
            self.logger.info("Database warehouse_temperature.db created successfully with tables")
            
        except Exception as e:
            print(f"Error creating database: {e}")
    
    def setup_default_sensors(self):
        default_sensors = [
            ("sensor_001", "Cold Storage Area"),
            ("sensor_002", "Loading Dock"),
            ("sensor_003", "Main Storage Area"),
            ("sensor_004", "Office Area"),
            ("sensor_005", "Shipping Department")
        ]
        
        for sensor_id, location in default_sensors:
            self.sensors[sensor_id] = {
                'location': location,
                'current_temp': random.uniform(15.0, 25.0),
                'last_reading': None,
                'is_active': True
            }
        self.logger.info("5 sensors added for simulation")
    
    def generate_random_temperature(self, sensor_id):
        """Generate random temperature data that will trigger alerts"""
        base_temps = {
            "sensor_001": (1.0, 10.0),    # Cold Storage - more likely to trigger low alerts
            "sensor_002": (15.0, 30.0),   # Loading Dock - more likely to trigger high alerts
            "sensor_003": (18.0, 28.0),   # Main Storage
            "sensor_004": (20.0, 24.0),   # Office Area
            "sensor_005": (16.0, 26.0)    # Shipping Department
        }
        
        base_min, base_max = base_temps.get(sensor_id, (15.0, 25.0))
        temperature = random.uniform(base_min, base_max)
        
        # Frequently create extreme temperatures to trigger alerts for demo
        if random.random() < 0.3:  # 30% chance for extreme values
            if random.random() < 0.5:
                temperature = random.uniform(26.0, 35.0)  # High temperature
            else:
                temperature = random.uniform(-5.0, 1.0)   # Low temperature
        
        return round(temperature, 1)
    
    def store_reading(self, sensor_id, temperature):
        """Store in warehouse_temperature.db"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO temperature_readings (sensor_id, temperature, location)
            VALUES (?, ?, ?)
        ''', (sensor_id, temperature, self.sensors[sensor_id]['location']))
        
        conn.commit()
        conn.close()
    
    def check_alerts(self, sensor_id, temperature):
        """Check and log alerts"""
        if temperature > self.alert_threshold_high:
            message = f"HIGH TEMPERATURE: {self.sensors[sensor_id]['location']} - {temperature}°C (Threshold: {self.alert_threshold_high}°C)"
            self.store_alert(sensor_id, "HIGH_TEMPERATURE", temperature)
            self.logger.warning(message)
            print(f"🚨 {message}")
            
        elif temperature < self.alert_threshold_low:
            message = f"LOW TEMPERATURE: {self.sensors[sensor_id]['location']} - {temperature}°C (Threshold: {self.alert_threshold_low}°C)"
            self.store_alert(sensor_id, "LOW_TEMPERATURE", temperature)
            self.logger.warning(message)
            print(f"🚨 {message}")
    
    def store_alert(self, sensor_id, alert_type, temperature):
        """Store alert in warehouse_temperature.db"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO alerts (sensor_id, alert_type, temperature)
            VALUES (?, ?, ?)
        ''', (sensor_id, alert_type, temperature))
        
        conn.commit()
        conn.close()
    
    def monitoring_loop(self):
        """Main loop that generates random data"""
        self.logger.info("Starting temperature monitoring system - generating random data every 3 seconds")
        
        while self.is_running:
            for sensor_id in self.sensors.keys():
                # Generate random temperature
                temperature = self.generate_random_temperature(sensor_id)
                
                # Store in database
                self.store_reading(sensor_id, temperature)
                
                # Check for alerts
                self.check_alerts(sensor_id, temperature)
                
                # Update sensor data
                self.sensors[sensor_id]['last_reading'] = {
                    'temperature': temperature,
                    'timestamp': datetime.now()
                }
            
            time.sleep(3)  # Generate data every 3 seconds
    
    def start_monitoring(self):
        self.is_running = True
        self.monitor_thread = threading.Thread(target=self.monitoring_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        self.logger.info("Monitoring thread started")
    
    def stop_monitoring(self):
        self.is_running = False
        self.logger.info("Monitoring system stopped")

# Simple console display
def display_updates(monitor):
    print("\n📊 LIVE TEMPERATURE MONITORING STARTED!")
    print("📍 Monitoring 5 warehouse locations")
    print("🔔 Alerts will appear when temperature exceeds 25°C or drops below 2°C")
    print("⏹️  Press Ctrl+C to stop\n")
    
    try:
        while True:
            time.sleep(5)
            print("\n" + "="*60)
            print(f"📊 LIVE UPDATE - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("="*60)
            
            for sensor_id, data in monitor.sensors.items():
                if data['last_reading']:
                    temp = data['last_reading']['temperature']
                    if temp > 25:
                        status = "🔥 HIGH ALERT"
                    elif temp < 2:
                        status = "❄️  LOW ALERT"
                    else:
                        status = "✅ NORMAL"
                    print(f"{status:12} | {data['location']:20} | {temp:5}°C")
            
            print("="*60)
            print("Next update in 5 seconds...")
            
    except KeyboardInterrupt:
        pass

# RUN THIS CODE - IT WILL CREATE THE FILES AUTOMATICALLY
if __name__ == "__main__":
    print("🚀 Starting Warehouse Temperature Monitoring System...")
    print("📁 Creating warehouse_temperature.db and warehouse_monitor.log...")
    
    monitor = WarehouseTemperatureMonitor()
    
    try:
        monitor.start_monitoring()
        display_updates(monitor)
        
    except KeyboardInterrupt:
        print("\n🛑 Stopping system...")
        monitor.stop_monitoring()
    except Exception as e:
        print(f"Error: {e}")