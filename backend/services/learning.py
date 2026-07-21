import re
from collections import Counter

def sentences(text):
    return [x.strip() for x in re.split(r'(?<=[.!?])\s+',text) if len(x.strip())>35]
def keywords(text,limit=8):
    words=re.findall(r'\b[a-zA-Z]{5,}\b',text.lower());stop={'which','these','there','their','about','would','should','could','through','because','between','another','chapter','section','following','important'}
    return [w for w,_ in Counter(x for x in words if x not in stop).most_common(limit)]
def make_summary(text):
    parts=sentences(text);short=' '.join(parts[:3]) or text[:600];detail=' '.join(parts[:12]) or short
    return {'short_summary':short,'detailed_summary':detail,'bullet_notes':parts[:8] or [short],'keywords':keywords(text)}
def make_flashcards(text):
    parts=sentences(text)[:10];cards=[]
    for i,s in enumerate(parts):
        terms=keywords(s,1); term=terms[0] if terms else f'concept {i+1}'
        cards.append({'question':f'What does the lesson explain about {term}?','answer':s})
    return cards or [{'question':'What is the main topic of this lesson?','answer':text[:300]}]
def make_quiz(text):
    parts=sentences(text)[:10] or [text[:250]]; keys=keywords(text,14);questions=[]
    for i,s in enumerate(parts):
        answer=(keywords(s,1) or ['the topic'])[0];wrong=[x for x in keys if x!=answer][:3]
        while len(wrong)<3: wrong.append(['analysis','process','result'][len(wrong)])
        opts=[answer]+wrong; # deterministic rotation makes answer position vary
        shift=i%4;opts=opts[shift:]+opts[:shift]
        questions.append({'question':f'Which key concept is most closely associated with this statement: “{s[:160]}…”?','options':opts,'correct_answer':opts.index(answer),'explanation':f'The statement focuses on {answer}.'})
    while len(questions)<10: questions.append(questions[len(questions)%len(questions)].copy())
    return questions[:10]
