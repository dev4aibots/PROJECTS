from datetime import date
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator

ISO_CODES={'USD','EUR','GBP','INR','JPY','CAD','AUD','BRL','CHF'}
class LineItem(BaseModel):
 description:str=Field(min_length=1);quantity:Decimal=Field(ge=0);unit_price:Decimal=Field(ge=0);line_total:Decimal=Field(ge=0)
class Invoice(BaseModel):
 invoice_number:str=Field(min_length=1);vendor_name:str=Field(min_length=1);invoice_date:date;currency:str;subtotal:Decimal=Field(ge=0);tax:Decimal|None=Field(default=None,ge=0);total:Decimal=Field(ge=0);line_items:list[LineItem]=Field(min_length=1);vendor_address:str|None=None;customer_name:str|None=None
 @field_validator('currency')
 @classmethod
 def valid_currency(cls,v:str)->str:
  v=v.upper()
  if v not in ISO_CODES: raise ValueError('unrecognized ISO-4217 currency')
  return v
class Check(BaseModel):
 name:str;field:str;expected:str;actual:str;passed:bool;delta:str;note:str|None=None
class Verification(BaseModel):
 status:str;checks:list[Check];tolerance:str
