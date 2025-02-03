import os
import openai
openai.api_key = "YOUR OPENAI API KEY"
os.environ["OPENAI_API_KEY"] = "YOUR OPENAI API KEY"

class LLM_Module():
    '''
    a class that wrap all functions for a specific LLM, GPT-4o
    If you want to use a different LLM, you can just adjust code in this class.
    '''
    def __init__(self, model = "gpt-4o"):
        '''
        initialize llm
        Args:
            model: backbone llm, default is gpt-4o
        '''
        self.llm = openai.OpenAI()

    def chat(self, messages, model, n=1):
        '''
        function to call llm api and get response from llm
        Args:
            messages: List[Dict{}], input message to the llm
            model: str, specify which llm to use
            n: int, number of responses we want from the llm
        Return:
            text_response: List[str], a list contains n response from the llm
        '''
        response = self.llm.chat.completions.create(
                            model=model,
                            messages=messages,
                            n=n
                            )
        text_response = [response.choices[i].message.content for i in range(n)]
        
        return text_response

    def make_message(self, user_prompt, system_prompt=None):
        '''
        Function that make the input for the llm
        Args:
            user_prompt: str, user prompt for the llm
            system_prompt: str, optional, system prompt for the llm
        Return:
            message: input for the llm
        '''
        if system_prompt:
            message = [{"role":"system", "content":system_prompt}] + \
                    [{"role":"user", "content":user_prompt}]
        else:
            message = [{"role":"user", "content":user_prompt}]

        return message
