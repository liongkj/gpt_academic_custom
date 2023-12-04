from collections.abc import Callable, Iterable, Mapping
from typing import Any
from toolbox import CatchException, update_ui, gen_time_str, trimmed_format_exc
from toolbox import promote_file_to_downloadzone, get_log_folder
from .crazy_utils import request_gpt_model_in_new_thread_with_ui_alive
from .crazy_utils import input_clipping, try_install_deps
from multiprocessing import Process, Pipe
import os
import time

templete = """
```python
import ...  # Put dependencies here, e.g. import numpy as np

class TerminalFunction(object): # Do not change the name of the class, The name of the class must be `TerminalFunction`

    def run(self, path):    # The name of the function must be `run`, it takes only a positional argument.
        # rewrite the function you have just written here 
        ...
        return generated_file_path
```
"""

def inspect_dependency(chatbot, history):
    yield from update_ui(chatbot=chatbot, history=history) # 刷新界面
    return True

def get_code_block(reply):
    import re
    pattern = r"```([\s\S]*?)```" # regex pattern to match code blocks
    matches = re.findall(pattern, reply) # find all code blocks in text
    if len(matches) == 1: 
        return matches[0].strip('python') #  code block
    for match in matches:
        if 'class TerminalFunction' in match:
            return match.strip('python') #  code block
    raise RuntimeError("GPT is not generating proper code.")

def gpt_interact_multi_step(txt, file_type, llm_kwargs, chatbot, history):
    # 输入
    prompt_compose = [
        f'Your job:\n1. write a single Python function, which takes a path of a `{file_type}` file as the only argument and returns a `string` containing the result of analysis or the path of generated files. \n',
        f"2. You should write this function to perform following task: {txt}"
        + "\n",
        "3. Wrap the output python function with markdown codeblock.",
    ]
    i_say = "".join(prompt_compose)
    demo = []

    # 第一步
    gpt_say = yield from request_gpt_model_in_new_thread_with_ui_alive(
        inputs=i_say, inputs_show_user=i_say, 
        llm_kwargs=llm_kwargs, chatbot=chatbot, history=demo, 
        sys_prompt= r"You are a programmer."
    )
    history.extend([i_say, gpt_say])
    yield from update_ui(chatbot=chatbot, history=history) # 刷新界面 # 界面更新

    # 第二步
    prompt_compose = [
        "If previous stage is successful, rewrite the function you have just written to satisfy following templete: \n",
        templete
    ]
    i_say = "".join(prompt_compose)
    inputs_show_user = "If previous stage is successful, rewrite the function you have just written to satisfy executable templete. "
    gpt_say = yield from request_gpt_model_in_new_thread_with_ui_alive(
        inputs=i_say, inputs_show_user=inputs_show_user, 
        llm_kwargs=llm_kwargs, chatbot=chatbot, history=history, 
        sys_prompt= r"You are a programmer."
    )
    code_to_return = gpt_say
    history.extend([i_say, code_to_return])
    yield from update_ui(chatbot=chatbot, history=history) # 刷新界面 # 界面更新

    # # 第三步
    # i_say = "Please list to packages to install to run the code above. Then show me how to use `try_install_deps` function to install them."
    # i_say += 'For instance. `try_install_deps(["opencv-python", "scipy", "numpy"])`'
    # installation_advance = yield from request_gpt_model_in_new_thread_with_ui_alive(
    #     inputs=i_say, inputs_show_user=inputs_show_user, 
    #     llm_kwargs=llm_kwargs, chatbot=chatbot, history=history, 
    #     sys_prompt= r"You are a programmer."
    # )
    # # # 第三步  
    # i_say = "Show me how to use `pip` to install packages to run the code above. "
    # i_say += 'For instance. `pip install -r opencv-python scipy numpy`'
    # installation_advance = yield from request_gpt_model_in_new_thread_with_ui_alive(
    #     inputs=i_say, inputs_show_user=i_say, 
    #     llm_kwargs=llm_kwargs, chatbot=chatbot, history=history, 
    #     sys_prompt= r"You are a programmer."
    # )
    installation_advance = ""

    return code_to_return, installation_advance, txt, file_type, llm_kwargs, chatbot, history

def make_module(code):
    module_file = 'gpt_fn_' + gen_time_str().replace('-','_')
    with open(f'{get_log_folder()}/{module_file}.py', 'w', encoding='utf8') as f:
        f.write(code)

    def get_class_name(class_string):
        import re
        # Use regex to extract the class name
        class_name = re.search(r'class (\w+)\(', class_string).group(1)
        return class_name

    class_name = get_class_name(code)
    return f"{get_log_folder().replace('/', '.')}.{module_file}->{class_name}"

def init_module_instance(module):
    import importlib
    module_, class_ = module.split('->')
    init_f = getattr(importlib.import_module(module_), class_)
    return init_f()

def for_immediate_show_off_when_possible(file_type, fp, chatbot):
    if file_type in ['png', 'jpg']:
        image_path = os.path.abspath(fp)
        chatbot.append(['这是一张图片, 展示如下:',  
            f'本地文件地址: <br/>`{image_path}`<br/>'+
            f'本地文件预览: <br/><div align="center"><img src="file={image_path}"></div>'
        ])
    return chatbot

def subprocess_worker(instance, file_path, return_dict):
    return_dict['result'] = instance.run(file_path)

def have_any_recent_upload_files(chatbot):
    if not chatbot: return False    # chatbot is None
    if most_recent_uploaded := chatbot._cookies.get(
        "most_recent_uploaded", None
    ):
        return time.time() - most_recent_uploaded["time"] < 5 * 60
    else:
        return False   # most_recent_uploaded is None

def get_recent_file_prompt_support(chatbot):
    most_recent_uploaded = chatbot._cookies.get("most_recent_uploaded", None)
    return most_recent_uploaded['path']

@CatchException
def 虚空终端CodeInterpreter(txt, llm_kwargs, plugin_kwargs, chatbot, history, system_prompt, web_port):
    """
    txt             输入栏用户输入的文本，例如需要翻译的一段话，再例如一个包含了待处理文件的路径
    llm_kwargs      gpt模型参数，如温度和top_p等，一般原样传递下去就行
    plugin_kwargs   插件模型的参数，暂时没有用武之地
    chatbot         聊天显示框的句柄，用于显示给用户
    history         聊天历史，前情提要
    system_prompt   给gpt的静默提醒
    web_port        当前软件运行的端口号
    """
    raise NotImplementedError   

"""
测试：
    裁剪图像，保留下半部分
    交换图像的蓝色通道和红色通道
    将图像转为灰度图像
    将csv文件转excel表格
"""