from datetime import date,timedelta
from decimal import Decimal
import pytest
from pydantic import ValidationError
from app.models import Invoice,LineItem
from app.verification import verify
D=Decimal
def inv(**kw):
 d=dict(invoice_number='1',vendor_name='V',invoice_date=date.today(),currency='USD',subtotal=D('10.00'),tax=D('1'),total=D('11'),line_items=[LineItem(description='x',quantity=D('2'),unit_price=D('5'),line_total=D('10'))]);d.update(kw);return Invoice(**d)
def test_clean_verified():assert verify(inv()).status=='VERIFIED'
def test_tolerance_boundaries():
 assert verify(inv(total=D('11.019'))).status=='VERIFIED';assert verify(inv(total=D('11.021'))).status=='VERIFICATION_FAILED'
def test_broken_line_exact_field():
 r=verify(inv(line_items=[LineItem(description='x',quantity=D('2'),unit_price=D('5'),line_total=D('9'))],subtotal=D('9'),total=D('10')));assert r.checks[0].field=='line_items[0].line_total' and not r.checks[0].passed
def test_zero_quantity():assert verify(inv(subtotal=D('0'),tax=None,total=D('0'),line_items=[LineItem(description='x',quantity=D('0'),unit_price=D('999'),line_total=D('0'))])).status=='VERIFIED'
def test_negative_rejected():
 with pytest.raises(ValidationError):LineItem(description='x',quantity=D('1'),unit_price=D('-1'),line_total=D('1'))
def test_missing_tax_assumed_zero():assert verify(inv(tax=None,total=D('10'))).checks[2].note=='assumed_zero'
def test_huge_decimal_exact():
 n=D('999999999999999999.99');assert verify(inv(subtotal=n,tax=D('0'),total=n,line_items=[LineItem(description='x',quantity=D('1'),unit_price=n,line_total=n)])).status=='VERIFIED'
def test_future_date_fails():assert verify(inv(invoice_date=date.today()+timedelta(days=2))).status=='VERIFICATION_FAILED'
def test_bad_currency_rejected():
 with pytest.raises(ValidationError):inv(currency='ZZZ')
def test_decimal_never_float():assert isinstance(inv().total,Decimal)
