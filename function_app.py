# This is the pre-defined centralized file to define Azure Functions with Python.
# In this case, each function's logic is contained in a separate file (Blueprint)
# Those functions (one or many) are registered in this file. 

import azure.functions as func

from process_manifest import function_process_manifest
#from test_send_queue_messsage import function_send_queue_messsage
#from test_readBlobContainer import function_httptrig_readBlobContainer

#app = func.FunctionApp()
app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)
app.register_functions(function_process_manifest)
#app.register_functions(function_send_queue_messsage)
#app.register_functions(function_httptrig_readBlobContainer)


