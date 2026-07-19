import torch
import torch.nn as nn
import torch.nn.functional as F


class TemporalAttention(nn.Module):
    def __init__(self, hidden_dim: int):
        super().__init__()
        self.attn = nn.Linear(hidden_dim, 1)

    def forward(self, hidden_states: torch.Tensor):
        # hidden_states: (B, T, H)
        scores  = self.attn(hidden_states).squeeze(-1)       # (B, T)
        weights = F.softmax(scores, dim=-1)                  # (B, T)
        context = (weights.unsqueeze(-1) * hidden_states).sum(dim=1)  # (B, H)
        return context, weights


class HSFEncoder(nn.Module):
    """
    Hormone State Foundation Encoder.
    Maps an irregular multivariate time series (B, T, input_dim) → (B, embed_dim).
    """

    def __init__(self, input_dim: int = 9, hidden_dim: int = 256, embed_dim: int = 128, num_layers: int = 2):
        super().__init__()
        self.input_proj = nn.Linear(input_dim, hidden_dim)
        self.gru = nn.GRU(
            input_size=hidden_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            dropout=0.2 if num_layers > 1 else 0.0,
        )
        self.attention  = TemporalAttention(hidden_dim)
        self.output_proj = nn.Sequential(
            nn.Linear(hidden_dim, embed_dim),
            nn.LayerNorm(embed_dim),
        )

    def forward(self, x: torch.Tensor):
        # x: (B, T, input_dim)
        x = F.relu(self.input_proj(x))          # (B, T, H)
        hidden_states, _ = self.gru(x)           # (B, T, H)
        context, weights = self.attention(hidden_states)  # (B, H), (B, T)
        embedding = self.output_proj(context)    # (B, embed_dim)
        embedding = F.normalize(embedding, dim=-1)
        return embedding, weights
