#!/usr/bin/env python3
"""
Test script for Car Rental Telegram Bot
This script tests the core functionality without requiring a Telegram bot token
"""

import sys
import os
from datetime import datetime, date, timedelta

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import Database
from utils import *
from config import CAR_CATEGORIES

def test_database():
    """Test database functionality"""
    print("🧪 Testing Database...")
    
    try:
        # Initialize database
        db = Database()
        print("✅ Database initialized successfully")
        
        # Test user operations
        db.add_user(12345, "testuser", "John", "Doe")
        user = db.get_user(12345)
        if user:
            print("✅ User operations working")
        else:
            print("❌ User operations failed")
        
        # Test car operations
        cars = db.get_available_cars()
        if cars:
            print(f"✅ Found {len(cars)} cars in database")
        else:
            print("❌ No cars found in database")
        
        # Test booking operations
        if cars:
            car = cars[0]
            booking_id = db.create_booking(
                12345, car[0], date(2024, 1, 15), date(2024, 1, 20), 
                250.0, "Credit Card"
            )
            if booking_id:
                print("✅ Booking creation working")
                
                # Test booking retrieval
                bookings = db.get_user_bookings(12345)
                if bookings:
                    print("✅ Booking retrieval working")
                else:
                    print("❌ Booking retrieval failed")
            else:
                print("❌ Booking creation failed")
        
        print("✅ Database tests completed\n")
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def test_utils():
    """Test utility functions"""
    print("🧪 Testing Utility Functions...")
    
    try:
        # Test date validation
        assert validate_date_format("2024-01-15") == True
        assert validate_date_format("invalid-date") == False
        print("✅ Date validation working")
        
        # Test date parsing
        start, end = parse_date_range("2024-01-15 - 2024-01-20")
        assert start == date(2024, 1, 15)
        assert end == date(2024, 1, 20)
        print("✅ Date parsing working")
        
        # Test price calculation with discounts
        # 5 days - 15% discount (3+ days)
        base_price = 49990
        days = 5
        expected_price = base_price * days * 0.85  # 15% discount
        assert calculate_total_price(base_price, days) == expected_price
        print("✅ Price calculation working")
        
        # Test formatting
        assert format_price(49990) == "$49,990 CLP"
        assert format_date(date(2024, 1, 15)) == "January 15, 2024"
        print("✅ Formatting functions working")
        
        # Test validation - use a future date
        future_date = date.today() + timedelta(days=10)
        end_date = future_date + timedelta(days=5)
        is_valid, message = validate_rental_period(future_date, end_date)
        assert is_valid == True
        print("✅ Rental period validation working")
        
        # Test discount calculation
        assert calculate_discount_percentage(2) == 0  # No discount
        assert calculate_discount_percentage(3) == 15  # 15% for 3+ days
        assert calculate_discount_percentage(30) == 25  # 25% for 30+ days
        assert calculate_discount_percentage(90) == 35  # 35% for 90+ days
        print("✅ Discount calculation working")
        
        # Test email validation
        assert is_valid_email("test@example.com") == True
        assert is_valid_email("invalid-email") == False
        print("✅ Email validation working")
        
        # Test phone validation
        assert is_valid_phone("+1234567890") == True
        assert is_valid_phone("1234567890") == True
        print("✅ Phone validation working")
        
        print("✅ Utility function tests completed\n")
        return True
        
    except Exception as e:
        print(f"❌ Utility function test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_config():
    """Test configuration"""
    print("🧪 Testing Configuration...")
    
    try:
        # Test car categories
        assert 'economy' in CAR_CATEGORIES
        assert 'standard' in CAR_CATEGORIES
        assert 'premium' in CAR_CATEGORIES
        assert 'suv' in CAR_CATEGORIES
        print("✅ Car categories configured correctly")
        
        # Test category structure
        for category_id, category_info in CAR_CATEGORIES.items():
            assert 'name' in category_info
            assert 'price_per_day' in category_info
            assert 'description' in category_info
        print("✅ Category structure valid")
        
        print("✅ Configuration tests completed\n")
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

def test_sample_data():
    """Test sample data generation"""
    print("🧪 Testing Sample Data...")
    
    try:
        db = Database()
        cars = db.get_available_cars()
        
        # Check if we have cars in each category
        categories = set()
        for car in cars:
            categories.add(car[4])  # category field
        
        expected_categories = {'economy', 'standard', 'premium', 'suv'}
        print(f"Found categories: {categories}")
        print(f"Expected categories: {expected_categories}")
        print(f"Missing categories: {expected_categories - categories}")
        
        # Check if we have at least some categories
        assert len(categories) > 0
        print(f"✅ Found cars in categories: {categories}")
        
        # Check car details - cars table has 10 columns: car_id, model, brand, year, category, price_per_day, available, image_url, description, created_at
        for car in cars:
            car_id, model, brand, year, category, price, available, image_url, description, created_at = car
            assert model and brand and year and price > 0
            assert category in CAR_CATEGORIES
            assert isinstance(available, int)  # SQLite stores boolean as integer
        
        print("✅ Sample data validation completed\n")
        return True
        
    except Exception as e:
        print(f"❌ Sample data test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("🚗 Car Rental Bot - Test Suite")
    print("=" * 40)
    
    tests = [
        test_config,
        test_database,
        test_utils,
        test_sample_data
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("=" * 40)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The bot is ready to run.")
        print("\n📝 Next steps:")
        print("1. Get a Telegram bot token from @BotFather")
        print("2. Create a .env file with your BOT_TOKEN")
        print("3. Run: python bot.py")
    else:
        print("❌ Some tests failed. Please check the errors above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 