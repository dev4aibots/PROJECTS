import re,unicodedata
from pathlib import Path
import yaml
PATTERNS=yaml.safe_load((Path(__file__).parent/'injection_patterns.yaml').read_text())
ZW=re.compile('[\u200b-\u200f\u2060\ufeff]');EMAIL=re.compile(r'\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b');PHONE=re.compile(r'(?<!\w)\+?\d[\d ()-]{8,}\d');SSN=re.compile(r'\b\d{3}-\d{2}-\d{4}\b');KEY=re.compile(r'\b(?:sk-[A-Za-z0-9]{16,}|AKIA[A-Z0-9]{16})\b');CARD=re.compile(r'(?<!\d)(?:\d[ -]?){13,19}(?!\d)')
def luhn(s):
 d=[int(x) for x in re.sub(r'\D','',s)];return len(d)>=13 and sum((x*2-9 if x*2>9 else x*2) if (len(d)-i)%2==0 else x for i,x in enumerate(d))%10==0
def injection(text):
 norm=' '.join(ZW.sub('',unicodedata.normalize('NFKC',text)).lower().split());hits=[]
 for fam,patterns in PATTERNS.items():
  if any(p in norm for p in patterns):hits.append(fam)
 if ZW.search(text) or re.search(r'(?:[A-Za-z0-9+/]{40,}={0,2})',text):hits.append('obfuscation')
 verdict='BLOCK' if len(set(hits))>=2 else 'WARN' if hits else 'PASS';return {'name':'injection','verdict':verdict,'detail':', '.join(sorted(set(hits))) or 'no known pattern family'}
def pii(text):
 found=[]
 for typ,rx in [('email',EMAIL),('phone',PHONE),('ssn',SSN),('api_key',KEY)]:
  for m in rx.finditer(text):
   if typ!='phone' or not luhn(m.group()): found.append((typ,m.group()))
 for m in CARD.finditer(text):
  if luhn(m.group()):found.append(('credit_card',m.group()))
 red=text
 for typ,value in sorted(found,key=lambda x:len(x[1]),reverse=True):red=red.replace(value,f'[REDACTED:{typ}]')
 return found,red
