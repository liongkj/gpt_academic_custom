import pickle

class VoidTerminalState():
    def __init__(self):
        self.reset_state()

    def reset_state(self):
        self.has_provided_explaination = False
 
    def lock_plugin(self, chatbot):
        chatbot._cookies['lock_plugin'] = 'crazy_functions.虚空终端->虚空终端'
        chatbot._cookies['plugin_state'] = pickle.dumps(self)

    def unlock_plugin(self, chatbot):
        self.reset_state()
        chatbot._cookies['lock_plugin'] = None
        chatbot._cookies['plugin_state'] = pickle.dumps(self)

    def set_state(self, chatbot, key, value):
        setattr(self, key, value)
        chatbot._cookies['plugin_state'] = pickle.dumps(self)

    def get_state(self):
        state = self._cookies.get('plugin_state', None)
        state = pickle.loads(state) if state is not None else VoidTerminalState()
        state.chatbot = self
        return state