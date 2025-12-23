import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.queries.role_queries import create_role

def add_special_roles():
    """Add owner and Admin roles that cannot be purchased"""
    # Owner role - tidak bisa dibeli (is_buy = 0)
    owner_id = create_role(
        name="Owner",
        price=0,
        description="Bot owner with full privileges",
        color="#FF0000",
        is_buy=0
    )
    
    # Admin role - tidak bisa dibeli (is_buy = 0)  
    admin_id = create_role(
        name="Admin", 
        price=0,
        description="Bot administrator with management privileges",
        color="#FF4500",
        is_buy=0
    )
    
    print(f"Created Owner role (ID: {owner_id}) and Admin role (ID: {admin_id})")

if __name__ == "__main__":
    add_special_roles()
