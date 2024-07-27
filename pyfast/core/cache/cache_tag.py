# -*- coding: utf-8 -*-
from enum import Enum


class CacheTag(Enum):
    GET_HEALTH_CHECK = "get_health_check"
    GET_USER_INFO = "get_user_info"
    GET_CATEGORIES = "get_categories"
    GET_HISTORY = "get_chat_history"
    GET_QUESTION = "get_question"
