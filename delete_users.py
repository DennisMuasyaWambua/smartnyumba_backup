#!/usr/bin/env python3
"""
Script to delete specific users from the Smart Nyumba database
"""
import psycopg2
from psycopg2.extras import RealDictCursor

# Database connection
DATABASE_URL = "postgresql://postgres:NrBvzlxjzBxcWFqOfaFYqUVTyiBLbSJZ@shuttle.proxy.rlwy.net:11362/railway"

# Users to delete
USERS_TO_DELETE = [
    "mkanto777@gmail.com",
    "wamuasya23@gmail.com"
]

def delete_users():
    try:
        print("Connecting to database...")
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        for email in USERS_TO_DELETE:
            print(f"\n{'='*60}")
            print(f"Processing: {email}")
            print('='*60)

            # Check if user exists
            cursor.execute("SELECT id, email, role_id FROM \"user\" WHERE email = %s", (email,))
            user = cursor.fetchone()

            if not user:
                print(f"❌ User {email} not found in database")
                continue

            user_id = user['id']
            print(f"✓ Found user ID: {user_id}")

            # Delete related records first (to avoid foreign key constraints)

            # Delete from tenant table
            cursor.execute("DELETE FROM tenant WHERE user_id = %s", (user_id,))
            deleted_tenants = cursor.rowcount
            if deleted_tenants > 0:
                print(f"  ✓ Deleted {deleted_tenants} tenant record(s)")

            # Delete from admin table
            cursor.execute("DELETE FROM admin WHERE user_id = %s", (user_id,))
            deleted_admins = cursor.rowcount
            if deleted_admins > 0:
                print(f"  ✓ Deleted {deleted_admins} admin record(s)")

            # Delete from block_landlord table and handle property relationships
            try:
                # First, remove property relationships
                cursor.execute("DELETE FROM block_landlord_property WHERE blocklandlord_id IN (SELECT id FROM block_landlord WHERE user_id = %s)", (user_id,))
                print(f"  ✓ Cleared landlord-property relationships")
            except psycopg2.Error:
                conn.rollback()

            # Check how many landlord records exist
            cursor.execute("SELECT COUNT(*) FROM block_landlord WHERE user_id = %s", (user_id,))
            landlord_count = cursor.fetchone()['count']
            print(f"  Found {landlord_count} landlord record(s)")

            cursor.execute("DELETE FROM block_landlord WHERE user_id = %s", (user_id,))
            deleted_landlords = cursor.rowcount
            if deleted_landlords > 0:
                print(f"  ✓ Deleted {deleted_landlords} landlord record(s)")

            # Verify deletion
            cursor.execute("SELECT COUNT(*) FROM block_landlord WHERE user_id = %s", (user_id,))
            remaining = cursor.fetchone()['count']
            if remaining > 0:
                print(f"  ⚠️  Warning: {remaining} landlord record(s) still remain!")

            # Delete from staff_accounts table (try different table names)
            try:
                cursor.execute("DELETE FROM staff_accounts WHERE user_id = %s", (user_id,))
                deleted_accounts = cursor.rowcount
                if deleted_accounts > 0:
                    print(f"  ✓ Deleted {deleted_accounts} accounts record(s)")
            except psycopg2.Error:
                conn.rollback()  # Rollback to continue
                try:
                    cursor.execute("DELETE FROM accounts WHERE user_id = %s", (user_id,))
                    deleted_accounts = cursor.rowcount
                    if deleted_accounts > 0:
                        print(f"  ✓ Deleted {deleted_accounts} accounts record(s)")
                except psycopg2.Error:
                    conn.rollback()  # Rollback to continue

            # Delete from caretaker table
            try:
                cursor.execute("DELETE FROM caretaker WHERE user_id = %s", (user_id,))
                deleted_caretakers = cursor.rowcount
                if deleted_caretakers > 0:
                    print(f"  ✓ Deleted {deleted_caretakers} caretaker record(s)")
            except psycopg2.Error:
                conn.rollback()  # Rollback to continue

            # Delete OTP records
            try:
                cursor.execute("DELETE FROM otp_verification_code WHERE email = %s", (email,))
                deleted_otps = cursor.rowcount
                if deleted_otps > 0:
                    print(f"  ✓ Deleted {deleted_otps} OTP record(s)")
            except psycopg2.Error:
                conn.rollback()

            # Delete login OTP records
            try:
                cursor.execute("DELETE FROM login_otp WHERE mobile_number = (SELECT mobile_number FROM \"user\" WHERE id = %s)", (user_id,))
                deleted_login_otps = cursor.rowcount
                if deleted_login_otps > 0:
                    print(f"  ✓ Deleted {deleted_login_otps} login OTP record(s)")
            except psycopg2.Error:
                conn.rollback()

            # Delete activation payments
            try:
                cursor.execute("DELETE FROM activation_transactions WHERE activation_payment_id IN (SELECT id FROM activation_payments WHERE user_id = %s)", (user_id,))
                deleted_act_trans = cursor.rowcount
                if deleted_act_trans > 0:
                    print(f"  ✓ Deleted {deleted_act_trans} activation transaction(s)")

                cursor.execute("DELETE FROM activation_payments WHERE user_id = %s", (user_id,))
                deleted_act_payments = cursor.rowcount
                if deleted_act_payments > 0:
                    print(f"  ✓ Deleted {deleted_act_payments} activation payment(s)")
            except psycopg2.Error:
                conn.rollback()

            # Delete JWT tokens
            try:
                cursor.execute("DELETE FROM token_blacklist_outstandingtoken WHERE user_id = %s", (user_id,))
                deleted_tokens = cursor.rowcount
                if deleted_tokens > 0:
                    print(f"  ✓ Deleted {deleted_tokens} JWT token(s)")
            except psycopg2.Error:
                conn.rollback()

            # Finally, delete the user
            cursor.execute("DELETE FROM \"user\" WHERE id = %s", (user_id,))
            print(f"  ✅ Deleted user account: {email}")

        # Commit all changes
        conn.commit()
        print(f"\n{'='*60}")
        print("✅ ALL USERS DELETED SUCCESSFULLY!")
        print('='*60)

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
    print("\n⚠️  WARNING: This will permanently delete users and all related data!")
    print(f"Users to delete: {', '.join(USERS_TO_DELETE)}")
    response = input("\nAre you sure you want to continue? (yes/no): ")

    if response.lower() == 'yes':
        delete_users()
    else:
        print("❌ Operation cancelled")
