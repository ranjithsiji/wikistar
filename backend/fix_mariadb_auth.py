import pymysql
import sys

def fix_mariadb_auth():
    """Fix MariaDB authentication plugin issue"""

    try:
        print("🔧 Attempting to fix MariaDB authentication...")

        # First, try to connect with current settings
        try:
            connection = pymysql.connect(
                host='localhost',
                user='root',
                password='',
                charset='utf8mb4'
            )
            print("✅ Connected to MariaDB server successfully")
        except pymysql.Error as e:
            print(f"❌ Cannot connect to MariaDB: {e}")
            print("Please make sure MariaDB is running and root user has access")
            return False

        with connection.cursor() as cursor:
            # Check current authentication plugin for root user
            cursor.execute("SELECT user, plugin, authentication_string FROM mysql.user WHERE user = 'root' AND host = 'localhost'")
            result = cursor.fetchone()

            if result:
                user, plugin, auth_string = result
                print(f"Current root user auth plugin: {plugin}")

                if plugin == 'auth_gssapi_client':
                    print("🔄 Changing root user authentication to mysql_native_password...")

                    # Change authentication method
                    cursor.execute("ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY ''")
                    cursor.execute("FLUSH PRIVILEGES")

                    print("✅ Authentication method changed successfully!")
                    print("Root user now uses mysql_native_password with empty password")
                else:
                    print(f"✅ Root user already uses compatible plugin: {plugin}")
            else:
                print("❌ Root user not found in mysql.user table")

        connection.commit()
        connection.close()

        # Test the connection with new settings
        print("\n🧪 Testing connection with new authentication...")
        test_connection = pymysql.connect(
            host='localhost',
            user='root',
            password='',
            database='editathons',
            charset='utf8mb4'
        )

        with test_connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM wikipedia_asian_month_2025")
            count = cursor.fetchone()[0]
            print(f"✅ Test query successful! Found {count} articles in wikipedia_asian_month_2025")

        test_connection.close()
        print("🎉 MariaDB authentication fixed successfully!")
        return True

    except pymysql.Error as e:
        print(f"❌ MariaDB Error: {e}")
        return False
    except Exception as e:
        print(f"❌ General Error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Fixing MariaDB Authentication for Editathon Review Tool...")
    success = fix_mariadb_auth()
    if success:
        print("\n✅ Authentication fix completed!")
        print("📋 You can now run your Flask application without authentication errors.")
    else:
        print("\n❌ Authentication fix failed.")
        print("Please check your MariaDB configuration and try again.")
        sys.exit(1)
