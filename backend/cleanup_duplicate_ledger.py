"""Clean up duplicate ledger transactions for same invoice."""
import asyncio
from sqlalchemy import select, func, delete
from app.database import async_session
from app.models.ledger import LedgerTransaction


async def main():
    async with async_session() as db:
        # Find invoices with multiple transactions
        stmt = select(
            LedgerTransaction.canonical_invoice_id,
            func.count(LedgerTransaction.id).label('count')
        ).where(
            LedgerTransaction.canonical_invoice_id.is_not(None)
        ).group_by(
            LedgerTransaction.canonical_invoice_id
        ).having(
            func.count(LedgerTransaction.id) > 1
        )
        
        result = await db.execute(stmt)
        duplicates = result.all()
        
        if not duplicates:
            print("✅ No duplicate transactions found")
            return
        
        print(f"📋 Found {len(duplicates)} invoices with duplicate postings\n")
        
        for invoice_id, count in duplicates:
            print(f"🔍 Invoice ID: {invoice_id} has {count} transactions")
            
            # Get all transactions for this invoice
            txn_result = await db.execute(
                select(LedgerTransaction)
                .where(LedgerTransaction.canonical_invoice_id == invoice_id)
                .order_by(LedgerTransaction.created_at.asc())
            )
            transactions = txn_result.scalars().all()
            
            # Keep the one with journal lines, prefer latest if multiple have data
            transactions_with_lines = [t for t in transactions if t.journal_lines and len(t.journal_lines) > 0]
            
            if transactions_with_lines:
                # Keep the latest complete transaction
                keep = transactions_with_lines[-1]
            else:
                # If none have journal lines, keep the first one
                keep = transactions[0]
            
            to_delete = [t for t in transactions if t.id != keep.id]
            
            print(f"   ✅ Keeping: Transaction {keep.id} (created {keep.created_at})")
            for txn in to_delete:
                print(f"   ❌ Deleting: Transaction {txn.id} (created {txn.created_at})")
                await db.delete(txn)
            
            print()
        
        await db.commit()
        print("✅ Cleanup complete!")


if __name__ == "__main__":
    asyncio.run(main())
