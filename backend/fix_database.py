import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def fix_database():
    # Connect to MongoDB
    client = AsyncIOMotorClient("mongodb+srv://Rohith:Raju2006@cluster0.e32pg9l.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
    db = client.crop_disease_db
    
    try:
        print("=" * 60)
        print("FIXING DATABASE")
        print("=" * 60)
        
        # 1. Fix indexes
        print("\n📝 Step 1: Fixing database indexes...")
        
        # Drop old indexes if they exist
        try:
            await db.users.drop_index("email_1")
            print("   ✓ Dropped old email_1 index")
        except Exception:
            print("   - email_1 index doesn't exist (OK)")
        
        try:
            await db.users.drop_index("phone_1")
            print("   ✓ Dropped old phone_1 index")
        except Exception:
            print("   - phone_1 index doesn't exist (OK)")
        
        # Create correct indexes
        await db.users.create_index("email", unique=True)
        print("   ✓ Created unique index on email (NOT sparse)")
        
        await db.users.create_index("phone", unique=True, sparse=True)
        print("   ✓ Created sparse unique index on phone")
        
        # 2. Fix location format for existing users
        print("\n📝 Step 2: Fixing user locations...")
        users = await db.users.find({}).to_list(length=None)
        fixed_count = 0
        
        for user in users:
            location = user.get('location')
            needs_update = False
            new_location = None
            
            if location is not None:
                if isinstance(location, dict):
                    # Convert {text: "city"} to "city"
                    new_location = location.get('text', '')
                    needs_update = True
                elif isinstance(location, str):
                    # Already a string, keep it
                    new_location = location
                else:
                    # Unknown type, convert to empty string
                    new_location = ''
                    needs_update = True
            
            if needs_update:
                await db.users.update_one(
                    {"_id": user["_id"]},
                    {"$set": {"location": new_location}}
                )
                fixed_count += 1
                print(f"   ✓ Fixed location for: {user.get('email', 'unknown')}")
        
        if fixed_count == 0:
            print("   ℹ️  No locations needed fixing")
        else:
            print(f"   ✓ Total locations fixed: {fixed_count}")
        
        # 3. Show current database state
        print("\n📝 Step 3: Current database state:")
        all_users = await db.users.find({}, {"email": 1, "phone": 1, "location": 1}).to_list(length=None)
        
        if not all_users:
            print("   ℹ️  No users in database")
        else:
            for user in all_users:
                loc = user.get('location')
                loc_type = type(loc).__name__
                print(f"\n   User: {user.get('email')}")
                print(f"   ├─ Phone: {user.get('phone') or 'None'}")
                print(f"   └─ Location: {loc} (type: {loc_type})")
        
        # 4. Verify indexes
        print("\n📝 Step 4: Verifying indexes...")
        indexes = await db.users.list_indexes().to_list(length=None)
        for idx in indexes:
            idx_name = idx.get('name')
            idx_unique = idx.get('unique', False)
            idx_sparse = idx.get('sparse', False)
            print(f"   ✓ {idx_name}: unique={idx_unique}, sparse={idx_sparse}")
        
        print("\n" + "=" * 60)
        print("✅ DATABASE FIXED SUCCESSFULLY!")
        print("=" * 60)
        print("\n💡 Next steps:")
        print("   1. Restart your backend server")
        print("   2. Test login with existing user")
        print("   3. Test registration with new user")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(fix_database())