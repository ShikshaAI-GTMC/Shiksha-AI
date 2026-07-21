from pydantic import BaseModel,EmailStr,Field
class Signup(BaseModel): name:str=Field(min_length=2,max_length=100);email:EmailStr;password:str=Field(min_length=8,max_length=128)
class Login(BaseModel): email:EmailStr;password:str
class GenerateRequest(BaseModel): pdf_id:str
class AudioRequest(GenerateRequest): voice:str='female'
class QuizSubmission(BaseModel): answers:list[int]
