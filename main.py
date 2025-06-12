from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv
import os
import base64
import json

load_dotenv()

client = OpenAI(
  api_key = os.getenv('OPENAI_API_KEY')
)

app = FastAPI()

origins = [
  'http://localhost:5173',
  'https://splitwiseui.onrender.com'
]

app.add_middleware(
  CORSMiddleware,
  allow_origins = origins,
  allow_methods=['*'],
  allow_headers=['*']
)

class Prompt(BaseModel):
  text : str

tools = [{
    "type": "function",
    "name": "extract_bill_data",
    "description": "Extracts structured bill information from a restaurant receipt.",
    "parameters": {
        "type": "object",
        "properties": {
            "restaurant": { "type": "string" },
            "items": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": { "type": "string" },
                        "quantity": { "type": "number" },
                        "unit_price": { "type": "number" },
                        "total": { "type": "number" }
                    }
                }
            },
            "summary": {
                "type": "object",
                "properties": {
                    "subtotal": { "type": "number" },
                    "taxes": {
                        "type": "object",
                        "properties": {
                            "SGST": { "type": "number" },
                            "CGST": { "type": "number" }
                        }
                    },
                    "round_off": { "type": "number" },
                    "grand_total": { "type": "number" }
                }
            }
        },
        "required": ["restaurant", "items", "summary"]
    }
}]


@app.get('/')
def hello():
  return 'Hello world'

@app.post('/api/llm/')
async def llm_response(image: UploadFile = File(...)):
  try:

    print(f'File received : {image.filename}')
    image_bytes = await image.read()
    base64_image = base64.b64encode(image_bytes).decode('utf-8')

    input_messages = [{
      'role':'user', 
      'content': [
        {'type': 'input_text', 'text':'Extract restaurant bill details from the image into structured JSON format using extract_bill_data function.'},
        {'type': 'input_image', 'image_url':f'data:image/png;base64,{base64_image}'}
      ]}]
    
    response = client.responses.create(
      model='gpt-4o-mini',
      input=input_messages,
      tools=tools
    )
    json_string = response.output[0].arguments
    bill_details = json.loads(json_string)
    print(bill_details)

    return {'output': bill_details, 'status':response.status}
  except Exception as e:
    print(e)
    return {'output': f'Error occured: {e}', 'status':'failed'}
    



# @app.post('/api/llm/')
# def llm_response(prompt: Prompt):
#   try:
    
#     response = client.responses.create(
#       model='gpt-4o-mini',
#       input=prompt.text,
#     )
#     return {'output': response.output, 'status':'ok'}
#   except Exception as e:
#     return {'output': f'Error occured: {e}', 'status':'failed'}
    



