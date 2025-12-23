#!/usr/bin/env python3
"""
Script untuk menambahkan sample roles ke database
"""
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.queries.role_queries import create_role, get_all_roles

def setup_sample_roles():
    """Setup sample roles for the game"""
    
    sample_roles = [
        {
            'name': 'Bronze Member',
            'price': 5000,
            'description': 'Basic membership with small perks',
            'color': '#CD7F32'
        },
        {
            'name': 'Silver Member', 
            'price': 15000,
            'description': 'Silver membership with moderate perks',
            'color': '#C0C0C0'
        },
        {
            'name': 'Gold Member',
            'price': 30000,
            'description': 'Gold membership with great perks',
            'color': '#FFD700'
        },
        {
            'name': 'Platinum Member',
            'price': 50000,
            'description': 'Platinum membership with premium perks',
            'color': '#E5E4E2'
        },
        {
            'name': 'Diamond Member',
            'price': 100000,
            'description': 'Diamond membership with exclusive perks',
            'color': '#B9F2FF'
        },
        {
            'name': 'Warrior',
            'price': 25000,
            'description': 'Combat specialist role',
            'color': '#FF4500'
        },
        {
            'name': 'Mage',
            'price': 25000,
            'description': 'Magic specialist role',
            'color': '#4169E1'
        },
        {
            'name': 'Archer',
            'price': 25000,
            'description': 'Ranged combat specialist role',
            'color': '#228B22'
        },
        {
            'name': 'Guild Leader',
            'price': 200000,
            'description': 'Leadership role with special privileges',
            'color': '#8B0000'
        },
        {
            'name': 'Veteran',
            'price': 75000,
            'description': 'Experienced player role',
            'color': '#800080'
        }
    ]
    
    print("Setting up sample roles...")
    created_count = 0
    
    # Get existing roles to avoid duplicates
    existing_roles = get_all_roles()
    existing_names = [role[1] for role in existing_roles]
    
    for role_data in sample_roles:
        if role_data['name'] not in existing_names:
            try:
                role_id = create_role(
                    name=role_data['name'],
                    price=role_data['price'],
                    description=role_data['description'],
                    color=role_data['color']
                )
                print(f"✅ Created role: {role_data['name']} (ID: {role_id})")
                created_count += 1
            except Exception as e:
                print(f"❌ Failed to create role {role_data['name']}: {e}")
        else:
            print(f"⏭️  Role {role_data['name']} already exists, skipping...")
    
    print(f"\n🎉 Setup complete! Created {created_count} new roles.")
    
    # Display all roles
    print("\n📋 All available roles:")
    all_roles = get_all_roles()
    for role in all_roles:
        print(f"  • {role[1]} - {role[2]:,} ACR - {role[3] or 'No description'}")

if __name__ == "__main__":
    setup_sample_roles()