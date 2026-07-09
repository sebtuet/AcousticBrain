from dataclasses import dataclass

@dataclass
class BrainConfig:
    llm_model: str = "qwen3:8b"
    language: str = "fr"
    debug: bool = False
    