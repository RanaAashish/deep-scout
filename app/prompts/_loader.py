import yaml
from pathlib import Path
from typing import Any, Dict, Optional

class PromptLoader:
    def __init__(self, base_dir: Optional[Path] = None):
        if base_dir is None:
            # Assume we are in app/prompts/_loader.py
            base_dir = Path(__file__).parent
        self.base_dir = base_dir
        self.registry_path = self.base_dir / "_registry.yaml"
        self._registry: Dict[str, Any] = {}
        self._cache: Dict[str, Any] = {}
        self.load_registry()

    def load_registry(self):
        if not self.registry_path.exists():
            return
        with open(self.registry_path, "r") as f:
            self._registry = yaml.safe_load(f) or {}

    def get_prompt(self, agent: str, key: str = "system", sub_key: Optional[str] = None) -> Any:
        version = self._registry.get("agents", {}).get(agent, "v1")
        cache_key = f"{agent}/{version}"
        
        if cache_key not in self._cache:
            prompt_path = self.base_dir / "agents" / agent / f"{version}.yaml"
            if not prompt_path.exists():
                raise FileNotFoundError(f"Prompt not found: {prompt_path}")
            with open(prompt_path, "r") as f:
                self._cache[cache_key] = yaml.safe_load(f) or {}
        
        data = self._cache[cache_key]
        val = data.get(key)
        
        if val and isinstance(val, dict) and sub_key:
            path = sub_key.split(".")
            for p in path:
                if isinstance(val, dict):
                    val = val.get(p)
                else:
                    return None
        return val

# Global instance for easy access
loader = PromptLoader()

def get_prompt(agent: str, key: str = "system", sub_key: Optional[str] = None) -> Any:
    return loader.get_prompt(agent, key, sub_key)
