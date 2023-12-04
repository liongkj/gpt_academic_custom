from pydantic import BaseModel, Field
from typing import List
from toolbox import update_ui_lastest_msg, disable_auto_promotion
from request_llms.bridge_all import predict_no_ui_long_connection
from crazy_functions.json_fns.pydantic_io import GptJsonIO, JsonStringError
import time
import pickle

def have_any_recent_upload_files(chatbot):
    if not chatbot: return False    # chatbot is None
    if most_recent_uploaded := chatbot._cookies.get(
        "most_recent_uploaded", None
    ):
        return time.time() - most_recent_uploaded["time"] < 5 * 60
    else:
        return False   # most_recent_uploaded is None

class GptAcademicState():
    def __init__(self):
        self.reset()

    def reset(self):
        pass

    def dump_state(self, chatbot):
        chatbot._cookies['plugin_state'] = pickle.dumps(self)

    def set_state(self, chatbot, key, value):
        setattr(self, key, value)
        chatbot._cookies['plugin_state'] = pickle.dumps(self)

    def get_state(self, cls=None):
        state = self._cookies.get('plugin_state', None)
        if state is not None:   state = pickle.loads(state)
        elif cls is not None:   state = cls()
        else:                   state = GptAcademicState()
        state.chatbot = self
        return state

class GatherMaterials():
    def __init__(self, materials) -> None:
        materials = ['image', 'prompt']