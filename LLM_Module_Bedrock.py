import boto3
class LLM_Module():
    '''
    a class that wrap all functions for a specific LLM, anthropic.claude-3-5-sonnet-20240620-v1:0
    If you want to use a different LLM, you can just adjust code in this class.
    '''
    def __init__(self, model = "anthropic.claude-3-5-sonnet-20240620-v1:0"):
        '''
        initialize llm
        Args:
            model: backbone llm, default is amazon.nova-pro-v1:0
        '''
        self.llm = boto3.client("bedrock-runtime", region_name="us-east-1",
                                     aws_access_key_id="YOUR AWS ACCESS KEY ID",
                                    aws_secret_access_key="YOUR AWX SECRET ACCESS KEY")

        # Set the model ID, e.g., Amazon Titan Text G1 - Express.
        self.model_id = model

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
        # Send the message to the model, using a basic inference configuration.
        # Send the message to the model, using a basic inference configuration.
        
        text_response = []
        for i in range(n):
            if len(messages) == 2:
                response = self.llm.converse(
                    modelId=self.model_id,
                    messages=messages[0],
                    system=messages[1],
                    inferenceConfig = {"maxTokens": 5120}
                )
            else:
                response = self.llm.converse(
                    modelId=self.model_id,
                    messages=messages[0],
                    inferenceConfig = {"maxTokens": 5120}
                )
    
            # Extract and print the response text.
            response_text = response["output"]["message"]["content"][0]["text"]
            text_response.append(response_text)
        
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
        user_message = [
                {
                    "role": "user",
                    "content": [{"text": user_prompt}],
                }
            ]
        
        if system_prompt:
            system_message = [
                {
                    "text": system_prompt
                }
            ]
            message = [user_message, system_message]
        else:
            message = [user_message]

        return message