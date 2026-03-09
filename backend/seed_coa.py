"""Quick script to seed chart of accounts for existing tenant."""
import asyncio
import sys
from sqlalchemy import select
from app.database import async_session
from app.models.tenant import Tenant
from seed.chart_of_accounts import seed_chart_of_accounts


async def main():
    async with async_session() as db:
        # Get all tenants
        result = await db.execute(select(Tenant))
        tenants = result.scalars().all()
        
        if not tenants:
            print("❌ No tenants found")
            sys.exit(1)
        
        print(f"📋 Found {len(tenants)} tenant(s)")
        
        for tenant in tenants:
            print(f"\n🔄 Processing: {tenant.name} (ID: {tenant.id})")
            print("🌱 Seeding chart of accounts...")
            
            try:
                await seed_chart_of_accounts(db, tenant.id)
                await db.commit()
                print(f"✅ Chart of accounts seeded for {tenant.name}")
            except Exception as e:
                print(f"⚠️  Error or already seeded: {e}")
                await db.rollback()
        
        print("\n✅ All tenants processed!")


if __name__ == "__main__":
    asyncio.run(main())
