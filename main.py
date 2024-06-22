# -*- coding: utf-8 -*-
import uvicorn
import os

if __name__ == '__main__':
	os.system('pre-commit install')
	uvicorn.run('src.application:app', host='0.0.0.0', port=5005, reload=True)
