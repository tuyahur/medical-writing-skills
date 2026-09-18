"""统计已核对的Discussion句子表；不自动判断句子论证质量。"""
import argparse,csv,json,re
from collections import Counter
from pathlib import Path

MARKERS=['associated with','our findings','our results','these findings','we found','we observed','we did not','no association','no associations','no evidence','consistent with','inconsistent with','compared with','compared to','in contrast','however','although','nevertheless','whereas','therefore','thus','furthermore','in addition','for example','for instance','may','might','could','suggest','suggests','suggesting','likely','potential','potentially','residual confounding','reverse causation','measurement error','misclassification','sensitivity analysis','sensitivity analyses','future studies','further studies','in conclusion','in summary']
FRAMES={
 '内部发现：we found/observed/reported that':r'\bwe (?:found|observed|reported) that\b',
 '研究发现回指：our findings/results':r'\bour (?:findings|results)\b',
 '否定发现：did not/was not/were not':r'\b(?:did|was|were) not\b',
 '证据不足：no evidence/unclear/limited data':r'\b(?:no evidence|unclear|limited data|more limited data)\b',
 '可能解释：may/might/could + be/explain/reflect/affect':r'\b(?:may|might|could) (?:be|explain|reflect|affect)\b',
 '对照引导：compared with/to':r'\bcompared (?:with|to)\b',
 '文献相容：consistent/inconsistent with':r'\b(?:consistent|inconsistent) with\b',
 '未来研究：future/further + studies/work/research':r'\b(?:future|further) (?:studies|work|research)\b',
 '优势引导：strengths of/include/are':r'\bstrengths (?:of|include|are)\b',
 '限制作路标：limitations':r'\blimitations\b'}
def analyze(rows):
 assert rows and len({r['id'] for r in rows})==len(rows),'句子ID必须非空且唯一'
 keys=sorted({r['paper'] for r in rows});wc={k:Counter() for k in keys}
 for r in rows:wc[r['paper']].update(re.findall(r"[A-Za-z]+(?:[-’'][A-Za-z]+)*",r['text'].lower()))
 totals={k:sum(wc[k].values()) for k in keys};total=sum(totals.values());allwords=sum(wc.values(),Counter())
 phrases=[]
 for label,rx in [(x,r'\b'+re.escape(x)+r'\b') for x in MARKERS]+list(FRAMES.items()):
  counts={k:0 for k in keys};ids=[];kind='词组/标记' if label in MARKERS else '规则句架'
  for r in rows:
   matches=list(re.finditer(rx,r['text'].lower()))
   if matches:counts[r['paper']]+=len(matches);ids.append(r['id'])
  phrases.append({'expression':label,'kind':kind,'count':sum(counts.values()),'papers':sum(c>0 for c in counts.values()),'per_1000':round(sum(counts.values())*1000/total,3),'by_paper':counts,'occurrence_ids':ids})
 return {'paper_count':len(keys),'paragraph_count':len({(r['paper'],r['paragraph']) for r in rows}),'sentence_count':len(rows),'token_count':total,'tokens_by_paper':totals,'word_rows':[{'word':w,'count':n,'papers':sum(w in wc[k] for k in keys),'per_1000':round(n*1000/total,3),'by_paper':{k:wc[k][w] for k in keys}} for w,n in allwords.most_common()],'expressions':phrases}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('sentences',type=Path);ap.add_argument('output',type=Path);a=ap.parse_args()
 rows=json.loads(a.sentences.read_text(encoding='utf-8'));d=analyze(rows);a.output.mkdir(parents=True,exist_ok=True)
 (a.output/'statistics.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
 for name,rs,first in [('词汇频次.csv',d['word_rows'],'word'),('表达与句架频次.csv',d['expressions'],'expression')]:
  keys=sorted(d['tokens_by_paper'])
  with (a.output/name).open('w',encoding='utf-8-sig',newline='') as f:
   w=csv.writer(f);w.writerow([first,'总次数','出现论文数','每千词频次']+keys+['对应句子ID'])
   for r in rs:w.writerow([r[first],r['count'],r['papers'],r['per_1000']]+[r['by_paper'][k] for k in keys]+[';'.join(r.get('occurrence_ids',[]))])
 print(json.dumps({k:d[k] for k in ['paper_count','paragraph_count','sentence_count','token_count']},ensure_ascii=False))
if __name__=='__main__':main()
