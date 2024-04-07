# ################## SAMPLE CODE ##################

# from src.core.database.postgresql import PostgresRepository, Transactional
# from sqlalchemy.inspection import inspect
# from src.models import AnswersModel as Answer


# from typing import Any


# class AnswerRepository(PostgresRepository[Answer]):
#     @Transactional()
#     async def insert_answer(self, data: dict[str, Any]):
#         # Get the names of the columns in the Answer model
#         data = {
#             k: v
#             for k, v in data.items()
#             if k in self.model_class.__table__.columns.keys()
#         }
#         # Create the new record
#         _answer = await self.create(data)
#         return _answer

#     @Transactional()
#     async def update_answer(self, data: dict[str, Any], updated_data: dict[str, Any]):
#         _updated_answer = await self.update(data, updated_data)
#         return _updated_answer

#     @Transactional()
#     async def delete_answer(self, answer_id: str):
#         _answer = await self.get_by("id", answer_id)
#         await self.delete(_answer[0])
#         return {"message": "Answer deleted successfully"}
