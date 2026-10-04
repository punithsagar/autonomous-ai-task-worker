"""
Mock internal company system for demo purposes.
Simulates an invoice tracking system.
"""
from fastapi import FastAPI, HTTPException, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uvicorn


app = FastAPI(title="Company Invoice System")

# In-memory database
invoices_db: List[dict] = []


class Invoice(BaseModel):
    id: Optional[int] = None
    company_name: str
    amount: float
    due_date: str
    entry_date: Optional[str] = None
    status: str = "pending"


@app.get("/", response_class=HTMLResponse)
async def home():
    """Main page with invoice entry form."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Company Invoice System</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 50px auto;
                padding: 20px;
                background-color: #f5f5f5;
            }
            .container {
                background: white;
                padding: 30px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            h1 {
                color: #333;
                border-bottom: 3px solid #4CAF50;
                padding-bottom: 10px;
            }
            .form-group {
                margin-bottom: 20px;
            }
            label {
                display: block;
                margin-bottom: 5px;
                font-weight: bold;
                color: #555;
            }
            input[type="text"],
            input[type="number"],
            input[type="date"] {
                width: 100%;
                padding: 10px;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 14px;
            }
            button {
                background-color: #4CAF50;
                color: white;
                padding: 12px 30px;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                font-size: 16px;
            }
            button:hover {
                background-color: #45a049;
            }
            .success {
                background-color: #d4edda;
                color: #155724;
                padding: 15px;
                border-radius: 4px;
                margin-top: 20px;
                display: none;
            }
            .invoice-list {
                margin-top: 30px;
            }
            .invoice-item {
                background: #f9f9f9;
                padding: 15px;
                margin-bottom: 10px;
                border-radius: 4px;
                border-left: 4px solid #4CAF50;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📋 Invoice Entry System</h1>
            <p>Enter invoice details below</p>

            <form id="invoiceForm" onsubmit="submitInvoice(event)">
                <div class="form-group">
                    <label for="company">Company Name:</label>
                    <input type="text" id="company" name="company_name" required>
                </div>

                <div class="form-group">
                    <label for="amount">Invoice Amount ($):</label>
                    <input type="number" id="amount" name="amount" step="0.01" required>
                </div>

                <div class="form-group">
                    <label for="due_date">Due Date:</label>
                    <input type="date" id="due_date" name="due_date" required>
                </div>

                <button type="submit">Submit Invoice</button>
            </form>

            <div id="successMessage" class="success"></div>

            <div class="invoice-list">
                <h2>Recent Invoices</h2>
                <div id="invoicesList"></div>
            </div>
        </div>

        <script>
            async function submitInvoice(event) {
                event.preventDefault();
                const form = event.target;
                const formData = new FormData(form);

                try {
                    const response = await fetch('/api/invoices', {
                        method: 'POST',
                        body: formData
                    });

                    if (response.ok) {
                        const result = await response.json();
                        document.getElementById('successMessage').style.display = 'block';
                        document.getElementById('successMessage').textContent =
                            `✓ Invoice #${result.id} successfully entered!`;
                        form.reset();
                        loadInvoices();
                    }
                } catch (error) {
                    alert('Error submitting invoice');
                }
            }

            async function loadInvoices() {
                try {
                    const response = await fetch('/api/invoices');
                    const invoices = await response.json();

                    const list = document.getElementById('invoicesList');
                    if (invoices.length === 0) {
                        list.innerHTML = '<p>No invoices entered yet.</p>';
                    } else {
                        list.innerHTML = invoices.map(inv => `
                            <div class="invoice-item">
                                <strong>#${inv.id} - ${inv.company_name}</strong><br>
                                Amount: $${inv.amount} | Due: ${inv.due_date}<br>
                                <small>Entered: ${inv.entry_date}</small>
                            </div>
                        `).join('');
                    }
                } catch (error) {
                    console.error('Error loading invoices:', error);
                }
            }

            // Load invoices on page load
            loadInvoices();
            setInterval(loadInvoices, 3000); // Refresh every 3 seconds
        </script>
    </body>
    </html>
    """


@app.get("/api/invoices")
async def get_invoices():
    """Get all invoices."""
    return invoices_db


@app.post("/api/invoices")
async def create_invoice(
    company_name: str = Form(...),
    amount: float = Form(...),
    due_date: str = Form(...)
):
    """Create a new invoice entry."""
    invoice_id = len(invoices_db) + 1
    invoice = {
        "id": invoice_id,
        "company_name": company_name,
        "amount": amount,
        "due_date": due_date,
        "entry_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": "pending"
    }
    invoices_db.append(invoice)
    return invoice


@app.get("/api/invoices/{invoice_id}")
async def get_invoice(invoice_id: int):
    """Get a specific invoice."""
    for invoice in invoices_db:
        if invoice["id"] == invoice_id:
            return invoice
    raise HTTPException(status_code=404, detail="Invoice not found")


@app.delete("/api/invoices/clear")
async def clear_invoices():
    """Clear all invoices (for testing)."""
    invoices_db.clear()
    return {"message": "All invoices cleared"}


if __name__ == "__main__":
    print("\n" + "="*60)
    print("Mock Company Invoice System")
    print("="*60)
    print("\nAccess the system at: http://localhost:8000")
    print("API docs at: http://localhost:8000/docs")
    print("\nPress Ctrl+C to stop\n")

    uvicorn.run(app, host="0.0.0.0", port=8000)
