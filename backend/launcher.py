import sys
sys.path.insert(0, '/tmp/jinzai-pylib')
import os
os.chdir('/Users/hitokiwa/Desktop/jinzai-competitor-db/backend')
sys.path.insert(0, '/Users/hitokiwa/Desktop/jinzai-competitor-db/backend')

from main import app
import uvicorn
uvicorn.run(app, host='0.0.0.0', port=8000, loop='asyncio', http='h11')
