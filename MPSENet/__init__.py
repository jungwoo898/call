"""Stub implementation of MPSENet for local builds.
Provides the same interface (from_pretrained, forward) but performs no enhancement.
Replace with the real implementation when available.
"""
from __future__ import annotations

import torch

__all__ = ["MPSENet", "__version__"]
__version__ = "0.0.1"


class MPSENet(torch.nn.Module):
    """Minimal placeholder for the real MPSENet speech-enhancement network."""

    def __init__(self):
        super().__init__()
        # no actual parameters – passthrough network

    @classmethod
    def from_pretrained(cls, model_name: str | None = None) -> "MPSENet":
        """Return a dummy model instance.

        Parameters
        ----------
        model_name : str, optional
            Name or path requested by the caller. Ignored in the stub.
        """
        print(f"[MPSENet-stub] Loaded placeholder model for '{model_name or 'default'}'.")
        return cls()

    def forward(self, wav_tensor: torch.Tensor, *args, **kwargs):  # type: ignore[override]
        """Pass input through unchanged (identity function)."""
        return wav_tensor 