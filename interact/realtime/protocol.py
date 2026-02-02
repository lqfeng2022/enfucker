# interact/usecases/protocol.py
class ClientEvent:
    TEXT_PARTIAL = 'text.partial'
    TEXT_FINAL = 'text.final'
    CALL_END = 'call.end'


class ServerEvent:
    AGENT_STATE = 'agent.state'     # idle | thinking | speaking
    AGENT_TEXT = 'agent.text'       # text to be spoken by TTS
    ERROR = 'error'
