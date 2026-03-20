
from fastapi.middleware.cors import CORSMiddleware
class CorsMiddleWare:
    """
    app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    )
    """
    def __init__(self,app):
        self.app=app
    def add_cors_middleware(
            self,
            allow_origins,
            allow_credentials,
            allow_methods,
            allow_headers):
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=allow_origins,
            allow_credentials=allow_credentials,
            allow_methods=allow_methods,
            allow_headers=allow_headers
        )
        return self.app