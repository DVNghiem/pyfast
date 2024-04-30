# -*- coding: utf-8 -*-
import uvicorn

if __name__ == '__main__':
	uvicorn.run('src.application:app', host='0.0.0.0', port=5005, reload=True)
