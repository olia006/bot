import sqlite3
import logging
from datetime import datetime, date
from config import DATABASE_PATH
from typing import List, Tuple, Optional
import os

class Database:
    def __init__(self, db_path: str = DATABASE_PATH):
        self.db_path = db_path
        self.create_tables()
        if not self.get_cars():  # If no cars exist
            self.populate_sample_cars()
    
    def create_tables(self):
        """Create database tables if they don't exist"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Users table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        user_id INTEGER PRIMARY KEY,
                        username TEXT,
                        first_name TEXT,
                        last_name TEXT,
                        phone TEXT,
                        email TEXT,
                        language TEXT DEFAULT 'en',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Cars table with updated structure
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS cars (
                        car_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        model TEXT NOT NULL,
                        brand TEXT NOT NULL,
                        year INTEGER NOT NULL,
                        category TEXT NOT NULL,
                        price_per_day INTEGER NOT NULL,
                        available BOOLEAN DEFAULT 1,
                        image_url TEXT,
                        description TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_maintenance DATE,
                        total_rentals INTEGER DEFAULT 0,
                        total_revenue INTEGER DEFAULT 0,
                        average_rating FLOAT DEFAULT 0
                    )
                ''')
                
                # Bookings table with payment tracking
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS bookings (
                        booking_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        car_id INTEGER NOT NULL,
                        start_date DATE NOT NULL,
                        end_date DATE NOT NULL,
                        total_price INTEGER NOT NULL,
                        status TEXT DEFAULT 'pending',
                        payment_method TEXT,
                        payment_status TEXT DEFAULT 'pending',
                        payment_transaction_id TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users (user_id),
                        FOREIGN KEY (car_id) REFERENCES cars (car_id)
                    )
                ''')
                
                # Reviews table with enhanced features
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS reviews (
                        review_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        booking_id INTEGER NOT NULL UNIQUE,
                        user_id INTEGER NOT NULL,
                        car_id INTEGER NOT NULL,
                        rating INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
                        comment TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (booking_id) REFERENCES bookings (booking_id),
                        FOREIGN KEY (user_id) REFERENCES users (user_id),
                        FOREIGN KEY (car_id) REFERENCES cars (car_id)
                    )
                ''')
                
                # Maintenance log table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS maintenance_log (
                        log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        car_id INTEGER NOT NULL,
                        maintenance_date DATE NOT NULL,
                        description TEXT NOT NULL,
                        cost INTEGER NOT NULL,
                        next_maintenance_date DATE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (car_id) REFERENCES cars (car_id)
                    )
                ''')
                
                conn.commit()
                
        except Exception as e:
            logging.error(f"Database initialization error: {e}")
    
    def populate_sample_cars(self):
        """Populate the database with sample cars"""
        sample_cars = [
            # Premium Category
            ('All New GS8', 'GAC', 2024, 'premium', 149990, 1, 'public/images/gacfull.png', 'SUV grande, 7 asientos (Blanco)'),
            ('All New GS8', 'GAC', 2024, 'premium', 149990, 1, 'public/images/gaccomfort.PNG', 'SUV grande, 7 asientos (Negro)'),
            ('RX 450 H', 'Lexus', 2024, 'premium', 135990, 1, 'public/images/lexusrx.png', 'SUV premium híbrido'),
            
            # Economy Category
            ('Cavalier', 'Chevrolet', 2024, 'economy', 49990, 1, 'public/images/chevrolett.png', 'Sedán compacto'),
            ('Tiggo 2 Pro Max', 'Cherry', 2024, 'economy', 49990, 1, 'public/images/cherry.PNG', 'SUV compacto'),
            ('Accord', 'Honda', 2024, 'economy', 34990, 1, 'public/images/honda.png', 'Sedán mediano/full-size'),
            ('6', 'Mazda', 2024, 'economy', 49990, 1, 'public/images/mazda6.png', 'Sedán mediano'),
            ('Impreza', 'Subaru', 2024, 'economy', 49990, 1, 'public/images/Impreza.jpeg', 'Hatchback compacto'),
            ('ES 350', 'Lexus', 2024, 'economy', 54990, 1, 'public/images/lexuses.png', 'Sedán premium'),
            
            # SUV Category
            ('CX-9', 'Mazda', 2024, 'suv', 119990, 1, 'public/images/mazda9.png', '7 asientos, SUV grande'),
            ('Outlander', 'Mitsubishi', 2024, 'suv', 71990, 1, 'public/images/mitsubishi.png', 'SUV mediano'),
            ('Outback', 'Subaru', 2024, 'suv', 64990, 1, 'public/images/subaruoutback.png', 'Wagon/Crossover 4x4'),
            ('RAV4', 'Toyota', 2024, 'suv', 71990, 1, 'public/images/toyota.png', 'SUV compacto')
        ]
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.executemany('''
                    INSERT INTO cars (model, brand, year, category, price_per_day, available, image_url, description)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', sample_cars)
                conn.commit()
        except Exception as e:
            logging.error(f"Error populating sample cars: {e}")
    
    def add_user(self, user_id, username, first_name, last_name, language='en'):
        """Add or update user information"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO users (user_id, username, first_name, last_name, language)
                    VALUES (?, ?, ?, ?, ?)
                ''', (user_id, username, first_name, last_name, language))
                conn.commit()
                return True
        except Exception as e:
            logging.error(f"Error adding user: {e}")
            return False
    
    def get_user(self, user_id):
        """Get user information"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
                return cursor.fetchone()
        except Exception as e:
            logging.error(f"Error getting user: {e}")
            return None
    
    def get_available_cars(self, category=None):
        """Get available cars, optionally filtered by category"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                if category:
                    cursor.execute('''
                        SELECT * FROM cars 
                        WHERE available = 1 AND category = ?
                        ORDER BY price_per_day
                    ''', (category,))
                else:
                    cursor.execute('''
                        SELECT * FROM cars 
                        WHERE available = 1
                        ORDER BY category, price_per_day
                    ''')
                return cursor.fetchall()
        except Exception as e:
            logging.error(f"Error getting available cars: {e}")
            return []
    
    def get_car(self, car_id):
        """Get specific car information"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM cars WHERE car_id = ?', (car_id,))
                return cursor.fetchone()
        except Exception as e:
            logging.error(f"Error getting car: {e}")
            return None
    
    def create_booking(self, user_id, car_id, start_date, end_date, total_price, payment_method):
        """Create a new booking"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO bookings (user_id, car_id, start_date, end_date, total_price, payment_method)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (user_id, car_id, start_date, end_date, total_price, payment_method))
                booking_id = cursor.lastrowid
                
                # Mark car as unavailable
                cursor.execute('UPDATE cars SET available = 0 WHERE car_id = ?', (car_id,))
                conn.commit()
                return booking_id
        except Exception as e:
            logging.error(f"Error creating booking: {e}")
            return None
    
    def get_user_bookings(self, user_id):
        """Get all bookings for a user"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT b.*, c.model, c.brand, c.year
                    FROM bookings b
                    JOIN cars c ON b.car_id = c.car_id
                    WHERE b.user_id = ?
                    ORDER BY b.created_at DESC
                ''', (user_id,))
                return cursor.fetchall()
        except Exception as e:
            logging.error(f"Error getting user bookings: {e}")
            return []
    
    def update_booking_status(self, booking_id, status):
        """Update booking status"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE bookings SET status = ? WHERE booking_id = ?
                ''', (status, booking_id))
                conn.commit()
                return True
        except Exception as e:
            logging.error(f"Error updating booking status: {e}")
            return False
    
    def cancel_booking(self, booking_id, user_id):
        """Cancel a booking and make car available again"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                # Get car_id from booking
                cursor.execute('SELECT car_id FROM bookings WHERE booking_id = ? AND user_id = ?', 
                             (booking_id, user_id))
                result = cursor.fetchone()
                if result:
                    car_id = result[0]
                    # Update booking status
                    cursor.execute('''
                        UPDATE bookings SET status = 'cancelled' WHERE booking_id = ?
                    ''', (booking_id,))
                    # Make car available again
                    cursor.execute('UPDATE cars SET available = 1 WHERE car_id = ?', (car_id,))
                    conn.commit()
                    return True
                return False
        except Exception as e:
            logging.error(f"Error cancelling booking: {e}")
            return False
    
    def add_review(self, booking_id, user_id, car_id, rating, comment):
        """Add a review for a completed booking"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO reviews (booking_id, user_id, car_id, rating, comment)
                    VALUES (?, ?, ?, ?, ?)
                ''', (booking_id, user_id, car_id, rating, comment))
                conn.commit()
                return True
        except Exception as e:
            logging.error(f"Error adding review: {e}")
            return False
    
    def get_car_reviews(self, car_id):
        """Get reviews for a specific car"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT r.*, u.first_name, u.last_name
                    FROM reviews r
                    JOIN users u ON r.user_id = u.user_id
                    WHERE r.car_id = ?
                    ORDER BY r.created_at DESC
                ''', (car_id,))
                return cursor.fetchall()
        except Exception as e:
            logging.error(f"Error getting car reviews: {e}")
            return []
    
    def get_rental_statistics(self) -> dict:
        """Get rental statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                stats = {}
                
                # Total rentals and revenue
                cursor.execute('''
                    SELECT 
                        COUNT(*) as total_bookings,
                        SUM(total_price) as total_revenue,
                        COUNT(DISTINCT user_id) as total_customers
                    FROM bookings
                    WHERE status != 'cancelled'
                ''')
                result = cursor.fetchone()
                stats['total_bookings'] = result[0]
                stats['total_revenue'] = result[1] or 0
                stats['total_customers'] = result[2]
                
                # Revenue by category
                cursor.execute('''
                    SELECT 
                        cars.category,
                        COUNT(*) as rentals,
                        SUM(bookings.total_price) as revenue
                    FROM bookings
                    JOIN cars ON bookings.car_id = cars.car_id
                    WHERE bookings.status != 'cancelled'
                    GROUP BY cars.category
                ''')
                stats['revenue_by_category'] = cursor.fetchall()
                
                # Most popular cars
                cursor.execute('''
                    SELECT 
                        cars.brand,
                        cars.model,
                        COUNT(*) as rental_count
                    FROM bookings
                    JOIN cars ON bookings.car_id = cars.car_id
                    WHERE bookings.status != 'cancelled'
                    GROUP BY cars.car_id
                    ORDER BY rental_count DESC
                    LIMIT 5
                ''')
                stats['popular_cars'] = cursor.fetchall()
                
                # Average ratings
                cursor.execute('''
                    SELECT 
                        cars.category,
                        AVG(reviews.rating) as avg_rating
                    FROM reviews
                    JOIN cars ON reviews.car_id = cars.car_id
                    GROUP BY cars.category
                ''')
                stats['ratings_by_category'] = cursor.fetchall()
                
                return stats
        except Exception as e:
            logging.error(f"Error getting rental statistics: {e}")
            return {}
    
    def backup_database(self) -> str:
        """Create a backup of the database"""
        try:
            backup_dir = 'backups'
            os.makedirs(backup_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = f"{backup_dir}/car_rental_backup_{timestamp}.db"
            
            with sqlite3.connect(self.db_path) as conn:
                backup = sqlite3.connect(backup_path)
                conn.backup(backup)
            
            return backup_path
        except Exception as e:
            logging.error(f"Error backing up database: {e}")
            return ""
    
    def add_maintenance_log(self, car_id: int, description: str, cost: int, next_maintenance_date: Optional[date] = None) -> bool:
        """Add a maintenance log entry"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO maintenance_log 
                    (car_id, maintenance_date, description, cost, next_maintenance_date)
                    VALUES (?, DATE('now'), ?, ?, ?)
                ''', (car_id, description, cost, next_maintenance_date))
                
                # Update car's last maintenance date
                cursor.execute('''
                    UPDATE cars 
                    SET last_maintenance = DATE('now')
                    WHERE car_id = ?
                ''', (car_id,))
                
                conn.commit()
                return True
        except Exception as e:
            logging.error(f"Error adding maintenance log: {e}")
            return False
    
    def get_maintenance_history(self, car_id: int) -> List[tuple]:
        """Get maintenance history for a car"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM maintenance_log
                    WHERE car_id = ?
                    ORDER BY maintenance_date DESC
                ''', (car_id,))
                
                history = cursor.fetchall()
                return history
        except Exception as e:
            logging.error(f"Error getting maintenance history: {e}")
            return []
    
    def get_cars(self):
        """Get all cars"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM cars ORDER BY category, brand, model')
                return cursor.fetchall()
        except Exception as e:
            logging.error(f"Error getting cars: {e}")
            return []
    
    def update_user_language(self, user_id: int, language: str) -> bool:
        """Update user's preferred language"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE users SET language = ? WHERE user_id = ?
                ''', (language, user_id))
                conn.commit()
                return True
        except Exception as e:
            logging.error(f"Error updating user language: {e}")
            return False
    
    def get_user_language(self, user_id: int) -> str:
        """Get user's preferred language"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT language FROM users WHERE user_id = ?', (user_id,))
                result = cursor.fetchone()
                return result[0] if result else 'en'
        except Exception as e:
            logging.error(f"Error getting user language: {e}")
            return 'en' 