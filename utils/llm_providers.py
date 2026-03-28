import os
from dotenv import load_dotenv
from openai import AzureOpenAI

load_dotenv()


class AzureOpenAIProvider:
    def __init__(self):
        try:
            self.client = AzureOpenAI(
                api_key=os.getenv("AZURE_OPENAI_API_KEY"),
                api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
                azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
            )

            self.deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-35-turbo")
            self.name = "Azure OpenAI"

        except Exception as e:
            print("Azure OpenAI initialization failed:", str(e))
            self.client = None

    def is_available(self):
        return self.client is not None

    def generate(self, prompt, system_message=None, temperature=0.7, max_tokens=1000):
        if not self.client:
            return "Azure client not initialized"

        try:
            messages = []

            if system_message:
                messages.append({
                    "role": "system",
                    "content": system_message
                })

            messages.append({
                "role": "user",
                "content": prompt
            })

            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )

            return response.choices[0].message.content

        except Exception as e:
            return f"Azure Error: {str(e)}" 