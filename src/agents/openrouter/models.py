"""
Author: rahn
Datum: 22.06.2025
Version: 1.0
Beschreibung: OpenRouter Model-Definitionen
"""

from dataclasses import dataclass
from typing import Dict


@dataclass
class OpenRouterModel:
    """OpenRouter model configuration"""
    id: str
    name: str
    provider: str
    is_free: bool
    context_length: int
    description: str


class ModelRegistry:
    """Verwaltet alle verfügbaren OpenRouter-Modelle"""
    
    @staticmethod
    def get_premium_models() -> Dict[str, OpenRouterModel]:
        """Premium models for best performance (Updated 2025)"""
        return {
            "anthropic/claude-3.5-sonnet-20241022": OpenRouterModel(
                id="anthropic/claude-3.5-sonnet-20241022",
                name="Claude 3.5 Sonnet (Latest)",
                provider="Anthropic",
                is_free=False,
                context_length=200000,
                description="Latest Claude 3.5 Sonnet with improved performance"
            ),
            "anthropic/claude-3-opus": OpenRouterModel(
                id="anthropic/claude-3-opus",
                name="Claude 3 Opus",
                provider="Anthropic",
                is_free=False,
                context_length=200000,
                description="Claude's most powerful model for complex tasks"
            ),
            # ÄNDERUNG 24.06.2025: Model von OpenRouter API nicht mehr unterstützt
            # "google/gemini-2.0-flash-exp": OpenRouterModel(
            #     id="google/gemini-2.0-flash-exp",
            #     name="Gemini 2.0 Flash (Free)",
            #     provider="Google",
            #     is_free=True,
            #     context_length=1048576,
            #     description="Google's latest Gemini 2.0 Flash with 1M context"
            # ),
            "google/gemini-pro-1.5": OpenRouterModel(
                id="google/gemini-pro-1.5",
                name="Gemini 1.5 Pro",
                provider="Google",
                is_free=False,
                context_length=2097152,
                description="Google's Gemini Pro with 2M context window"
            ),
            # ÄNDERUNG 24.06.2025: Model von OpenRouter API nicht mehr unterstützt
            # "google/gemini-2.0-flash-thinking-exp": OpenRouterModel(
            #     id="google/gemini-2.0-flash-thinking-exp",
            #     name="Gemini 2.0 Flash Thinking",
            #     provider="Google",
            #     is_free=False,
            #     context_length=65536,
            #     description="Reasoning model for complex problem solving"
            # ),
            # ÄNDERUNG 24.06.2025: Model von OpenRouter API nicht mehr unterstützt
            # "google/gemini-2.0-flash-thinking-exp:free": OpenRouterModel(
            #     id="google/gemini-2.0-flash-thinking-exp:free",
            #     name="Gemini 2.0 Flash Thinking (Free)",
            #     provider="Google",
            #     is_free=True,
            #     context_length=65536,
            #     description="Free tier reasoning model for complex problem solving"
            # ),
            "x-ai/grok-2-1212": OpenRouterModel(
                id="x-ai/grok-2-1212",
                name="Grok 2 (Latest)",
                provider="xAI",
                is_free=False,
                context_length=131072,
                description="Latest Grok with real-time search capabilities"
            ),
            "openai/gpt-4o": OpenRouterModel(
                id="openai/gpt-4o",
                name="GPT-4o",
                provider="OpenAI",
                is_free=False,
                context_length=128000,
                description="OpenAI's GPT-4 Omni model"
            ),
            "openai/gpt-4o-2024-11-20": OpenRouterModel(
                id="openai/gpt-4o-2024-11-20",
                name="GPT-4o (Latest)",
                provider="OpenAI",
                is_free=False,
                context_length=128000,
                description="Latest GPT-4o with improved capabilities"
            ),
            "openai/o1": OpenRouterModel(
                id="openai/o1",
                name="OpenAI o1",
                provider="OpenAI",
                is_free=False,
                context_length=200000,
                description="Advanced reasoning model for complex tasks"
            ),
            "openai/o1-preview": OpenRouterModel(
                id="openai/o1-preview",
                name="OpenAI o1 Preview",
                provider="OpenAI",
                is_free=False,
                context_length=128000,
                description="Preview of OpenAI's reasoning model"
            ),
            "meta-llama/llama-3.1-405b-instruct": OpenRouterModel(
                id="meta-llama/llama-3.1-405b-instruct",
                name="Llama 3.1 405B",
                provider="Meta",
                is_free=False,
                context_length=128000,
                description="Meta's largest open model with 405B parameters"
            )
        }
    
    @staticmethod
    def get_free_models() -> Dict[str, OpenRouterModel]:
        """Free tier models with strong performance"""
        return {
            "deepseek/deepseek-chat": OpenRouterModel(
                id="deepseek/deepseek-chat",
                name="DeepSeek Chat",
                provider="DeepSeek",
                is_free=True,
                context_length=32768,
                description="DeepSeek's latest chat model with strong reasoning"
            ),
            "qwen/qwen-2.5-72b-instruct": OpenRouterModel(
                id="qwen/qwen-2.5-72b-instruct",
                name="Qwen 2.5 72B",
                provider="Alibaba",
                is_free=True,
                context_length=32768,
                description="Alibaba's powerful 72B parameter model"
            ),
            "mistralai/mistral-7b-instruct": OpenRouterModel(
                id="mistralai/mistral-7b-instruct",
                name="Mistral 7B Instruct",
                provider="Mistral AI",
                is_free=True,
                context_length=32768,
                description="Mistral's efficient 7B instruction model"
            ),
            "meta-llama/llama-3.2-90b-vision-instruct": OpenRouterModel(
                id="meta-llama/llama-3.2-90b-vision-instruct",
                name="Llama 3.2 90B Vision",
                provider="Meta",
                is_free=True,
                context_length=128000,
                description="Meta's latest 90B Llama model with vision capabilities"
            ),
            "google/gemma-2-27b-it": OpenRouterModel(
                id="google/gemma-2-27b-it",
                name="Gemma 2 27B",
                provider="Google",
                is_free=True,
                context_length=8192,
                description="Google's Gemma 2 instruction-tuned model"
            ),
            "nousresearch/hermes-3-llama-3.1-70b": OpenRouterModel(
                id="nousresearch/hermes-3-llama-3.1-70b",
                name="Hermes 3 Llama 70B",
                provider="Nous Research",
                is_free=True,
                context_length=128000,
                description="Fine-tuned Llama for complex tasks"
            )
        }
    
    @staticmethod
    def get_all_models() -> Dict[str, OpenRouterModel]:
        """Alle verfügbaren Modelle"""
        return {
            **ModelRegistry.get_premium_models(),
            **ModelRegistry.get_free_models()
        }
    
    @staticmethod
    def get_model(model_id: str) -> OpenRouterModel:
        """Gibt ein spezifisches Modell zurück"""
        all_models = ModelRegistry.get_all_models()
        if model_id in all_models:
            return all_models[model_id]
        else:
            # Default zu DeepSeek
            return ModelRegistry.get_free_models()["deepseek/deepseek-chat"]
