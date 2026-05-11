#!/usr/bin/env python3
"""
Script to create an approver account in the Smart Nyumba database
"""
import psycopg2
from psycopg2.extras import RealDictCursor
import random
import hashlib

# Database connection
DATABASE_URL = "postgresql://postgres:NrBvzlxjzBxcWFqOfaFYqUVTyiBLbSJZ@shuttle.proxy.rlwy.net:11362/railway"

# Approver details
APPROVER_EMAIL = "muasyathegreat4@gmail.com"
APPROVER_NAME = "System Approver"
APPROVER_PHONE = "712345678"
APPROVER_ID_NUMBER = "12345678"
MOBILE_NUMBER = "254712345678"

def hash_password(password):
    """Hash password using Django's PBKDF2 algorithm"""
    import hashlib
    import base64

    algorithm = 'pbkdf2_sha256'
    iterations = 600000  # Django 4.x default
    salt = base64.b64encode(hashlib.sha256(str(random.random()).encode()).digest())[:12].decode()

    hash_obj = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), iterations)
    hash_b64 = base64.b64encode(hash_obj).decode().strip()

    return f"{algorithm}${iterations}${salt}${hash_b64}"

def create_approver():
    try:
        # Connect to database
        print("Connecting to database...")
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Check if user already exists
        print(f"\nChecking if {APPROVER_EMAIL} already exists...")
        cursor.execute("SELECT id, email, status FROM \"user\" WHERE email = %s", (APPROVER_EMAIL,))
        existing_user = cursor.fetchone()

        if existing_user:
            print(f"\n✅ User already exists!")
            print(f"   User ID: {existing_user['id']}")
            print(f"   Email: {existing_user['email']}")
            print(f"   Status: {existing_user['status']}")

            # Check if admin profile exists
            cursor.execute("SELECT id FROM admin WHERE email = %s", (APPROVER_EMAIL,))
            admin_profile = cursor.fetchone()

            if admin_profile:
                print(f"   Admin Profile ID: {admin_profile['id']}")
                print("\n✅ Approver account already fully configured!")
            else:
                print("\n⚠️  User exists but admin profile missing. Creating admin profile...")
                cursor.execute("""
                    INSERT INTO admin (user_id, email, name, phone_number, id_number, is_active)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (existing_user['id'], APPROVER_EMAIL, APPROVER_NAME, APPROVER_PHONE, APPROVER_ID_NUMBER, 1))
                admin_id = cursor.fetchone()['id']
                conn.commit()
                print(f"   ✅ Admin profile created with ID: {admin_id}")

            cursor.close()
            conn.close()
            return

        # Get admin role ID
        print("\nFetching admin role...")
        cursor.execute("SELECT id FROM role WHERE short_name = %s", ('admin',))
        role = cursor.fetchone()

        if not role:
            print("❌ Admin role not found in database!")
            cursor.close()
            conn.close()
            return

        role_id = role['id']
        print(f"   Admin role ID: {role_id}")

        # Generate password
        password = str(random.randint(100000, 999999))
        hashed_password = hash_password(password)

        print("\nCreating user account...")
        # Create User
        cursor.execute("""
            INSERT INTO "user" (
                username, email, password, role_id, mobile_number,
                status, is_active, is_staff, is_superuser,
                first_name, last_name, date_joined
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
            RETURNING id
        """, (
            APPROVER_EMAIL,  # username
            APPROVER_EMAIL,  # email
            hashed_password,  # password
            role_id,  # role_id
            MOBILE_NUMBER,  # mobile_number
            1,  # status (activated)
            True,  # is_active
            True,  # is_staff
            False,  # is_superuser
            'System',  # first_name
            'Approver'  # last_name
        ))

        user_id = cursor.fetchone()['id']
        print(f"   ✅ User created with ID: {user_id}")

        # Create staffAdmin profile
        print("\nCreating admin profile...")
        cursor.execute("""
            INSERT INTO admin (user_id, email, name, phone_number, id_number, is_active)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (user_id, APPROVER_EMAIL, APPROVER_NAME, APPROVER_PHONE, APPROVER_ID_NUMBER, 1))

        admin_id = cursor.fetchone()['id']
        print(f"   ✅ Admin profile created with ID: {admin_id}")

        # Commit transaction
        conn.commit()

        print("\n" + "="*60)
        print("✅ APPROVER ACCOUNT CREATED SUCCESSFULLY!")
        print("="*60)
        print(f"Email:    {APPROVER_EMAIL}")
        print(f"Password: {password}")
        print(f"User ID:  {user_id}")
        print(f"Admin ID: {admin_id}")
        print(f"Status:   Activated")
        print("="*60)
        print(f"\n⚠️  IMPORTANT: Save this password: {password}")
        print("="*60)

        cursor.close()
        conn.close()

    except psycopg2.Error as e:
        print(f"\n❌ Database error: {e}")
        if 'conn' in locals():
            conn.rollback()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    create_approver()
