import pymysql
import os
from datetime import datetime

def setup_mariadb():
    """Set up MariaDB database with tables and sample data"""

    # Database connection details - using root with password
    db_config = {
        'host': 'localhost',
        'user': 'root',
        'password': 'maria123',  # Password for root user
        'database': 'editathons',
        'charset': 'utf8mb4',
        'cursorclass': pymysql.cursors.DictCursor,
        'autocommit': True
    }

    try:
        # Connect to MySQL server (without specifying database to create it)
        connection = pymysql.connect(
            host=db_config['host'],
            user=db_config['user'],
            password=db_config['password'],
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )

        with connection.cursor() as cursor:
            # Create database if it doesn't exist
            cursor.execute("CREATE DATABASE IF NOT EXISTS editathons CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            print("✅ Database 'editathons' created or already exists")

        connection.commit()
        connection.close()

        # Now connect to the specific database
        connection = pymysql.connect(**db_config)

        with connection.cursor() as cursor:
            # Create tables
            tables = [
                """
                CREATE TABLE IF NOT EXISTS wikipedia_asian_month_2025 (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_name VARCHAR(255) NOT NULL,
                    article_title VARCHAR(500) NOT NULL,
                    article_added DATETIME,
                    points INT,
                    jury_notes TEXT
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """,
                """
                CREATE TABLE IF NOT EXISTS wiki_loves_ramadan_2025 (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_name VARCHAR(255) NOT NULL,
                    article_title VARCHAR(500) NOT NULL,
                    article_added DATETIME,
                    points INT,
                    jury_notes TEXT
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """,
                """
                CREATE TABLE IF NOT EXISTS women_in_red_translation_contest_2024 (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_name VARCHAR(255) NOT NULL,
                    article_title VARCHAR(500) NOT NULL,
                    article_added DATETIME,
                    points INT,
                    jury_notes TEXT
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """,
                """
                CREATE TABLE IF NOT EXISTS feminism_and_folklore_2024 (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_name VARCHAR(255) NOT NULL,
                    article_title VARCHAR(500) NOT NULL,
                    article_added DATETIME,
                    points INT,
                    jury_notes TEXT
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """
            ]

            for table_sql in tables:
                cursor.execute(table_sql)
                print("✅ Table created successfully")

            # Sample data for wikipedia_asian_month_2025
            wikipedia_asian_data = [
                ('Min968', 'History of Korean cuisine', '2025-11-01 10:00:00', 85, 'Excellent coverage of traditional Korean dishes and their cultural significance'),
                ('MisawaSakura', 'Japanese tea ceremony', '2025-11-02 14:30:00', 92, 'Comprehensive article with great attention to detail'),
                ('Nicholas0', 'Traditional Mongolian clothing', '2025-11-03 09:15:00', 78, 'Good research but could use more images'),
                ('SDGB1217', 'Filipino martial arts', '2025-11-04 16:45:00', 88, 'Well-structured article with reliable sources'),
                ('Min968', 'Chinese calligraphy techniques', '2025-11-05 11:20:00', 90, 'Outstanding work on brush techniques'),
                ('MisawaSakura', 'Vietnamese traditional music', '2025-11-06 13:10:00', 85, 'Good coverage of musical instruments'),
                ('Nicholas0', 'Thai Buddhist temples', '2025-11-07 15:30:00', 82, 'Solid research on temple architecture'),
                ('SDGB1217', 'Indonesian batik patterns', '2025-11-08 10:45:00', 87, 'Beautiful article on cultural significance'),
                ('Min968', 'Singaporean street food', '2025-11-09 12:15:00', 89, 'Excellent documentation of local cuisine'),
                ('MisawaSakura', 'Cambodian Angkor Wat history', '2025-11-10 14:20:00', 91, 'Comprehensive historical analysis'),
                ('Nicholas0', 'Malaysian traditional games', '2025-11-11 16:30:00', 80, 'Good introduction to cultural games'),
                ('SDGB1217', 'Burmese pagoda festivals', '2025-11-12 11:45:00', 86, 'Well-researched festival traditions')
            ]

            # Sample data for wiki_loves_ramadan_2025
            ramadan_data = [
                ('Min968', 'Ramadan traditions in Muslim countries', '2025-02-25 10:00:00', 88, 'Comprehensive overview of global Ramadan practices'),
                ('ZI Jony', 'Islamic calligraphy during Ramadan', '2025-02-26 14:30:00', 92, 'Beautiful examples of decorative arts'),
                ('MisawaSakura', 'Ramadan food traditions', '2025-02-27 09:15:00', 85, 'Excellent coverage of traditional dishes'),
                ('Nicholas0', 'Mosque architecture and Ramadan', '2025-02-28 16:45:00', 87, 'Good architectural analysis'),
                ('SDGB1217', 'Ramadan charity and community service', '2025-03-01 11:20:00', 90, 'Outstanding work on social aspects'),
                ('Min968', 'Ramadan in modern times', '2025-03-02 13:10:00', 86, 'Contemporary perspectives well covered'),
                ('ZI Jony', 'Ramadan moon sighting traditions', '2025-03-03 15:30:00', 89, 'Detailed astronomical and cultural aspects'),
                ('MisawaSakura', 'Family gatherings during Ramadan', '2025-03-04 10:45:00', 84, 'Heartwarming family traditions'),
                ('Nicholas0', 'Ramadan shopping and markets', '2025-03-05 12:15:00', 82, 'Good coverage of economic aspects'),
                ('SDGB1217', 'Ramadan literature and poetry', '2025-03-06 14:20:00', 91, 'Excellent literary analysis')
            ]

            # Sample data for women_in_red_translation_contest_2024
            women_red_data = [
                ('Min968', 'Marie Curie biography (translated)', '2024-07-01 10:00:00', 90, 'Excellent translation with cultural adaptation'),
                ('MisawaSakura', 'Malala Yousafzai story (translated)', '2024-07-15 14:30:00', 88, 'Well-translated inspirational story')
            ]

            # Sample data for feminism_and_folklore_2024
            feminism_data = [
                ('Haoreima', 'Feminist themes in Japanese folklore', '2024-02-01 10:00:00', 92, 'Outstanding analysis of gender roles in traditional stories')
            ]

            # Insert sample data
            data_sets = [
                (wikipedia_asian_data, 'wikipedia_asian_month_2025'),
                (ramadan_data, 'wiki_loves_ramadan_2025'),
                (women_red_data, 'women_in_red_translation_contest_2024'),
                (feminism_data, 'feminism_and_folklore_2024')
            ]

            for data, table_name in data_sets:
                for row in data:
                    cursor.execute(f"""
                        INSERT INTO {table_name} (user_name, article_title, article_added, points, jury_notes)
                        VALUES (%s, %s, %s, %s, %s)
                    """, row)
                print(f"✅ Sample data inserted into {table_name}")

        connection.commit()
        print("✅ All tables created and sample data inserted successfully!")

        # Verify data insertion
        with connection.cursor() as cursor:
            tables_to_check = [
                'wikipedia_asian_month_2025',
                'wiki_loves_ramadan_2025',
                'women_in_red_translation_contest_2024',
                'feminism_and_folklore_2024'
            ]

            print("\n📊 Database Summary:")
            for table in tables_to_check:
                cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
                result = cursor.fetchone()
                print(f"   {table}: {result['count']} articles")

    except pymysql.Error as e:
        print(f"❌ MariaDB Error: {e}")
        return False
    except Exception as e:
        print(f"❌ General Error: {e}")
        return False
    finally:
        if 'connection' in locals():
            connection.close()

    return True

if __name__ == "__main__":
    print("🚀 Setting up MariaDB database for Editathon Review Tool...")
    success = setup_mariadb()
    if success:
        print("\n✅ MariaDB setup completed successfully!")
        print("📋 You can now run your Flask application with MariaDB backend.")
    else:
        print("\n❌ MariaDB setup failed. Please check your configuration.")
