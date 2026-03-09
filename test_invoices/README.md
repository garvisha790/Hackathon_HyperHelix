# Test Invoice Templates

## 📋 Overview
This folder contains 5 test invoice templates covering different GST scenarios for thorough testing.

## 📄 Invoice Templates

### 1. INVOICE_1_PURCHASE_B2B.txt
**Type:** Purchase Invoice (B2B)  
**Scenario:** Standard intra-state purchase with 18% GST  
**Key Features:**
- CGST + SGST (9% each)
- Multiple line items
- Standard 30-day payment terms
- HSN codes included

**Use for testing:**
- Basic invoice upload
- GSTIN validation
- GST calculation
- Purchase expense posting

---

### 2. INVOICE_2_INTERSTATE_IGST.txt
**Type:** Purchase Invoice (Interstate)  
**Scenario:** Interstate purchase from Karnataka to Maharashtra  
**Key Features:**
- IGST (18%) instead of CGST+SGST
- Interstate supply notation
- Higher value invoice (₹1,18,000)

**Use for testing:**
- Interstate detection logic
- IGST handling
- State-wise GST rules

---

### 3. INVOICE_3_LOW_GST.txt
**Type:** Purchase Invoice (Essential Goods)  
**Scenario:** Food supplies with 5% GST rate  
**Key Features:**
- Low GST rate (2.5% CGST + 2.5% SGST)
- Essential commodities (rice, wheat, oil)
- Different HSN codes

**Use for testing:**
- Variable GST rate detection
- Essential goods handling
- Multiple GST rates in system

---

### 4. INVOICE_4_SALES.txt
**Type:** Sales Invoice (B2B Services)  
**Scenario:** Professional IT services sold to customer  
**Key Features:**
- Sales invoice (not purchase)
- Output GST tracking
- Service Accounting Code (SAC)
- Higher value (₹2,36,000)

**Use for testing:**
- Sales vs Purchase detection
- Output GST calculation
- Revenue posting
- Receivables tracking

---

### 5. INVOICE_5_CREDIT_NOTE.txt
**Type:** Credit Note  
**Scenario:** Partial cancellation/refund for Invoice 4  
**Key Features:**
- Negative amounts
- Linked to original invoice
- GST reversal
- Reduces original liability

**Use for testing:**
- Credit note handling
- Negative amount posting
- GST adjustment
- Original invoice linking

---

## 🔄 Converting TXT to PDF

These templates are in `.txt` format. You need to convert them to PDF before uploading to the system.

### Method 1: Using Microsoft Word
1. Open the `.txt` file in Word
2. Adjust font to monospace (Courier New, 10pt) for alignment
3. File → Save As → PDF

### Method 2: Using Google Docs
1. Upload `.txt` to Google Drive
2. Open with Google Docs
3. Change font to monospace (Courier New or Roboto Mono)
4. File → Download → PDF

### Method 3: Online Converter
1. Use any TXT-to-PDF converter online
2. Ensure formatting is preserved

---

## 📊 Expected Test Results

### After uploading all 5 invoices:

**Total Sales:**
- Revenue: ₹2,00,000
- Less Returns: -₹30,000
- **Net: ₹1,70,000**

**Total Purchases:**
- Invoice 1: ₹50,000
- Invoice 2: ₹1,00,000
- Invoice 3: ₹20,000
- **Total: ₹1,70,000**

**GST Summary:**
| Type | CGST | SGST | IGST | Total |
|------|------|------|------|-------|
| Output (Sales) | ₹15,300 | ₹15,300 | ₹0 | ₹30,600 |
| Input (Purchase) | ₹5,000 | ₹5,000 | ₹18,000 | ₹28,000 |
| **Net Liability** | | | | **₹2,600** |

**Outstanding Balances:**
- Receivables: ₹2,00,600 (after credit note)
- Payables: ₹3,09,000

---

## ✅ Testing Sequence

**Recommended order:**
1. Upload Invoice 1 (Basic purchase) - Verify basic flow works
2. Upload Invoice 2 (Interstate) - Test IGST handling
3. Upload Invoice 3 (Low GST) - Test rate variations
4. Upload Invoice 4 (Sales) - Test revenue side
5. Upload Invoice 5 (Credit Note) - Test reversals

**Between each upload:**
- Check dashboard updates
- Verify extracted data
- Confirm ledger entries
- Test copilot queries

---

## 🐛 Known Issues

**Issue:** OCR might not perfectly extract all fields  
**Solution:** Review and edit extracted data before approval

**Issue:** GSTIN validation might fail on demo GSTINs  
**Solution:** These are properly formatted demo GSTINs with valid checksums

**Issue:** Duplicate detection might flag similar invoices  
**Solution:** Use "Upload Anyway" option

---

## 📞 Support

If extraction fails:
1. Check PDF formatting (ensure text is not image)
2. Verify invoice has clear structure
3. Check AWS Textract quota
4. Review backend logs

---

## 🎯 Success Criteria

**After testing all 5 invoices:**
- [ ] All invoices processed successfully (100% success rate)
- [ ] Dashboard shows correct totals
- [ ] GST calculation accurate to ₹1
- [ ] Ledger entries balanced
- [ ] AI copilot can answer questions about this data
- [ ] No console errors
- [ ] Performance acceptable (<30s per invoice)

**You're ready for demo! 🚀**
