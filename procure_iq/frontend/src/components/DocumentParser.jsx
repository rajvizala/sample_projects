import React, { useState } from 'react';
import { FileText, Loader2, CheckCircle } from 'lucide-react';
import { api } from '../utils/api';

const SAMPLE_INVOICE = `INVOICE

From: Apex Manufacturing Co.
Invoice #: INV-2024-0847
Date: January 15, 2024
Due Date: February 14, 2024
Payment Terms: Net 30

Bill To:
TechCorp Industries
123 Industrial Blvd
Chicago, IL 60601

Item Description                  Qty    Unit Price    Total
Steel Plates (Grade A)             50      $185.00    $9,250.00
Aluminum Ingots                    30      $120.00    $3,600.00
Copper Wire (1mm)                 100      $275.00   $27,500.00

Subtotal:  $40,350.00
Tax (8%):   $3,228.00
Total:     $43,578.00

Amount Due: $43,578.00`;

export default function DocumentParser() {
  const [text, setText] = useState('');
  const [docType, setDocType] = useState('invoice');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleParse = async () => {
    if (!text.trim()) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await api.parseDocument({ text, doc_type: docType });
      setResult(res);
    } catch (err) {
      setError(err.message);
    }
    setLoading(false);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold">Document Parser</h2>
          <p className="text-sm text-slate-400 mt-1">Extract structured data from invoices and purchase orders using NLP.</p>
        </div>
        <button onClick={() => setText(SAMPLE_INVOICE)}
          className="text-xs px-3 py-1.5 bg-indigo-500/10 text-indigo-400 rounded-lg hover:bg-indigo-500/20">
          Load Sample
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="space-y-4">
          <div className="flex gap-2">
            {['invoice', 'po', 'receipt'].map((t) => (
              <button key={t} onClick={() => setDocType(t)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium capitalize ${
                  docType === t ? 'bg-indigo-600 text-white' : 'bg-slate-800 text-slate-400 hover:text-slate-200'
                }`}>{t}</button>
            ))}
          </div>
          <textarea
            value={text} onChange={(e) => setText(e.target.value)}
            placeholder="Paste invoice or purchase order text here..."
            rows={18}
            className="w-full bg-slate-900 border border-slate-800 rounded-xl px-4 py-3 text-sm font-mono focus:outline-none focus:border-indigo-500 resize-none"
          />
          <button onClick={handleParse} disabled={loading || !text.trim()}
            className="w-full bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-700 text-white font-medium py-2.5 rounded-lg flex items-center justify-center gap-2">
            {loading ? <Loader2 size={18} className="animate-spin" /> : <FileText size={18} />}
            {loading ? 'Parsing...' : 'Parse Document'}
          </button>
          {error && <div className="p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400 text-sm">{error}</div>}
        </div>

        {result && (
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
            <div className="flex items-center gap-2 text-emerald-400 mb-2">
              <CheckCircle size={18} />
              <span className="font-medium">Parsed Successfully</span>
              <span className="text-xs text-slate-500 ml-auto">Confidence: {(result.confidence * 100).toFixed(0)}%</span>
            </div>

            <div className="grid grid-cols-2 gap-3 text-sm">
              {result.vendor_name && <Field label="Vendor" value={result.vendor_name} />}
              {result.invoice_number && <Field label="Invoice #" value={result.invoice_number} />}
              {result.po_number && <Field label="PO #" value={result.po_number} />}
              {result.date && <Field label="Date" value={result.date} />}
              {result.due_date && <Field label="Due Date" value={result.due_date} />}
              {result.payment_terms && <Field label="Terms" value={result.payment_terms} />}
              <Field label="Currency" value={result.currency} />
              {result.subtotal != null && <Field label="Subtotal" value={`$${result.subtotal.toLocaleString()}`} />}
              {result.tax != null && <Field label="Tax" value={`$${result.tax.toLocaleString()}`} />}
              {result.total != null && <Field label="Total" value={`$${result.total.toLocaleString()}`} highlight />}
            </div>

            {result.line_items.length > 0 && (
              <div>
                <h4 className="text-sm font-medium text-slate-400 mb-2">Line Items</h4>
                <div className="bg-slate-800/50 rounded-lg overflow-hidden">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-slate-700">
                        <th className="text-left p-2 text-slate-400 font-medium">Item</th>
                        <th className="text-right p-2 text-slate-400 font-medium">Qty</th>
                        <th className="text-right p-2 text-slate-400 font-medium">Unit</th>
                        <th className="text-right p-2 text-slate-400 font-medium">Total</th>
                      </tr>
                    </thead>
                    <tbody>
                      {result.line_items.map((item, i) => (
                        <tr key={i} className="border-b border-slate-700/50">
                          <td className="p-2">{item.item_name}</td>
                          <td className="p-2 text-right text-slate-300">{item.quantity}</td>
                          <td className="p-2 text-right text-slate-300">${item.unit_price.toLocaleString()}</td>
                          <td className="p-2 text-right font-medium">${item.total.toLocaleString()}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function Field({ label, value, highlight }) {
  return (
    <div className="bg-slate-800/50 rounded-lg p-2.5">
      <p className="text-xs text-slate-500 mb-0.5">{label}</p>
      <p className={`font-medium ${highlight ? 'text-indigo-400' : ''}`}>{value}</p>
    </div>
  );
}
