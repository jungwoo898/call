try:
    from .model import ModelRegistry, LLaMAModel, OpenAIModel, AzureOpenAIModel
    
    ModelRegistry.text_register("llama", LLaMAModel)
    ModelRegistry.text_register("openai", OpenAIModel)
    ModelRegistry.text_register("azure_openai", AzureOpenAIModel)
except ImportError:
    # torch가 없는 환경에서는 모델 레지스트리를 건너뜀
    pass