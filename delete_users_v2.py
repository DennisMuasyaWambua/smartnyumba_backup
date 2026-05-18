#!/usr/bin/env python3
"""
Script to delete specific users from the Smart Nyumba database - Version 2
Uses raw SQL with CASCADE where possible
"""
import psycopg2

# Database connection
DATABASE_URL = "postgresql://postgres:NrBvzlxjzBxcWFqOfaFYqUVTyiBLbSJZ@shuttle.proxy.rlwy.net:11362/railway"

# Users to delete
USERS_TO_DELETE = [
    "mkanto777@gmail.com",
    "wamuasya23@gmail.com"
]

def delete_user_simple(email):
    """Delete a single user using a simpler approach"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = False
        cursor = conn.cursor()

        print(f"\n{'='*60}")
        print(f"Deleting: {email}")
        print('='*60)

        # Get user ID
        cursor.execute("SELECT id FROM \"user\" WHERE email = %s", (email,))
        result = cursor.fetchone()

        if not result:
            print(f"❌ User {email} not found")
            return

        user_id = result[0]
        print(f"✓ Found user ID: {user_id}")

        # Delete all related records manually in correct order
        tables_to_clean = [
            ("block_landlord_property", "blocklandlord_id IN (SELECT id FROM block_landlord WHERE user_id = %s)"),
            ("activation_transactions", "activation_payment_id IN (SELECT id FROM activation_payments WHERE user_id = %s)"),
            ("activation_payments", "user_id = %s"),
            ("otp_verification_code", "email = %s"),  # Use email for OTP
            ("login_otp", "mobile_number IN (SELECT mobile_number FROM \"user\" WHERE id = %s)"),
            ("token_blacklist_outstandingtoken", "user_id = %s"),
            ("block_landlord", "user_id = %s"),
            ("tenant", "user_id = %s"),
            ("admin", "user_id = %s"),
            ("caretaker", "user_id = %s"),
        ]

        for table, condition in tables_to_clean:
            try:
                if table == "otp_verification_code":
                    query = f"DELETE FROM {table} WHERE {condition}"
                    cursor.execute(query, (email,))
                else:
                    query = f"DELETE FROM {table} WHERE {condition}"
                    cursor.execute(query, (user_id,))

                deleted = cursor.rowcount
                if deleted > 0:
                    print(f"  ✓ Deleted {deleted} record(s) from {table}")
            except psycopg2.Error as e:
                if "does not exist" in str(e):
                    pass  # Table doesn't exist, skip
                else:
                    print(f"  ⚠️  Error cleaning {table}: {e}")
                conn.rollback()

        # Finally delete the user
        cursor.execute("DELETE FROM \"user\" WHERE id = %s", (user_id,))
        print(f"  ✅ Deleted user account: {email}")

        # Commit the transaction
        conn.commit()
        print(f"✅ Successfully deleted {email}")

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"❌ Error deleting {email}: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()

def main():
    print("\n⚠️  WARNING: This will permanently delete users and all related data!")
    print(f"Users to delete: {', '.join(USERS_TO_DELETE)}")

    for email in USERS_TO_DELETE:
        delete_user_simple(email)

    print(f"\n{'='*60}")
    print("✅ PROCESS COMPLETED!")
    print('='*60)

if __name__ == "__main__":
    response = input("\nAre you sure you want to continue? (yes/no): ")
    if response.lower() == 'yes':
        main()
    else:
        print("❌ Operation cancelled")
