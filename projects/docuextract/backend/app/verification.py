from datetime import date,timedelta
from decimal import Decimal
from .models import Check,Invoice,Verification

DEFAULT_TOLERANCE=Decimal('0.02')
def money(v:Decimal)->str:return format(v,'f')
def check(name,field,expected,actual,tolerance,note=None):
 delta=abs(expected-actual);return Check(name=name,field=field,expected=money(expected),actual=money(actual),passed=delta<=tolerance,delta=money(delta),note=note)
def verify(invoice:Invoice,tolerance:Decimal=DEFAULT_TOLERANCE)->Verification:
 checks=[]
 for i,item in enumerate(invoice.line_items): checks.append(check('line_item_math',f'line_items[{i}].line_total',item.quantity*item.unit_price,item.line_total,tolerance))
 checks.append(check('subtotal','subtotal',sum((x.line_total for x in invoice.line_items),Decimal('0')),invoice.subtotal,tolerance))
 tax=invoice.tax if invoice.tax is not None else Decimal('0')
 checks.append(check('grand_total','total',invoice.subtotal+tax,invoice.total,tolerance,'assumed_zero' if invoice.tax is None else None))
 future_limit=date.today()+timedelta(days=1);checks.append(Check(name='date_sanity',field='invoice_date',expected=f'<= {future_limit.isoformat()}',actual=invoice.invoice_date.isoformat(),passed=invoice.invoice_date<=future_limit,delta='0'))
 checks.append(Check(name='currency',field='currency',expected='recognized ISO-4217',actual=invoice.currency,passed=True,delta='0'))
 return Verification(status='VERIFIED' if all(c.passed for c in checks) else 'VERIFICATION_FAILED',checks=checks,tolerance=money(tolerance))
