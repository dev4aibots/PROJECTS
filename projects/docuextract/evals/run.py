from pathlib import Path
import sys,json
sys.path.insert(0,str(Path(__file__).parents[1]/'backend'))
from app.provider import DeterministicExtractor,ExtractionError
from app.verification import verify
root=Path(__file__).parents[1]/'sample_docs';truth=json.loads((root/'ground_truth.json').read_text());passed=0
for name,expected in truth.items():
 try:actual=verify(DeterministicExtractor().extract(name,(root/name).read_bytes())).status
 except ExtractionError:actual='FAILED_EXTRACTION'
 ok=actual==expected;passed+=ok;print(('PASS' if ok else 'FAIL'),name,actual)
print(f'verdict_accuracy: {passed}/{len(truth)}')
