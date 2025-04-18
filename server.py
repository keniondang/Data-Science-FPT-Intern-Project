# server.py
from flask import Flask, jsonify
import pyodbc

# Create the Flask application
app = Flask(__name__)

# SQL Server Configuration
app.config['SQLSERVER_HOST'] = 'IT-ONDANGKN\\SQLEXPRESS' 
app.config['SQLSERVER_DB'] = 'ip_location_api'             

# Global variable for database connection
def get_db_connection():
    """Get a connection to the database"""
    connection_string = (
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER={app.config['SQLSERVER_HOST']};"
        f"DATABASE={app.config['SQLSERVER_DB']};"
        "Trusted_Connection=yes;"
    )
    return pyodbc.connect(connection_string)

def close_db(e=None):
    """Close the database connection at the end of a request"""
    # Implementation to close DB connection if needed
    pass

# Register database close function
app.teardown_appcontext(close_db)

# Root route for API info
@app.route('/')
def index():
    """Root endpoint that provides API information"""
    return jsonify({
        "name": "VPN Analysis API",
        "version": "2.0",
        "description": "API for analyzing VPN usage patterns with enhanced data preprocessing",
        "endpoints": [
            # API key management endpoints
            "/api/authenticate - Test your API key",
            "/api/users - List all users (admin only)",
            "/api/stats - Get database statistics (admin only)",
            "/api/key/generate - Generate new API key (admin only, POST)",
            "/api/key/<key> - Get/Update/Delete API key (admin only)",
            "/api/keys - List all API keys (admin only, GET)",
            
            # VPN endpoints with enhanced capabilities
            "/api/vpn/load - Load VPN data from CSV (admin only, POST)",
            "/api/vpn/stats - Get VPN usage statistics, including time categories",
            "/api/vpn/users/<username> - Get VPN usage details for a user",
            "/api/vpn/anomalies - Detect potential anomalies in VPN usage patterns"
        ]
    })

def init_db():
    """Initialize the database with required tables"""
    try:
        # Create connection to SQL Server
        connection_string = (
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={app.config['SQLSERVER_HOST']};"
            "Trusted_Connection=yes;"
        )
        
        # First connect to master to check if our database exists
        conn = pyodbc.connect(connection_string + "DATABASE=master;")
        cursor = conn.cursor()
        
        # Check if database exists, create if not
        cursor.execute(f"SELECT database_id FROM sys.databases WHERE Name = '{app.config['SQLSERVER_DB']}'")
        if not cursor.fetchone():
            cursor.execute(f"CREATE DATABASE {app.config['SQLSERVER_DB']}")
            print(f"Database {app.config['SQLSERVER_DB']} created")
        
        conn.close()
        
        # Now connect to our database
        conn = pyodbc.connect(connection_string + f"DATABASE={app.config['SQLSERVER_DB']};")
        cursor = conn.cursor()
        
        # Create api_keys table
        cursor.execute('''
        IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[api_keys]') AND type in (N'U'))
        BEGIN
            CREATE TABLE [dbo].[api_keys] (
                [key] NVARCHAR(255) PRIMARY KEY,
                [username] NVARCHAR(255) NOT NULL,
                [rate_limit] INT DEFAULT 100,
                [is_admin] BIT DEFAULT 0
            )
        END
        ''')
        
        # Create vpn_logs table with enhanced fields from updated preprocessor
        cursor.execute('''
        IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[vpn_logs]') AND type in (N'U'))
        BEGIN
            CREATE TABLE [dbo].[vpn_logs] (
                [id] INT IDENTITY(1,1) PRIMARY KEY,
                [timestamp] DATETIME,
                [username] NVARCHAR(255) NOT NULL,
                [source_ip] NVARCHAR(45) NOT NULL,
                [department] NVARCHAR(255),
                [vpn_gateway] NVARCHAR(100),
                [session_id] NVARCHAR(100),
                [hour_of_day] INT,
                [time_category] NVARCHAR(50)
            )
            
            CREATE INDEX [idx_vpn_username] ON [dbo].[vpn_logs] ([username])
            CREATE INDEX [idx_vpn_source_ip] ON [dbo].[vpn_logs] ([source_ip])
            CREATE INDEX [idx_vpn_time_category] ON [dbo].[vpn_logs] ([time_category])
        END
        ''')
        
        # Check if default API keys exist
        cursor.execute('SELECT COUNT(*) FROM api_keys')
        count = cursor.fetchone()[0]
        
        if count == 0:
            # Add default API keys - one regular user and one admin
            cursor.execute('''
            INSERT INTO api_keys ([key], username, rate_limit, is_admin) VALUES 
            ('demo_key', 'demo_user', 100, 0),
            ('admin_key', 'admin_user', 1000, 1)
            ''')
        
        conn.commit()
        conn.close()
        
        print("Database initialized successfully")
    except Exception as e:
        print(f"Error initializing database: {e}")

# Initialize the application
def init_app():
    """Initialize the application"""
    # Initialize the database
    with app.app_context():
        init_db()
    
    # Register blueprints
    from api_keys import api_bp
    from vpn_analysis import vpn_bp
    
    app.register_blueprint(api_bp)
    app.register_blueprint(vpn_bp)
    
    return app

# Configuration
DATA_FILE = 'sample_data.csv'
HOST = '0.0.0.0'
PORT = 5000
DEBUG = True

# Run the application
if __name__ == '__main__':
    # Initialize the app
    app = init_app()
    
    # Start the server
    print(f"Starting server on {HOST}:{PORT}")
    print(f"Debug mode: {'ON' if DEBUG else 'OFF'}")
    print(f"Database: SQL Server ({app.config['SQLSERVER_HOST']} / {app.config['SQLSERVER_DB']})")
    app.run(debug=DEBUG, host=HOST, port=PORT)