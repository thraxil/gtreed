"Template support for Json"

from turbojson import jsonify

class JsonSupport(object):
    
    def __init__(self, extra_vars_func=None, options=None):
        pass
        
    def render(self, info, format=None, fragment=False, template=None):
        """Renders data in the desired format.
    
        @param info: the data itself
        @type info: dict
        @param format: not used
        @type format: string
        @param fragment: not used
        @type fragment: bool
        @param template: not used
        @type template: string
        """
        [info.pop(item) for item in info.copy() if (item.startswith("tg_") and item != "tg_flash")]

        return jsonify.encode_iter(info)

    def get_content_type(self, user_agent):
        if "Opera" in user_agent.browser: 
            return "text/plain"
        else:
            return "text/javascript"


