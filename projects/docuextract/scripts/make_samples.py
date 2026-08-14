#!/usr/bin/env python3
from pathlib import Path
import json
from reportlab.pdfgen import canvas
from PIL import Image,ImageDraw
root=Path(__file__).parents[1]/'sample_docs';root.mkdir(exist_ok=True)
def pdf(name,total='11,800.00',line='3,000.00'):
 c=canvas.Canvas(str(root/name));c.setFont('Helvetica-Bold',18);c.drawString(70,780,'NORTHSTAR INSTRUMENTS — INVOICE');c.setFont('Helvetica',12);rows=['Invoice INV-2026-0042 · 2026-08-01','Industrial Sensor   10 × 800.00   8,000.00',f'Calibration Kit      2 × 1,500.00   {line}','Subtotal 11,000.00','Tax 800.00',f'TOTAL {total} USD'];
 for i,x in enumerate(rows):c.drawString(70,730-i*42,x)
 c.save()
pdf('clean_invoice.pdf');pdf('broken_total_invoice.pdf','12,800.00');pdf('broken_lineitem_invoice.pdf','11,800.00','3,200.00')
im=Image.new('RGB',(900,1100),'white');d=ImageDraw.Draw(im);d.text((70,80),'NORTHSTAR INSTRUMENTS — INVOICE\n\nINV-2026-0042  2026-08-01\n\nIndustrial Sensor 10 x 800 = 8,000\nCalibration Kit 2 x 1,500 = 3,000\n\nSubtotal 11,000\nTax 800\nTOTAL 11,800 USD',fill='black',spacing=20);im.save(root/'receipt_photo.png')
cat=Image.new('RGB',(500,400),'#d5c3a1');dc=ImageDraw.Draw(cat);dc.ellipse((120,80,380,340),fill='#777');dc.polygon([(150,120),(180,30),(230,110)],fill='#777');dc.polygon([(270,110),(330,30),(350,130)],fill='#777');cat.save(root/'cat.png')
truth={'clean_invoice.pdf':'VERIFIED','broken_total_invoice.pdf':'VERIFICATION_FAILED','broken_lineitem_invoice.pdf':'VERIFICATION_FAILED','receipt_photo.png':'VERIFIED','cat.png':'FAILED_EXTRACTION'};(root/'ground_truth.json').write_text(json.dumps(truth,indent=2))
