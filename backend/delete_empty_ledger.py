"""Delete ledger transactions with no journal lines."""
import asyncio
from sqlalchemy import select
from app.database import async_session
from app.models.ledger import LedgerTransaction


async def main():
    async with async_session() as db:
        # Find all transactions
        result = await db.execute(select(LedgerTransaction))
        all_txns = result.scalars().all()
        
        empty_txns = []
        for txn in all_txns:
            if not txn.journal_lines or len(txn.journal_lines) == 0:
                empty_txns.append(txn)
        
        if not empty_txns:
            print("✅ No empty transactions found")
            return
        
        print(f"📋 Found {len(empty_txns)} empty transactions\n")
        
        for txn in empty_txns:
            print(f"❌ Deleting empty transaction: {txn.id}")
            print(f"   Description: {txn.description}")
            print(f"   Created: {txn.created_at}")
            await db.delete(txn)
        
        await db.commit()
        print(f"\n✅ Deleted {len(empty_txns)} empty transactions")
        print("\n🔄 Now re-approve the affected invoices to recreate ledger entries")


if __name__ == "__main__":
    asyncio.run(main())
