import os,shutil,uuid
from datetime import datetime,timezone
from pathlib import Path
import fitz
from bson import ObjectId
from fastapi import FastAPI,UploadFile,File,Depends,HTTPException,status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from auth import hash_password,verify_password,create_token,current_user
from database import db,setup_indexes
from models import Signup,Login,GenerateRequest,AudioRequest,QuizSubmission
from services.learning import make_summary,make_flashcards,make_quiz

ROOT=Path(__file__).parent;FRONTEND=ROOT.parent/'frontend';UPLOADS=ROOT/'uploads';AUDIO=ROOT/'generated_audio'
UPLOADS.mkdir(exist_ok=True);AUDIO.mkdir(exist_ok=True)
app=FastAPI(title='ShikshaAI API',version='1.0.0')
app.add_middleware(CORSMiddleware,allow_origins=os.getenv('CORS_ORIGINS','*').split(','),allow_credentials=False,allow_methods=['*'],allow_headers=['*'])
app.mount('/uploads',StaticFiles(directory=UPLOADS),name='uploads');app.mount('/audio',StaticFiles(directory=AUDIO),name='audio')
@app.on_event('startup')
async def startup(): await setup_indexes()
def now():return datetime.now(timezone.utc)
def oid(value):
    try:return ObjectId(value)
    except:raise HTTPException(400,'Invalid resource id')
async def owned_pdf(pdf_id,user):
    item=await db.pdfs.find_one({'_id':oid(pdf_id),'user_id':user['_id']})
    if not item:raise HTTPException(404,'PDF not found')
    return item
def dto(item):
    item['id']=str(item.pop('_id'));item['user_id']=str(item['user_id']);return item
async def activity(user,description,icon='✦'):
    await db.history.insert_one({'user_id':user['_id'],'activity':description,'icon':icon,'date':now()})
@app.get('/health')
async def health():return {'status':'ok'}
@app.post('/signup',status_code=201)
async def signup(data:Signup):
    if await db.users.find_one({'email':data.email.lower()}):raise HTTPException(409,'An account with this email already exists')
    await db.users.insert_one({'name':data.name.strip(),'email':data.email.lower(),'password':hash_password(data.password),'created_at':now()})
    return {'message':'Account created successfully'}
@app.post('/login')
async def login(data:Login):
    user=await db.users.find_one({'email':data.email.lower()})
    if not user or not verify_password(data.password,user['password']):raise HTTPException(status.HTTP_401_UNAUTHORIZED,'Incorrect email or password')
    return {'access_token':create_token(str(user['_id'])),'token_type':'bearer','user':{'id':str(user['_id']),'name':user['name'],'email':user['email']}}
@app.post('/upload',status_code=201)
async def upload(file:UploadFile=File(...),user=Depends(current_user)):
    if file.content_type!='application/pdf' or not file.filename.lower().endswith('.pdf'):raise HTTPException(415,'Only PDF files are accepted')
    content=await file.read()
    if len(content)>50*1024*1024:raise HTTPException(413,'PDF must be no larger than 50 MB')
    if not content:raise HTTPException(400,'The uploaded file is empty')
    filename=f'{uuid.uuid4().hex}.pdf';path=UPLOADS/filename;path.write_bytes(content)
    try:
        doc=fitz.open(path);text='\n'.join(page.get_text() for page in doc);doc.close()
    except Exception:
        path.unlink(missing_ok=True);raise HTTPException(422,'Unable to read this PDF')
    if len(text.strip())<30:raise HTTPException(422,'No selectable text found. OCR support for scanned PDFs is coming soon.')
    title=Path(file.filename).stem
    result=await db.pdfs.insert_one({'user_id':user['_id'],'title':title,'filename':filename,'original_filename':file.filename,'upload_date':now(),'text':text})
    pdf_id=str(result.inserted_id);await db.summaries.insert_one({'pdf_id':result.inserted_id,'summary':make_summary(text),'created_at':now()});await activity(user,f'Uploaded “{title}”','⇧')
    return {'id':pdf_id,'title':title,'message':'PDF uploaded and summary generated'}
@app.get('/pdfs')
async def pdfs(user=Depends(current_user)):
    data=[]
    async for item in db.pdfs.find({'user_id':user['_id']},{'text':0}).sort('upload_date',-1):data.append(dto(item))
    return data
@app.get('/pdf/{pdf_id}')
async def pdf(pdf_id:str,user=Depends(current_user)):
    p=await owned_pdf(pdf_id,user);summary=await db.summaries.find_one({'pdf_id':p['_id']});audio=await db.audio_lessons.find_one({'pdf_id':p['_id']})
    return {'id':str(p['_id']),'title':p['title'],'summary':summary['summary'],'audio_url':audio['audio_url'] if audio else None}
@app.post('/generate-summary')
async def generate_summary(data:GenerateRequest,user=Depends(current_user)):
    p=await owned_pdf(data.pdf_id,user);summary=make_summary(p['text']);await db.summaries.update_one({'pdf_id':p['_id']},{'$set':{'summary':summary,'updated_at':now()}},upsert=True);return summary
@app.post('/generate-flashcards')
async def generate_flashcards(data:GenerateRequest,user=Depends(current_user)):
    p=await owned_pdf(data.pdf_id,user);cards=make_flashcards(p['text']);await db.flashcards.delete_many({'pdf_id':p['_id']});await db.flashcards.insert_many([{'pdf_id':p['_id'],**c} for c in cards]);await activity(user,f'Generated flashcards for “{p["title"]}”','▣');return {'count':len(cards)}
@app.get('/pdf/{pdf_id}/flashcards')
async def flashcards(pdf_id:str,user=Depends(current_user)):
    p=await owned_pdf(pdf_id,user);return [{'id':str(x['_id']),'question':x['question'],'answer':x['answer']} async for x in db.flashcards.find({'pdf_id':p['_id']})]
@app.post('/generate-quiz')
async def generate_quiz(data:GenerateRequest,user=Depends(current_user)):
    p=await owned_pdf(data.pdf_id,user);questions=make_quiz(p['text']);await db.quizzes.update_one({'pdf_id':p['_id']},{'$set':{'questions':questions,'updated_at':now()}},upsert=True);await activity(user,f'Generated quiz for “{p["title"]}”','?');return {'count':len(questions)}
@app.get('/pdf/{pdf_id}/quiz')
async def quiz(pdf_id:str,user=Depends(current_user)):
    p=await owned_pdf(pdf_id,user);q=await db.quizzes.find_one({'pdf_id':p['_id']});return {'questions':q['questions'] if q else []}
@app.post('/pdf/{pdf_id}/submit-quiz')
async def submit_quiz(pdf_id:str,data:QuizSubmission,user=Depends(current_user)):
    p=await owned_pdf(pdf_id,user);q=await db.quizzes.find_one({'pdf_id':p['_id']})
    if not q:raise HTTPException(404,'Generate a quiz first')
    correct=sum(a==x['correct_answer'] for a,x in zip(data.answers,q['questions']));total=len(q['questions']);percent=round(correct/total*100);message='Excellent work!' if percent>=80 else 'Good progress—review the lesson and try again.' if percent>=50 else 'Keep going. A quick review will help you improve.'
    await db.quiz_attempts.insert_one({'user_id':user['_id'],'pdf_id':p['_id'],'score':percent,'correct':correct,'date':now()});await activity(user,f'Completed quiz for “{p["title"]}”','✓');return {'correct':correct,'wrong':total-correct,'percentage':percent,'message':message}
@app.post('/generate-audio')
async def generate_audio(data:AudioRequest,user=Depends(current_user)):
    p=await owned_pdf(data.pdf_id,user);summary=await db.summaries.find_one({'pdf_id':p['_id']});script=summary['summary']['detailed_summary']
    # Production extension point: call a TTS provider here. A text transcript is retained even when TTS is not configured.
    await db.audio_lessons.update_one({'pdf_id':p['_id']},{'$set':{'audio_url':None,'script':script,'voice':data.voice,'duration':0,'created_at':now()}},upsert=True);await activity(user,f'Prepared audio script for “{p["title"]}”','♫');return {'message':'Audio script prepared. Configure a TTS provider to create MP3 output.'}
@app.get('/dashboard')
async def dashboard(user=Depends(current_user)):
    pdf_count=await db.pdfs.count_documents({'user_id':user['_id']});audio_count=await db.audio_lessons.count_documents({'pdf_id':{'$in':[x['_id'] async for x in db.pdfs.find({'user_id':user['_id']},{'_id':1})]}});attempts=[x async for x in db.quiz_attempts.find({'user_id':user['_id']})];history=[x async for x in db.history.find({'user_id':user['_id']}).sort('date',-1).limit(6)]
    return {'stats':{'pdfs':pdf_count,'audio_lessons':audio_count,'quiz_scores':round(sum(x['score'] for x in attempts)/len(attempts)) if attempts else 0,'study_hours':round(pdf_count*.25,1)},'history':[{'activity':x['activity'],'icon':x.get('icon','✦'),'date':x['date']} for x in history]}
@app.get('/history')
async def history(user=Depends(current_user)):return [{'id':str(x['_id']),'activity':x['activity'],'date':x['date']} async for x in db.history.find({'user_id':user['_id']}).sort('date',-1)]
@app.delete('/history/{item_id}',status_code=204)
async def delete_history(item_id:str,user=Depends(current_user)):
    result=await db.history.delete_one({'_id':oid(item_id),'user_id':user['_id']})
    if not result.deleted_count:raise HTTPException(404,'History item not found')

# Serve the web application from the same origin as the API. This avoids browser CORS
# errors and means the project can be launched with one Uvicorn command.
app.mount('/',StaticFiles(directory=FRONTEND,html=True),name='frontend')
