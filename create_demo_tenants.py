#!/usr/bin/env python3
"""
Script to create 2 demo tenants for testing purposes.
These tenants will be auto-activated with system-generated passwords.

Usage:
    python3 create_demo_tenants.py
"""

import os
import sys
import django
import random

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smartnyumba_system.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.db import transaction
from authentication.models import Role, Tenant
from properties.models import Property, PropertyBlock
from email_service.email_service import send_creation_email

User = get_user_model()


def create_demo_tenant(email, first_name, last_name, mobile_number, id_number,
                       block_number, house_number):
    """
    Create a demo tenant with auto-generated password and send credentials email.
    """
    try:
        with transaction.atomic():
            # Check if user already exists
            if User.objects.filter(email=email).exists():
                print(f"❌ User with email {email} already exists. Skipping.")
                return False

            # Get tenant role
            role = Role.objects.filter(short_name='tenant').first()
            if not role:
                print("❌ Tenant role not found in database")
                return False

            # Get property block
            block = Property.objects.filter(block_number=block_number).first()
            if not block:
                print(f"❌ Property block {block_number} not found")
                return False

            # Get house
            property_block = PropertyBlock.objects.filter(
                block=block,
                house_number=house_number
            ).first()

            if not property_block:
                print(f"❌ House {house_number} not found in block {block_number}")
                return False

            # Check if house is occupied
            if Tenant.objects.filter(PropertyBlock=property_block).exists():
                print(f"❌ House {house_number} in block {block_number} is already occupied")
                return False

            # Format phone number
            phone_number = str(mobile_number)[-9:]
            formatted_mobile = f'+254{phone_number}'

            # Generate random password
            password = random.randint(1111, 9999)

            # Create User
            user = User(
                email=email,
                username=email,
                firstName=first_name,
                lastName=last_name,
                role=role,
                mobile_number=formatted_mobile,
                status=1,  # Auto-activated
                is_active=True,
                is_staff=False
            )
            user.set_password(str(password))
            user.save()

            # Create Tenant profile
            name = f'{first_name} {last_name}'
            tenant = Tenant.objects.create(
                user=user,
                name=name,
                id_number=id_number,
                email=email,
                is_active=1,  # Auto-approved
                PropertyBlock=property_block
            )

            # Send credentials email
            try:
                send_creation_email(email=email, password=password)
                print(f"✅ Demo tenant created: {name} ({email})")
                print(f"   Block: {block_number}, House: {house_number}")
                print(f"   Password: {password} (sent to email)")
            except Exception as e:
                print(f"⚠️  Tenant created but email failed: {str(e)}")
                print(f"   Password: {password}")

            return True

    except Exception as error:
        print(f"❌ Error creating tenant: {str(error)}")
        return False


def main():
    """
    Create 2 demo tenants.
    IMPORTANT: Modify block_number and house_number to match your database.
    """
    print("=" * 60)
    print("Creating Demo Tenants")
    print("=" * 60)
    print()

    # First, let's show available properties and houses
    print("Checking available properties and houses...")
    print()

    properties = Property.objects.all()[:5]
    if not properties:
        print("❌ No properties found in database. Please add properties first.")
        return

    print("Available properties:")
    for prop in properties:
        print(f"  - Block: {prop.block_number}, Location: {prop.location}")
        houses = PropertyBlock.objects.filter(block=prop)[:3]
        for house in houses:
            occupied = Tenant.objects.filter(PropertyBlock=house).exists()
            status = "OCCUPIED" if occupied else "AVAILABLE"
            print(f"    • House: {house.house_number} [{status}]")
    print()

    # Get first available houses
    available_houses = []
    for prop in properties:
        houses = PropertyBlock.objects.filter(block=prop)
        for house in houses:
            if not Tenant.objects.filter(PropertyBlock=house).exists():
                available_houses.append((prop.block_number, house.house_number))
                if len(available_houses) >= 2:
                    break
        if len(available_houses) >= 2:
            break

    if len(available_houses) < 2:
        print("⚠️  Less than 2 available houses found. Adjust tenants accordingly.")
        if len(available_houses) == 0:
            print("❌ No available houses. All houses are occupied.")
            return

    # Demo tenant 1
    print("Creating Demo Tenant 1...")
    tenant1_created = create_demo_tenant(
        email="demo.tenant1@smartnyumba.com",
        first_name="James",
        last_name="Mwangi",
        mobile_number="0712345678",
        id_number="12345678",
        block_number=available_houses[0][0],
        house_number=available_houses[0][1]
    )
    print()

    # Demo tenant 2 (if we have a second house)
    if len(available_houses) >= 2:
        print("Creating Demo Tenant 2...")
        tenant2_created = create_demo_tenant(
            email="demo.tenant2@smartnyumba.com",
            first_name="Mary",
            last_name="Njeri",
            mobile_number="0723456789",
            id_number="87654321",
            block_number=available_houses[1][0],
            house_number=available_houses[1][1]
        )
        print()

    print("=" * 60)
    print("Demo Tenant Creation Complete!")
    print("=" * 60)
    print()
    print("📧 Login credentials have been sent to the tenants' emails.")
    print("🔐 They can log in to the tenant portal and change their passwords.")


if __name__ == "__main__":
    main()
